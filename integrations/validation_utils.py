"""
Validation Utilities
Orchestrates quality check + AI detection for content validation
Results saved to Airtable "Suggested Edits" field
"""
import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from anthropic import Anthropic
from utils.anthropic_client import get_anthropic_client

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))


async def run_quality_check(content: str, platform: str) -> Dict[str, Any]:
    """
    Run quality check with AI pattern detection

    Uses the same quality_check logic that runs in SDK agents
    Returns structured scores + AI pattern issues
    """
    # Import platform-specific quality check prompt
    if platform == 'linkedin':
        from prompts.linkedin_tools import QUALITY_CHECK_PROMPT
    elif platform == 'twitter':
        from prompts.twitter_tools import QUALITY_CHECK_PROMPT
    elif platform == 'email':
        from prompts.email_tools import QUALITY_CHECK_PROMPT
    elif platform == 'youtube':
        from prompts.youtube_tools import QUALITY_CHECK_PROMPT
    elif platform == 'instagram':
        from prompts.instagram_tools import QUALITY_CHECK_PROMPT
    else:
        # Fallback to LinkedIn for unknown platforms
        from prompts.linkedin_tools import QUALITY_CHECK_PROMPT
        logger.warning(f"⚠️ Unknown platform '{platform}', using LinkedIn quality check prompt")

    # Validate API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Please set it to run quality checks."
        )

    client = get_anthropic_client()

    # Format prompt for the specific platform
    prompt = QUALITY_CHECK_PROMPT.format(post=content)

    try:
        # Call Claude with web_search tool for fact checking
        messages = [{"role": "user", "content": prompt}]

        max_iterations = 5
        for iteration in range(max_iterations):
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=3000,
                    tools=[{
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": 3
                    }],
                    messages=messages
                )
            except Exception as api_error:
                error_str = str(api_error).lower()
                logger.error(f"❌ Anthropic API error during quality check: {api_error}")

                # Check if web search tool failed specifically
                if any(keyword in error_str for keyword in ['web_search', '500', 'internal server error', 'api_error']):
                    logger.warning("⚠️ Web search tool unavailable - returning partial results without fact-checking")
                    return {
                        "scores": {"total": 18},  # Assume decent quality
                        "decision": "manual_review",
                        "issues": [{
                            "axis": "validation",
                            "severity": "high",
                            "original": "Fact-checking unavailable",
                            "fix": "Manual review required - web search API failed",
                            "impact": "Could not verify claims or check for fabrications"
                        }],
                        "surgical_summary": "Quality check ran but fact-checking unavailable due to API error."
                    }
                else:
                    # Other API errors - re-raise
                    raise

            # Check if Claude wants to use a tool
            if response.stop_reason == "tool_use":
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                continue

            # Got final response
            final_text = ""
            for block in response.content:
                if hasattr(block, 'text'):
                    final_text += block.text

            # Try to parse JSON (handle markdown code fences)
            try:
                # Strip markdown code fences if present
                import re
                cleaned_text = final_text.strip()

                # Remove ```json\n...\n``` wrapper
                json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned_text, re.DOTALL)
                if json_match:
                    cleaned_text = json_match.group(1)

                json_result = json.loads(cleaned_text)
                if "scores" in json_result and "decision" in json_result:
                    return json_result
            except (json.JSONDecodeError, AttributeError):
                pass

            # Fallback: return raw text
            return {
                "scores": {"total": 0},
                "decision": "error",
                "issues": [],
                "surgical_summary": final_text
            }

        # Max iterations reached
        return {
            "scores": {"total": 0},
            "decision": "error",
            "issues": [],
            "surgical_summary": "Max iterations reached"
        }

    except Exception as e:
        return {
            "scores": {"total": 0},
            "decision": "error",
            "issues": [],
            "surgical_summary": f"Quality check error: {str(e)}"
        }


async def run_gptzero_check(content: str) -> Optional[Dict[str, Any]]:
    """
    Run GPTZero AI detection if API key is available
    Returns None if API key not set
    """
    api_key = os.getenv('GPTZERO_API_KEY')

    if not api_key:
        return None

    if len(content) < 50:
        return {
            "status": "SKIPPED",
            "reason": "Content too short (minimum 50 characters)"
        }

    try:
        # GPTZero can be slow for long content - use 40s timeout (wrapped in 45s asyncio.wait_for)
        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(
                'https://api.gptzero.me/v2/predict/text',
                headers={
                    'x-api-key': api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'document': content,
                    'multilingual': False
                }
            )

            response.raise_for_status()
            data = response.json()

            # Extract probabilities
            documents = data.get('documents', [])
            if not documents:
                return {
                    "status": "ERROR",
                    "reason": "No documents in GPTZero response"
                }

            doc = documents[0]

            # Extract probabilities from class_probabilities (CORRECT way)
            class_probs = doc.get('class_probabilities', {})
            human_prob = class_probs.get('human', 0) * 100
            ai_prob = class_probs.get('ai', 0) * 100
            mixed_prob = class_probs.get('mixed', 0) * 100

            # Get flagged sentences
            sentences = doc.get('sentences', [])
            flagged = [
                s.get('sentence', '')
                for s in sentences
                if s.get('generated_prob', 0) > 0.7
            ]

            # PASS if human probability > 70% (i.e., AI < 30%)
            passes = human_prob > 70

            return {
                "status": "PASS" if passes else "FLAGGED",
                "human_probability": round(human_prob, 1),
                "ai_probability": round(ai_prob, 1),
                "mixed_probability": round(mixed_prob, 1),
                "flagged_sentences_count": len(flagged),
                "flagged_sentences": [s[:100] + "..." for s in flagged[:3]]
            }

    except httpx.HTTPError as e:
        return {
            "status": "ERROR",
            "reason": f"GPTZero API error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "reason": f"GPTZero check error: {str(e)}"
        }


async def run_all_validators(content: str, platform: str) -> str:
    """
    Run all validators and return formatted JSON for Airtable "Suggested Edits"

    Args:
        content: Clean post content
        platform: linkedin, twitter, email, youtube

    Returns:
        JSON string with validation results
    """
    logger.info("=" * 60)
    logger.info("🔍 RUNNING VALIDATORS")
    logger.info("=" * 60)

    # Run validators sequentially to avoid timeout issues (GPTZero can be slow)
    logger.info("📊 Running quality check first...")
    try:
        quality_result = await asyncio.wait_for(run_quality_check(content, platform), timeout=60.0)
        logger.info(f"📊 Quality check raw result keys: {quality_result.keys() if isinstance(quality_result, dict) else 'not a dict'}")
        logger.info(f"📊 Quality check scores: {quality_result.get('scores', 'missing')}")
    except asyncio.TimeoutError:
        logger.warning("⚠️ Quality check timed out after 60s - using fallback")
        quality_result = {
            "scores": {"total": 18},
            "decision": "timeout",
            "issues": [],
            "surgical_summary": "Quality check timed out"
        }

    logger.info("📊 Running GPTZero check...")
    try:
        gptzero_result = await asyncio.wait_for(run_gptzero_check(content), timeout=45.0)
    except asyncio.TimeoutError:
        logger.warning("⚠️ GPTZero check timed out after 45s - skipping")
        gptzero_result = {
            "status": "TIMEOUT",
            "reason": "GPTZero API timed out after 45 seconds"
        }

    logger.info(f"✅ Quality check complete: {quality_result.get('scores', {}).get('total', 0)}/25")
    if gptzero_result:
        logger.info(f"✅ GPTZero check complete: {gptzero_result.get('status')}")
    else:
        logger.warning("⚠️ GPTZero API key not set - skipping")

    # Format for Airtable
    validation_data = {
        "quality_scores": quality_result.get('scores', {}),
        "decision": quality_result.get('decision'),
        "ai_patterns_found": quality_result.get('issues', []),
        "surgical_summary": quality_result.get('surgical_summary', ''),
        "searches_performed": quality_result.get('searches_performed', []),  # For fact-checking transparency
        "gptzero": gptzero_result if gptzero_result else {"status": "NOT_RUN", "reason": "API key not configured"},
        "platform": platform,
        "timestamp": datetime.now().isoformat()
    }

    # Convert to JSON string for Airtable
    json_str = json.dumps(validation_data, indent=2, ensure_ascii=False)

    logger.info(f"📋 Returning validation JSON ({len(json_str)} chars)")
    logger.info("📋 Validation summary:")
    logger.info(f"   Quality Score: {quality_result.get('scores', {}).get('total', 0)}/25")
    logger.info(f"   AI Patterns Found: {len(quality_result.get('issues', []))}")
    if gptzero_result and gptzero_result.get('status') not in ['NOT_RUN', 'ERROR', 'SKIPPED']:
        logger.info(f"   GPTZero: {gptzero_result.get('human_probability', 0)}% human")
    logger.info("=" * 60)

    return json_str


def format_validation_for_airtable(validation_json_str: str) -> str:
    """
    Convert validation JSON into human-readable rich text for Airtable

    Args:
        validation_json_str: JSON string from run_all_validators()

    Returns:
        Formatted rich text string for Airtable "Suggested Edits" field
    """
    if not validation_json_str:
        return "✅ No validation data available"

    try:
        data = json.loads(validation_json_str)
    except json.JSONDecodeError:
        return "⚠️ Invalid validation data"

    # Build formatted output
    lines = []
    lines.append("🔍 CONTENT VALIDATION REPORT")
    lines.append("=" * 50)
    lines.append("")

    # Quality Scores
    quality_scores = data.get('quality_scores', {})
    total_score = quality_scores.get('total', 0)
    decision = data.get('decision', 'unknown')

    # Decision emoji
    decision_emoji = {
        'accept': '✅',
        'revise': '⚠️',
        'reject': '❌',
        'error': '🔴'
    }.get(decision, '❓')

    lines.append(f"{decision_emoji} OVERALL: {decision.upper()} (Score: {total_score}/25)")
    lines.append("")

    # Individual scores
    if quality_scores:
        lines.append("📊 Quality Breakdown:")
        for key, value in quality_scores.items():
            if key != 'total':
                lines.append(f"   • {key.replace('_', ' ').title()}: {value}/5")
        lines.append("")

    # AI Patterns Found - Enhanced formatting with severity grouping
    ai_patterns = data.get('ai_patterns_found', [])

    # Initialize severity lists (needed for later sections)
    critical_issues = []
    high_issues = []
    medium_issues = []
    low_issues = []

    if ai_patterns:
        # Check if ai_patterns contains dicts (new format) or strings (old format)
        if ai_patterns and isinstance(ai_patterns[0], dict):
            # NEW FORMAT: Array of issue objects with severity
            lines.append("⚠️ ISSUES FOUND:")
            lines.append("")

            # Group by severity
            critical_issues = [p for p in ai_patterns if p.get('severity') == 'critical']
            high_issues = [p for p in ai_patterns if p.get('severity') == 'high']
            medium_issues = [p for p in ai_patterns if p.get('severity') == 'medium']
            low_issues = [p for p in ai_patterns if p.get('severity') == 'low']

            # Display critical issues first
            if critical_issues:
                lines.append("🚨 CRITICAL:")
                for issue in critical_issues:
                    axis = issue.get('axis', 'general').upper()
                    original = issue.get('original', 'N/A')
                    fix = issue.get('fix', 'N/A')
                    impact = issue.get('impact', '')

                    lines.append(f"   [{axis}]")
                    lines.append(f"   Problem: {original}")
                    lines.append(f"   Fix: {fix}")
                    if impact:
                        lines.append(f"   Impact: {impact}")
                    lines.append("")

            # High priority issues
            if high_issues:
                lines.append("⚠️ HIGH PRIORITY:")
                for issue in high_issues:
                    axis = issue.get('axis', 'general').upper()
                    original = issue.get('original', 'N/A')
                    fix = issue.get('fix', 'N/A')
                    impact = issue.get('impact', '')

                    lines.append(f"   [{axis}]")
                    lines.append(f"   Problem: {original}")
                    lines.append(f"   Fix: {fix}")
                    if impact:
                        lines.append(f"   Impact: {impact}")
                    lines.append("")

            # Medium priority issues
            if medium_issues:
                lines.append("📝 MEDIUM PRIORITY:")
                for issue in medium_issues:
                    axis = issue.get('axis', 'general').upper()
                    original = issue.get('original', 'N/A')
                    fix = issue.get('fix', 'N/A')
                    impact = issue.get('impact', '')

                    lines.append(f"   [{axis}]")
                    lines.append(f"   Problem: {original}")
                    lines.append(f"   Fix: {fix}")
                    if impact:
                        lines.append(f"   Impact: {impact}")
                    lines.append("")

            # Low priority issues
            if low_issues:
                lines.append("💡 SUGGESTIONS:")
                for issue in low_issues:
                    axis = issue.get('axis', 'general').upper()
                    original = issue.get('original', 'N/A')
                    fix = issue.get('fix', 'N/A')

                    lines.append(f"   [{axis}] {original} → {fix}")
                    lines.append("")

        else:
            # OLD FORMAT: Array of strings (backwards compatibility)
            lines.append("⚡ AI Patterns Detected:")
            for pattern in ai_patterns:
                lines.append(f"   • {pattern}")
            lines.append("")

    # Add numbered action items section if we have issues
    if ai_patterns and isinstance(ai_patterns[0], dict):
        lines.append("🔧 SPECIFIC EDITS TO MAKE:")
        lines.append("")

        # Combine all issues in priority order for action list
        all_issues = critical_issues + high_issues + medium_issues + low_issues

        for i, issue in enumerate(all_issues, 1):
            severity = issue.get('severity', 'medium').upper()
            axis = issue.get('axis', 'general')
            original = issue.get('original', 'N/A')
            fix = issue.get('fix', 'N/A')
            impact = issue.get('impact', '')

            lines.append(f"{i}. [{severity}] {axis.title()}")
            lines.append(f"   Original: \"{original}\"")
            lines.append(f"   Fix: \"{fix}\"")
            if impact:
                lines.append(f"   Impact: {impact}")
            lines.append("")

    # Show search queries performed (transparency for fact-checking)
    searches = data.get('searches_performed', [])

    if searches:
        lines.append("🔍 Fact-Checking Performed:")
        for search_query in searches:
            lines.append(f"   • Searched: \"{search_query}\"")
        lines.append("")

    # Surgical Summary
    surgical_summary = data.get('surgical_summary', '')
    if surgical_summary:
        lines.append("💡 Recommended Fixes:")

        # Check if surgical_summary is JSON (fallback case)
        if surgical_summary.strip().startswith('{') or '```json' in surgical_summary:
            lines.append("   ⚠️ Quality check returned JSON instead of summary:")
            lines.append("   (This means the quality check tool didn't parse correctly)")
            # Try to extract the actual summary from the JSON
            try:
                import re
                # Strip code fences
                cleaned = re.sub(r'```(?:json)?\s*\n?', '', surgical_summary)
                cleaned = re.sub(r'\n?```', '', cleaned)
                parsed = json.loads(cleaned)
                actual_summary = parsed.get('surgical_summary', '')
                if actual_summary:
                    lines.append(f"   Extracted: {actual_summary}")
            except:
                lines.append("   [Could not parse - check quality check logs]")
        else:
            # Normal text summary
            lines.append(f"   {surgical_summary}")

        lines.append("")

    # Burstiness Analysis (if quality check provided it)
    burstiness = data.get('burstiness_analysis', {})
    if burstiness:
        lines.append("📏 Sentence Variation (Burstiness):")
        lines.append(f"   • Short (≤10w): {burstiness.get('short_pct', 0)}%")
        lines.append(f"   • Medium (10-20w): {burstiness.get('medium_pct', 0)}%")
        lines.append(f"   • Long (≥20w): {burstiness.get('long_pct', 0)}%")
        lines.append(f"   • Fragments (≤5w): {burstiness.get('fragment_pct', 0)}%")

        if burstiness.get('is_uniform', False):
            lines.append("   ⚠️ WARNING: Low burstiness detected (AI tell)")
        lines.append("")

    # GPTZero Results
    gptzero = data.get('gptzero', {})
    gptzero_status = gptzero.get('status', 'NOT_RUN')

    if gptzero_status == 'NOT_RUN':
        lines.append("🤖 GPTZero: Not configured (set GPTZERO_API_KEY to enable)")
    elif gptzero_status == 'ERROR':
        lines.append(f"🤖 GPTZero: Error - {gptzero.get('reason', 'Unknown')}")
    elif gptzero_status == 'SKIPPED':
        lines.append(f"🤖 GPTZero: Skipped - {gptzero.get('reason', 'Unknown')}")
    elif gptzero_status in ['PASS', 'FLAGGED']:
        human_prob = gptzero.get('human_probability', 0)
        ai_prob = gptzero.get('ai_probability', 0)
        flagged_count = gptzero.get('flagged_sentences_count', 0)

        status_emoji = '✅' if gptzero_status == 'PASS' else '⚠️'
        lines.append(f"{status_emoji} GPTZero AI Detection:")
        lines.append(f"   • Human-written: {human_prob}%")
        lines.append(f"   • AI-generated: {ai_prob}%")

        if flagged_count > 0:
            lines.append(f"   • Flagged sentences: {flagged_count}")
            flagged_sentences = gptzero.get('flagged_sentences', [])
            if flagged_sentences:
                lines.append("   • Examples:")
                for sentence in flagged_sentences[:2]:  # Show max 2
                    lines.append(f"     - {sentence}")

    lines.append("")
    lines.append("=" * 50)

    # Timestamp
    timestamp = data.get('timestamp', '')
    if timestamp:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"📅 Generated: {formatted_time}")
        except:
            lines.append(f"📅 Generated: {timestamp}")

    return "\n".join(lines)

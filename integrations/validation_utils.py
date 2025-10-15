"""
Validation Utilities
Orchestrates quality check + AI detection for content validation
Results saved to Airtable "Suggested Edits" field
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from anthropic import Anthropic


async def run_quality_check(content: str, platform: str) -> Dict[str, Any]:
    """
    Run quality check with AI pattern detection

    Uses the same quality_check logic that runs in SDK agents
    Returns structured scores + AI pattern issues
    """
    from prompts.linkedin_tools import QUALITY_CHECK_PROMPT

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # Format prompt for the specific platform
    prompt = QUALITY_CHECK_PROMPT.format(post=content)

    try:
        # Call Claude with web_search tool for fact checking
        messages = [{"role": "user", "content": prompt}]

        max_iterations = 5
        for iteration in range(max_iterations):
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

            # Try to parse JSON
            try:
                json_result = json.loads(final_text)
                if "scores" in json_result and "decision" in json_result:
                    return json_result
            except json.JSONDecodeError:
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
        async with httpx.AsyncClient(timeout=30.0) as client:
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
            human_prob = doc.get('average_generated_prob', 0) * 100
            ai_prob = doc.get('completely_generated_prob', 0) * 100
            mixed_prob = doc.get('partially_generated_prob', 0) * 100
            overall_class = doc.get('class_probabilities', {}).get('ai', 0)

            # Get flagged sentences
            sentences = doc.get('sentences', [])
            flagged = [
                s.get('sentence', '')
                for s in sentences
                if s.get('generated_prob', 0) > 0.7
            ]

            passes = human_prob > 70

            return {
                "status": "PASS" if passes else "FLAGGED",
                "human_probability": round(human_prob, 1),
                "ai_probability": round(ai_prob, 1),
                "mixed_probability": round(mixed_prob, 1),
                "overall_ai_score": round(overall_class * 100, 1),
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
    print("\n" + "="*60)
    print("🔍 RUNNING VALIDATORS")
    print("="*60)

    # Always run quality check (AI pattern detection)
    print("📊 Running quality check...")
    quality_result = await run_quality_check(content, platform)
    print(f"✅ Quality check complete: {quality_result.get('scores', {}).get('total', 0)}/25")

    # Optionally run GPTZero
    print("\n🤖 Checking GPTZero API key...")
    gptzero_result = await run_gptzero_check(content)
    if gptzero_result:
        print(f"✅ GPTZero check complete: {gptzero_result.get('status')}")
    else:
        print("⚠️ GPTZero API key not set - skipping")

    # Format for Airtable
    validation_data = {
        "quality_scores": quality_result.get('scores', {}),
        "decision": quality_result.get('decision'),
        "ai_patterns_found": quality_result.get('issues', []),
        "surgical_summary": quality_result.get('surgical_summary', ''),
        "gptzero": gptzero_result if gptzero_result else {"status": "NOT_RUN", "reason": "API key not configured"},
        "platform": platform,
        "timestamp": datetime.now().isoformat()
    }

    # Convert to JSON string for Airtable
    json_str = json.dumps(validation_data, indent=2)

    print("\n📋 Validation summary:")
    print(f"   Quality Score: {quality_result.get('scores', {}).get('total', 0)}/25")
    print(f"   AI Patterns Found: {len(quality_result.get('issues', []))}")
    if gptzero_result and gptzero_result.get('status') not in ['NOT_RUN', 'ERROR', 'SKIPPED']:
        print(f"   GPTZero: {gptzero_result.get('human_probability', 0)}% human")
    print("="*60 + "\n")

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

    # AI Patterns Found
    ai_patterns = data.get('ai_patterns_found', [])
    if ai_patterns:
        lines.append("⚡ AI Patterns Detected:")
        for pattern in ai_patterns:
            lines.append(f"   • {pattern}")
        lines.append("")

    # Surgical Summary
    surgical_summary = data.get('surgical_summary', '')
    if surgical_summary:
        lines.append("💡 Recommended Fixes:")
        lines.append(f"   {surgical_summary}")
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

"""
Instagram Native Tool Implementations
Unwrapped versions of tools from instagram_sdk_agent.py for direct API calling.
Uses EXACT same prompts, API parameters, and integrations.
"""

import json
import logging
from typing import Optional
from utils.anthropic_client import get_anthropic_client

logger = logging.getLogger(__name__)


async def generate_5_hooks_native(topic: str, context: str, target_audience: str = 'Instagram users') -> str:
    """Generate 5 Instagram hooks optimized for 125-char preview - EXACT implementation from SDK agent"""
    from prompts.instagram_tools import GENERATE_HOOKS_PROMPT

    print(f"   🔧 [TOOL] generate_5_hooks requesting client...", flush=True)
    client = get_anthropic_client()

    json_example = '[{{"type": "question", "text": "...", "chars": 82}}, ...]'
    prompt = GENERATE_HOOKS_PROMPT.format(
        topic=topic,
        context=context,
        audience=target_audience,
        json_example=json_example
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


async def search_company_documents_native(query: str, match_count: int = 3, document_type: Optional[str] = None) -> str:
    """Search company documents - EXACT implementation from SDK agent"""
    from tools.company_documents import search_company_documents as _search_func

    result = _search_func(
        query=query,
        match_count=match_count,
        document_type=document_type
    )

    return result


async def create_caption_draft_native(topic: str, hook: str, context: str) -> str:
    """Create Instagram caption draft - EXACT implementation from SDK agent"""
    from prompts.instagram_tools import CREATE_CAPTION_DRAFT_PROMPT, WRITE_LIKE_HUMAN_RULES

    print(f"   🔧 [TOOL] create_caption_draft requesting client...", flush=True)
    client = get_anthropic_client()

    prompt = CREATE_CAPTION_DRAFT_PROMPT.format(
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES,
        topic=topic,
        hook=hook,
        context=context
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    # Try to parse JSON, fallback to raw text if it fails
    try:
        json_result = json.loads(response_text)
        # Validate schema
        if "caption_text" in json_result or "post_text" in json_result:
            return json.dumps(json_result, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        pass

    # Fallback: return raw text wrapped in basic JSON
    return json.dumps({
        "caption_text": response_text,
        "self_assessment": {"total": 0, "notes": "JSON parsing failed, returning raw text"}
    }, indent=2)


async def condense_to_limit_native(caption: str, target_length: int = 2200) -> str:
    """Condense caption to fit Instagram's 2,200 character limit - EXACT implementation from SDK agent"""
    from prompts.instagram_tools import CONDENSE_TO_LIMIT_PROMPT

    print(f"   🔧 [TOOL] condense_to_limit requesting client...", flush=True)
    client = get_anthropic_client()

    current_length = len(caption)

    # If already under limit, return as-is
    if current_length <= target_length:
        return json.dumps({
            "caption": caption,
            "original_length": current_length,
            "target_length": target_length,
            "condensed": False,
            "note": "Already under limit"
        }, indent=2)

    prompt = CONDENSE_TO_LIMIT_PROMPT.format(
        caption=caption,
        current_length=current_length,
        target_length=target_length
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    condensed_caption = response.content[0].text

    return json.dumps({
        "caption": condensed_caption,
        "original_length": current_length,
        "new_length": len(condensed_caption),
        "target_length": target_length,
        "condensed": True,
        "chars_saved": current_length - len(condensed_caption)
    }, indent=2)


async def quality_check_native(post: str) -> str:
    """Quality check - EXACT implementation from SDK agent"""
    from prompts.instagram_tools import QUALITY_CHECK_PROMPT

    client = get_anthropic_client()

    # Modify prompt to skip web search verification (same as SDK version)
    prompt = QUALITY_CHECK_PROMPT.format(post=post) + """

IMPORTANT: For this evaluation, skip STEP 5 (web search verification).
Focus on steps 1-4 only: scanning for violations, creating issues, scoring, and making decision.
Mark any unverified claims as "NEEDS VERIFICATION" but do not attempt web searches."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text if response.content else ""

        # Try to parse as JSON
        try:
            json_result = json.loads(response_text)
            if "scores" in json_result and "decision" in json_result:
                if "searches_performed" not in json_result:
                    json_result["searches_performed"] = []
                json_result["note"] = "Fact verification skipped to avoid tool conflicts"
                return json.dumps(json_result, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

        return response_text

    except Exception as e:
        return json.dumps({
            "scores": {
                "hook": 0,
                "visual_pairing": 0,
                "readability": 0,
                "proof": 0,
                "cta_hashtags": 0,
                "total": 0,
                "ai_deductions": 0
            },
            "decision": "error",
            "issues": [],
            "surgical_summary": f"Quality check error: {str(e)}",
            "note": "Simplified quality check without web verification"
        }, indent=2)


async def external_validation_native(post: str) -> str:
    """External validation - EXACT implementation from SDK agent"""
    try:
        from integrations.validation_utils import run_all_validators

        # Run all validators (quality_check + GPTZero sequentially)
        validation_json = await run_all_validators(post, 'instagram')

        # Parse validation result with better error handling
        try:
            val_data = json.loads(validation_json) if isinstance(validation_json, str) else validation_json
        except json.JSONDecodeError as je:
            logger.error(f"❌ Failed to parse validation JSON: {je}")
            logger.error(f"   Raw JSON (first 500 chars): {str(validation_json)[:500]}")
            val_data = {
                "quality_scores": {"total": 18},
                "ai_patterns_found": [],
                "gptzero": {"status": "SKIPPED", "reason": "Validation JSON parse error"},
                "decision": "parse_error",
                "surgical_summary": f"Validation returned invalid JSON: {str(je)}"
            }

        # Extract key metrics
        quality_scores = val_data.get('quality_scores', {})
        total_score = quality_scores.get('total', 0)
        raw_issues = val_data.get('ai_patterns_found', [])
        gptzero = val_data.get('gptzero', {})

        # Normalize issues to dict format
        issues = []
        for issue in raw_issues:
            if isinstance(issue, dict):
                issues.append(issue)
            elif isinstance(issue, str):
                issues.append({
                    "severity": "medium",
                    "pattern": "unknown",
                    "original": issue,
                    "fix": "Review manually",
                    "impact": "Potential AI tell detected"
                })

        # GPTZero extraction
        gptzero_ai_pct = None
        gptzero_passes = None
        gptzero_flagged_sentences = []

        if gptzero and gptzero.get('status') in ['PASS', 'FLAGGED']:
            gptzero_ai_pct = gptzero.get('ai_probability', None)
            if gptzero_ai_pct is not None:
                gptzero_passes = gptzero_ai_pct < 100

            gptzero_flagged_sentences = gptzero.get('flagged_sentences', [])

        return json.dumps({
            "total_score": total_score,
            "quality_scores": quality_scores,
            "issues": issues,
            "gptzero_ai_pct": gptzero_ai_pct,
            "gptzero_passes": gptzero_passes,
            "gptzero_flagged_sentences": gptzero_flagged_sentences,
            "decision": val_data.get('decision', 'unknown'),
            "surgical_summary": val_data.get('surgical_summary', '')
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"❌ external_validation error: {e}")
        return json.dumps({
            "total_score": 18,
            "quality_scores": {"total": 18},
            "issues": [],
            "gptzero_ai_pct": None,
            "gptzero_passes": None,
            "gptzero_flagged_sentences": [],
            "decision": "error",
            "error": str(e),
            "surgical_summary": f"Validation error: {str(e)}"
        }, indent=2)


async def apply_fixes_native(
    post: str,
    issues_json: str,
    current_score: int,
    gptzero_ai_pct: Optional[float] = None,
    gptzero_flagged_sentences: Optional[list] = None
) -> str:
    """Apply fixes - EXACT implementation from SDK agent"""
    from prompts.instagram_tools import APPLY_FIXES_PROMPT, WRITE_LIKE_HUMAN_RULES

    print(f"   🔧 [TOOL] apply_fixes requesting client...", flush=True)
    client = get_anthropic_client()

    if gptzero_flagged_sentences is None:
        gptzero_flagged_sentences = []

    # ALWAYS comprehensive mode
    fix_strategy = "COMPREHENSIVE - Fix ALL issues, no limit on number of changes"

    # Format GPTZero flagged sentences
    flagged_sentences_text = "Not available"
    if gptzero_flagged_sentences:
        flagged_sentences_text = "\n".join([f"- {sent}" for sent in gptzero_flagged_sentences])

    prompt = APPLY_FIXES_PROMPT.format(
        post=post,
        issues_json=issues_json,
        current_score=current_score,
        gptzero_ai_pct=gptzero_ai_pct if gptzero_ai_pct is not None else "Not available",
        gptzero_flagged_sentences=flagged_sentences_text,
        fix_strategy=fix_strategy,
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    # Try to parse JSON
    try:
        json_result = json.loads(response_text)
        if "revised_post" in json_result:
            return json.dumps(json_result, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        pass

    # Fallback
    return json.dumps({
        "revised_post": response_text,
        "changes_made": [],
        "estimated_new_score": 0,
        "notes": "JSON parsing failed"
    }, indent=2)

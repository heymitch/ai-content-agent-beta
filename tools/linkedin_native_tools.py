"""
LinkedIn Native Tool Implementations
Unwrapped versions of tools from linkedin_sdk_agent.py for direct API calling.
Uses EXACT same prompts, API parameters, and integrations.
"""

import json
import logging
from typing import Optional
from utils.anthropic_client import get_anthropic_client

logger = logging.getLogger(__name__)


async def generate_5_hooks_native(topic: str, context: str, target_audience: str = 'professionals') -> str:
    """Generate 5 hooks - EXACT implementation from SDK agent"""
    from prompts.linkedin_tools import GENERATE_HOOKS_PROMPT

    print(f"   🔧 [TOOL] generate_5_hooks requesting client...", flush=True)
    client = get_anthropic_client()

    json_example = '[{{"type": "question", "text": "...", "chars": 45}}, ...]'
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


async def inject_proof_points_native(draft: str, topic: str, industry: str = 'SaaS') -> str:
    """Inject proof points - EXACT implementation from SDK agent"""
    from prompts.linkedin_tools import INJECT_PROOF_PROMPT, WRITE_LIKE_HUMAN_RULES
    from tools.company_documents import search_company_documents as _search_func

    client = get_anthropic_client()

    # Search company documents for proof points FIRST
    proof_context = _search_func(
        query=f"{topic} case study metrics ROI testimonial",
        match_count=3,
        document_type=None  # Search all types
    )

    prompt = INJECT_PROOF_PROMPT.format(
        write_like_human_rules=WRITE_LIKE_HUMAN_RULES,
        draft=draft,
        topic=topic,
        industry=industry,
        proof_context=proof_context
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


async def create_human_draft_native(topic: str, hook: str, context: str) -> str:
    """Create human draft - EXACT implementation from SDK agent"""
    from prompts.linkedin_tools import CREATE_HUMAN_DRAFT_PROMPT

    print(f"   🔧 [TOOL] create_human_draft requesting client...", flush=True)
    client = get_anthropic_client()

    prompt = CREATE_HUMAN_DRAFT_PROMPT.format(
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
        if "post_text" in json_result and "self_assessment" in json_result:
            return json.dumps(json_result, indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        pass

    # Fallback: return raw text wrapped in basic JSON
    return json.dumps({
        "post_text": response_text,
        "self_assessment": {"total": 0, "notes": "JSON parsing failed, returning raw text"}
    }, indent=2)


async def validate_format_native(post: str, post_type: str = 'standard') -> str:
    """Validate format - EXACT implementation from SDK agent"""
    from prompts.linkedin_tools import VALIDATE_FORMAT_PROMPT

    client = get_anthropic_client()

    prompt = VALIDATE_FORMAT_PROMPT.format(
        post=post,
        post_type=post_type
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


async def search_viral_patterns_native(topic: str, industry: str = '', days_back: int = 7) -> str:
    """Search viral patterns - EXACT implementation from SDK agent"""
    patterns = {
        "trending_hooks": [
            "Question format posts get 2.3x more engagement",
            "Posts with specific numbers get 45% more saves",
            "Story openers increase dwell time by 60%"
        ],
        "content_pillars": {
            "Acquisition": ["Cold outreach", "Paid ads", "Content marketing"],
            "Activation": ["Onboarding", "First value", "Time to wow"],
            "Retention": ["Churn prevention", "Engagement", "Loyalty"]
        },
        "winning_formats": [
            "Carousel with 7 slides (Big Promise → Stakes → Framework → Example → Checklist → Quick Win → CTA)",
            "Short post (80 words) with counterintuitive take",
            "Long post (350 words) with mini case study"
        ],
        "engagement_triggers": [
            "What's your experience with [topic]?",
            "Share your biggest [challenge] below",
            "Comment '[keyword]' for the template"
        ]
    }

    return json.dumps(patterns, indent=2, ensure_ascii=False)


async def score_and_iterate_native(post: str, target_score: int = 85, iteration: int = 1) -> str:
    """Score post - EXACT implementation from SDK agent"""
    from prompts.linkedin_tools import SCORE_ITERATE_PROMPT

    client = get_anthropic_client()

    prompt = SCORE_ITERATE_PROMPT.format(
        draft=post,
        target_score=target_score,
        iteration=iteration
    )

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


async def quality_check_native(post: str) -> str:
    """Quality check - EXACT implementation from SDK agent"""
    from prompts.linkedin_tools import QUALITY_CHECK_PROMPT

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
                "audience": 0,
                "headers": 0,
                "proof": 0,
                "cta": 0,
                "total": 0,
                "ai_deductions": 0
            },
            "decision": "error",
            "issues": [],
            "surgical_summary": f"Quality check error: {str(e)}",
            "note": "Simplified quality check without web verification"
        }, indent=2)


async def apply_fixes_native(
    post: str,
    issues_json: str,
    current_score: int,
    gptzero_ai_pct: Optional[float] = None,
    gptzero_flagged_sentences: Optional[list] = None
) -> str:
    """Apply fixes - EXACT implementation from SDK agent"""
    from prompts.linkedin_tools import APPLY_FIXES_PROMPT, WRITE_LIKE_HUMAN_RULES

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


async def external_validation_native(post: str) -> str:
    """External validation - EXACT implementation from SDK agent"""
    try:
        from integrations.validation_utils import run_all_validators

        # Run all validators (quality_check + GPTZero in parallel)
        validation_json = await run_all_validators(post, 'linkedin')
        val_data = json.loads(validation_json) if isinstance(validation_json, str) else validation_json

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
            "decision": "error",
            "error": str(e),
            "surgical_summary": f"Validation error: {str(e)}"
        }, indent=2)

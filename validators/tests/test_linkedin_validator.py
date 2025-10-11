"""Unit tests for LinkedInValidator deterministic checks."""
from __future__ import annotations

from typing import List, Tuple

from validators.linkedin_validator import (
    LinkedInValidator,
    check_alternation_rule,
    check_conclusion_and_cta,
    check_first_200_hook_and_cliffhanger,
    check_headers_sentence_style_and_mirroring,
    check_intro_length,
    check_section_lengths,
    check_specific_numbers,
    check_total_char_limit,
)


HOOK = (
    "You can add $100k in pipeline without posting daily—want the 3 plays we use "
    "to double meetings, reduce follow-ups, and protect your calendar from context "
    "switching while staying relevant to execs now?"
)

INTRO = (
    "Over the last 6 months we audited 37 SaaS sales teams and mapped the time sinks killing deals. "
    "We saw reps burn 11 hours per week chasing context, managers lack shared dashboards, and marketing forgets follow-up assets. "
    "This playbook shows how we tightened the system without adding headcount."
)

SECTION_BLOCKS: List[Tuple[str, str]] = [
    (
        "Step 1: Instrument the real buying moments.",
        "- Audit 90 days of CRM updates; tag every stage exit reason and quantify the leak in dollars.\n"
        "- Capture 3 trigger events (funding round, leadership change, hiring surge) and flag outbound to respond within 6 hours.\n"
        "- Require reps to log a 1-line win story and loss lesson every Friday; ship the summary to execs Monday.",
    ),
    (
        "Step 2: Script the micro-demo rhythm.",
        "Book 3 eighteen-minute micro demos per week and lead with the buyer's metric in slide one. "
        "Keep the walkthrough to 2 use cases, pause twice to validate the problem math, and log every objection verbatim. "
        "After each call, send a 4-bullet recap, a 2-minute Loom, and one question that tees up the next conversation.",
    ),
    (
        "Step 3: Operationalize the feedback loops.",
        "- Ship a Monday report showing demo-to-win %, average deal cycle, and onboarding NPS by segment.\n"
        "- Review the top 5 objections at Wednesday standup; update talk track lines and enablement docs live.\n"
        "- On Friday, trigger a 2-question survey to every lost deal and tag responses into a single Notion view for marketing.",
    ),
]

CONCLUSION = (
    "Run this sprint for 30 days and track the revenue per meeting change—then let me know which step would move the needle fastest for you?"
)


def build_post(
    hook: str = HOOK,
    intro: str = INTRO,
    section_blocks: List[Tuple[str, str]] = SECTION_BLOCKS,
    conclusion: str = CONCLUSION,
) -> str:
    """Assemble a LinkedIn post from supplied structural pieces."""
    parts: List[str] = [hook, "\n", intro, "\n\n"]
    for header, body in section_blocks:
        parts.append(f"{header}\n{body}\n\n")
    parts.append(conclusion)
    return "".join(parts)


def extract_issue_types(issues):
    return {issue.get("type") for issue in issues}


def test_spec_compliant_post_has_no_issues():
    validator = LinkedInValidator()
    content = build_post()
    issues = validator.validate(content)
    assert issues == []


def test_char_limit_violation_detected():
    oversized = build_post() + " extra" * 400  # push length beyond 2,800 chars
    issue = check_total_char_limit(oversized)
    assert issue is not None
    assert issue["type"] == "char_limit_exceeded"

    validator = LinkedInValidator()
    issues = validator.validate(oversized)
    assert "char_limit_exceeded" in extract_issue_types(issues)


def test_hook_cliffhanger_success():
    issues = check_first_200_hook_and_cliffhanger(build_post())
    assert issues == []


def test_hook_cliffhanger_failure():
    bad_hook = HOOK[:-1] + "."
    content = build_post(hook=bad_hook)
    issues = check_first_200_hook_and_cliffhanger(content)
    assert extract_issue_types(issues) == {"hook_cliffhanger_missing"}


def test_intro_length_in_range():
    assert check_intro_length(build_post()) is None


def test_intro_length_out_of_range():
    short_intro = "This intro is too short."  # <200 chars intentionally
    content = build_post(intro=short_intro)
    issue = check_intro_length(content)
    assert issue is not None
    assert issue["type"] == "intro_length_out_of_range"


def test_header_style_mirroring():
    issues = check_headers_sentence_style_and_mirroring(build_post())
    assert issues == []


def test_mixed_header_styles_flagged():
    mixed_sections = SECTION_BLOCKS.copy()
    mixed_sections = [*SECTION_BLOCKS]
    mixed_sections[1] = (
        "Mistake 2: Script the micro-demo rhythm.",
        SECTION_BLOCKS[1][1],
    )
    content = build_post(section_blocks=mixed_sections)
    issues = check_headers_sentence_style_and_mirroring(content)
    assert "mixed_styles_across_headers" in extract_issue_types(issues)


def test_header_sentence_style_required():
    sections = [*SECTION_BLOCKS]
    sections[0] = (
        "Step 1: Instrument the real buying moments",
        SECTION_BLOCKS[0][1],
    )
    content = build_post(section_blocks=sections)
    issues = check_headers_sentence_style_and_mirroring(content)
    assert "header_not_sentence_style" in extract_issue_types(issues)


def test_alternation_requires_bullets_first():
    sections = [
        (SECTION_BLOCKS[0][0], SECTION_BLOCKS[1][1]),
        SECTION_BLOCKS[1],
        SECTION_BLOCKS[2],
    ]
    content = build_post(section_blocks=sections)
    issue = check_alternation_rule(content)
    assert issue is not None
    assert issue["type"] == "alternation_expected_bullets"


def test_alternation_requires_paragraph_second():
    bullet_body = SECTION_BLOCKS[0][1]
    sections = [
        SECTION_BLOCKS[0],
        (SECTION_BLOCKS[1][0], bullet_body),
        SECTION_BLOCKS[2],
    ]
    content = build_post(section_blocks=sections)
    issue = check_alternation_rule(content)
    assert issue is not None
    assert issue["type"] == "alternation_expected_paragraph"


def test_section_length_enforced():
    short_bullets = "- One bullet."
    sections = [
        (SECTION_BLOCKS[0][0], short_bullets),
        SECTION_BLOCKS[1],
        SECTION_BLOCKS[2],
    ]
    content = build_post(section_blocks=sections)
    issues = check_section_lengths(content)
    types = extract_issue_types(issues)
    assert "section_length_out_of_range" in types


def test_conclusion_and_cta_pass():
    issues = check_conclusion_and_cta(build_post())
    assert issues == []


def test_conclusion_missing_cta():
    conclusion = (
        "Run this sprint for 30 days and track the revenue per meeting change—notice how the buyer math improves when each play stacks in sequence."
    )
    content = build_post(conclusion=conclusion)
    issues = check_conclusion_and_cta(content)
    assert "missing_cta" in extract_issue_types(issues)


def test_conclusion_question_cta_allowed():
    conclusion = (
        "Run this sprint for 30 days and track the revenue per meeting change—what do you think will move fastest?"
    )
    content = build_post(conclusion=conclusion)
    issues = check_conclusion_and_cta(content)
    assert issues == []


def test_conclusion_length_out_of_range():
    long_conclusion = (
        "Run this sprint for 30 days and track every revenue signal across the funnel, then let me know which play boosted demo-to-win percent, "
        "what friction stayed behind, and how you're rewriting your onboarding steps to keep the momentum compounding into Q4 and beyond."
    )
    content = build_post(conclusion=long_conclusion)
    issues = check_conclusion_and_cta(content)
    assert "conclusion_length_out_of_range" in extract_issue_types(issues)


def test_number_soft_check_warns_when_missing():
    issue = check_specific_numbers("No numbers anywhere in this paragraph of text.", min_numbers=1)
    assert issue is not None
    assert issue["type"] == "no_numbers_found"

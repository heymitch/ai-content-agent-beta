"""Indirect Email validator for faulty belief framework emails."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base_validator import BaseValidator


def check_one_sentence_per_line(content: str) -> List[Dict[str, Any]]:
    """Enforce one sentence per line (no double line breaks within sections)."""
    issues = []

    # Check for multiple sentences on same line (two sentence-ending punctuation marks)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        # Count sentence endings (. ! ?) that aren't abbreviations
        sentence_endings = len(re.findall(r'[.!?]\s+[A-Z]', line))
        if sentence_endings > 0:
            issues.append({
                "code": "multiple_sentences_per_line",
                "severity": "high",
                "auto_fixable": False,
                "message": f"Line {i+1} has multiple sentences - split into one sentence per line",
                "line": i+1
            })

    # Check for triple+ line breaks (only double allowed between sections)
    triple_breaks = re.findall(r'\n\n\n+', content)
    if triple_breaks:
        issues.append({
            "code": "excessive_line_breaks",
            "severity": "medium",
            "auto_fixable": False,
            "message": f"Found {len(triple_breaks)} instances of 3+ line breaks - max 2 allowed between sections"
        })

    return issues


def check_word_count(content: str, min_words: int = 400, max_words: int = 600) -> Optional[Dict[str, Any]]:
    """Check if email falls within Colin's 'bread and butter' length."""
    words = len(content.split())

    if words < min_words:
        return {
            "code": "word_count_too_short",
            "severity": "high",
            "auto_fixable": False,
            "message": f"Email is {words} words (target: {min_words}-{max_words}). Colin's 'bread and butter' length is 400-600 words.",
            "word_count": words
        }

    if words > max_words:
        return {
            "code": "word_count_too_long",
            "severity": "medium",
            "auto_fixable": False,
            "message": f"Email is {words} words (target: {min_words}-{max_words}). Trim to Colin's preferred range.",
            "word_count": words
        }

    return None


def check_subject_line(content: str) -> List[Dict[str, Any]]:
    """Validate subject line follows conversational story-driven patterns."""
    issues = []

    # Try to extract subject line (usually first line or labeled)
    lines = content.split('\n')
    subject_line = None

    for line in lines[:5]:  # Check first 5 lines
        if line.lower().startswith('subject:'):
            subject_line = line.split(':', 1)[1].strip()
            break
        # If first non-empty line and short, assume it's subject
        if line.strip() and len(line.strip()) < 80 and not subject_line:
            subject_line = line.strip()
            break

    if not subject_line:
        issues.append({
            "code": "subject_line_missing",
            "severity": "high",
            "auto_fixable": False,
            "message": "Subject line not found - should be first line or labeled 'Subject:'"
        })
        return issues

    # Check length (conversational = shorter)
    if len(subject_line) > 60:
        issues.append({
            "code": "subject_line_too_long",
            "severity": "medium",
            "auto_fixable": False,
            "message": f"Subject line is {len(subject_line)} chars (recommended: 30-60 for mobile)",
            "subject_line": subject_line
        })

    # Check for story-driven patterns
    story_patterns = [
        r"So .+ just told me",
        r"Because everyone thinks",
        r"The .+ lie nobody talks about",
        r"Why .+ is backwards",
        r".+ in \d+ (days|weeks|months)",
    ]

    has_pattern = any(re.search(pattern, subject_line, re.IGNORECASE) for pattern in story_patterns)

    if not has_pattern:
        issues.append({
            "code": "subject_line_not_story_driven",
            "severity": "low",
            "auto_fixable": False,
            "message": "Subject line doesn't follow proven patterns (So [client]..., Because everyone thinks..., Why [advice] is backwards...)",
            "subject_line": subject_line
        })

    return issues


def check_cta_formatting(content: str) -> List[Dict[str, Any]]:
    """Ensure CTAs use backtick format and only one primary CTA."""
    issues = []

    # Find all CTA mentions
    cta_with_backticks = re.findall(r'`\{\{(call|app|ghost)_cta\}\}`', content)
    cta_without_backticks = re.findall(r'(?<!`)\{\{(call|app|ghost)_cta\}\}(?!`)', content)

    # Flag CTAs without backticks
    if cta_without_backticks:
        issues.append({
            "code": "cta_missing_backticks",
            "severity": "high",
            "auto_fixable": True,
            "message": f"Found {len(cta_without_backticks)} CTAs without backticks - must use `{{{{cta}}}}`",
            "fix_hint": "Wrap all {{cta}} codes in backticks: `{{call_cta}}`"
        })

    # Check for multiple CTAs (only one primary allowed)
    total_ctas = len(cta_with_backticks) + len(cta_without_backticks)
    if total_ctas > 1:
        issues.append({
            "code": "multiple_ctas",
            "severity": "high",
            "auto_fixable": False,
            "message": f"Found {total_ctas} CTAs - use only ONE primary call-to-action",
            "fix_hint": "Pick the single most important action and remove others"
        })

    if total_ctas == 0:
        issues.append({
            "code": "cta_missing",
            "severity": "high",
            "auto_fixable": False,
            "message": "No CTA found - must include one of: `{{call_cta}}`, `{{app_cta}}`, or `{{ghost_cta}}`"
        })

    return issues


def check_forbidden_ai_phrases(content: str) -> List[Dict[str, Any]]:
    """Check for AI detection red flags."""
    issues = []

    forbidden_phrases = {
        # Contrast formats (already checked in LinkedIn, but critical for email too)
        "contrast_patterns": [
            r"(?:isn't|is not)\s+about\s+\w+[—,]\s*(?:it's|it is)\s+about",
            r"(?:it's|it is)\s+not\s+\w+[,]\s*(?:it's|it is)",
            r"These\s+\w+\s+haven't\s+made\s+\w+\s+more\s+\w+[—,]\s*they've\s+made\s+it",
        ],
        # Robotic transitions
        "robotic_transitions": [
            r"Here's the thing:",
            r"The reality is this:",
            r"At the end of the day,",
            r"The bottom line is:",
            r"When all is said and done,",
            r"The truth is,",
            r"Let me be clear:",
        ],
        # AI crutch phrases
        "ai_crutches": [
            r"Let's dive deep into",
            r"Let's unpack this",
            r"Here's what you need to know:",
            r"The key takeaway is",
            r"In today's digital landscape",
            r"In an ever-evolving world",
            r"In this day and age",
            r"Moving forward,",
        ],
        # Generic list introductions
        "generic_lists": [
            r"Here are \d+ ways to",
            r"Let me share \d+ strategies",
            r"I'm going to break down \d+ methods",
            r"Below are \d+ tips to",
        ],
    }

    for category, patterns in forbidden_phrases.items():
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "code": f"forbidden_ai_phrase_{category}",
                    "severity": "high",
                    "auto_fixable": False,
                    "message": f"AI detection red flag: '{match.group()}' - rewrite naturally",
                    "phrase": match.group(),
                    "span": (match.start(), match.end())
                })

    return issues


def check_faulty_belief_structure(content: str) -> List[Dict[str, Any]]:
    """Verify email follows faulty belief framework."""
    issues = []

    # Look for framework components (case-insensitive markers)
    content_lower = content.lower()

    # Check for story/case study (should have client mention early)
    has_client_story = bool(re.search(r'(client|customer|student|member)\s+\w+', content[:800], re.IGNORECASE))

    # Check for faulty belief language
    has_faulty_belief = any(phrase in content_lower for phrase in [
        'most people think',
        'everyone says',
        'common belief',
        'conventional wisdom',
        'the problem is',
    ])

    # Check for truth/solution
    has_truth = any(phrase in content_lower for phrase in [
        'actually',
        'instead',
        'what really',
        'the truth',
        'here\'s what',
    ])

    # Check for proof/results
    has_proof = bool(re.search(r'\d+%|\$\d+|in \d+ (days|weeks|months)', content))

    if not has_client_story:
        issues.append({
            "code": "missing_client_story",
            "severity": "high",
            "auto_fixable": False,
            "message": "No specific client example found in first 800 chars - indirect emails need concrete case study",
            "fix_hint": "Add client name and specific situation early in email"
        })

    if not has_faulty_belief:
        issues.append({
            "code": "missing_faulty_belief",
            "severity": "high",
            "auto_fixable": False,
            "message": "Faulty belief not clearly stated - use phrases like 'Most people think...' or 'Everyone says...'",
            "fix_hint": "Explicitly challenge the common belief that's wrong"
        })

    if not has_truth:
        issues.append({
            "code": "missing_truth",
            "severity": "high",
            "auto_fixable": False,
            "message": "Truth/solution not clearly presented - show what actually works instead",
            "fix_hint": "Use 'Actually...' or 'Instead...' to present the real solution"
        })

    if not has_proof:
        issues.append({
            "code": "missing_proof",
            "severity": "medium",
            "auto_fixable": False,
            "message": "No specific numbers/metrics found - add concrete results for credibility",
            "fix_hint": "Include percentages, dollar amounts, or timeframes"
        })

    return issues


class EmailIndirectValidator(BaseValidator):
    """Validator for indirect emails using faulty belief framework."""

    def validate(self, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        # Formatting checks
        issues.extend(check_one_sentence_per_line(content))

        word_count_issue = check_word_count(content, min_words=400, max_words=600)
        if word_count_issue:
            issues.append(word_count_issue)

        # Email-specific checks
        issues.extend(check_subject_line(content))
        issues.extend(check_cta_formatting(content))

        # AI detection
        issues.extend(check_forbidden_ai_phrases(content))

        # Framework validation
        issues.extend(check_faulty_belief_structure(content))

        return issues

    def get_grading_rubric(self) -> str:
        return """
INDIRECT EMAIL GRADING RUBRIC (0-100)

Subject Line & Hook (20 points)
- Story-driven subject following proven patterns
- Hook challenges belief or shares surprising insight
- Conversational, not clickbait

Faulty Belief Framework (30 points)
- Specific client case study with real details
- Clear statement of faulty/common belief
- Explanation of why it's wrong
- Counter-intuitive truth presented
- Proof with specific numbers/results

Structure & Flow (20 points)
- One sentence per line (no exceptions)
- Natural "So" and "Because" transitions
- Colin's "bread and butter" length (400-600 words)
- Clear bridge to reader's situation

Voice & Authenticity (20 points)
- Conversational teacher tone (not salesy)
- Specific details: names, numbers, timeframes
- Natural language (passes AI detection test)
- Challenges assumptions respectfully

CTA Integration (10 points)
- Single, clear call-to-action
- Properly formatted with backticks
- Natural integration (not forced)
- Value proposition clear

DEDUCTIONS:
- AI phrases detected: -25 points per instance
- Multiple CTAs: -15 points
- Generic case study: -20 points
- Missing faulty belief: -30 points
- Formatting violations: -10 points each
"""

    def get_writing_rules(self) -> str:
        return """
INDIRECT EMAIL WRITING RULES

1. Use faulty belief framework (Common Belief → Why Wrong → Truth → Proof)
2. Include specific client case study with real details
3. One sentence per line (absolutely no exceptions)
4. 400-600 words (Colin's preferred length)
5. Story-driven subject line (conversational, not clickbait)
6. Natural transitions with "So" and "Because"
7. Single CTA with backticks: `{{call_cta}}` or `{{app_cta}}`
8. Challenge conventional wisdom respectfully
9. Include specific metrics and timeframes
10. Sign off as "Colin"

FORBIDDEN:
- AI phrases (Here's the thing, Let's dive deep, etc.)
- Multiple CTAs
- Generic advice without personal experience
- Formal/corporate language
- Contrast clichés (not X but Y)
"""

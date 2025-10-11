"""Direct Email validator for short, conversion-focused emails."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base_validator import BaseValidator


def check_word_count_direct(content: str, min_words: int = 100, max_words: int = 200) -> Optional[Dict[str, Any]]:
    """Check if email is properly short and focused."""
    words = len(content.split())

    if words < min_words:
        return {
            "code": "word_count_too_short",
            "severity": "medium",
            "auto_fixable": False,
            "message": f"Email is {words} words (target: {min_words}-{max_words}). Add more value/urgency.",
            "word_count": words
        }

    if words > max_words:
        return {
            "code": "word_count_too_long",
            "severity": "high",
            "auto_fixable": False,
            "message": f"Email is {words} words (target: {min_words}-{max_words}). Direct emails must be SHORT and focused.",
            "word_count": words
        }

    return None


def check_subject_line_direct(content: str) -> List[Dict[str, Any]]:
    """Validate subject line for direct conversion patterns."""
    issues = []

    lines = content.split('\n')
    subject_line = None

    for line in lines[:5]:
        if line.lower().startswith('subject:'):
            subject_line = line.split(':', 1)[1].strip()
            break
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

    # Check length (direct = super tight)
    if len(subject_line) > 35:
        issues.append({
            "code": "subject_line_too_long",
            "severity": "high",
            "auto_fixable": False,
            "message": f"Subject line is {len(subject_line)} chars (direct emails: 20-35 max for urgency)",
            "subject_line": subject_line
        })

    if len(subject_line) < 15:
        issues.append({
            "code": "subject_line_too_short",
            "severity": "low",
            "auto_fixable": False,
            "message": f"Subject line is {len(subject_line)} chars (might lack clarity)",
            "subject_line": subject_line
        })

    # Check for proven patterns
    question_pattern = re.search(r'Ready to|Want to|\?$', subject_line, re.IGNORECASE)
    urgency_pattern = re.search(r'Last call|spots left|closes|deadline', subject_line, re.IGNORECASE)
    personal_pattern = re.search(r'Quick question|This is for you', subject_line, re.IGNORECASE)

    has_pattern = any([question_pattern, urgency_pattern, personal_pattern])

    if not has_pattern:
        issues.append({
            "code": "subject_line_weak_pattern",
            "severity": "medium",
            "auto_fixable": False,
            "message": "Subject doesn't follow proven direct patterns (Question: 'Ready to X?', Urgency: 'Last call for X', Personal: 'Quick question')",
            "subject_line": subject_line
        })

    return issues


def check_direct_hook(content: str) -> List[Dict[str, Any]]:
    """Check for strong direct opening that assumes interest."""
    issues = []

    # Get first 200 chars after subject line
    lines = [l for l in content.split('\n') if l.strip()]
    if len(lines) < 2:
        issues.append({
            "code": "content_too_short",
            "severity": "high",
            "auto_fixable": False,
            "message": "Email body is missing or too short"
        })
        return issues

    # Skip subject line, get opening
    opening = ' '.join(lines[1:3])[:200].lower()

    # Check for direct hook patterns
    has_question_hook = 'quick question' in opening or 'are you ready' in opening
    has_assumption_hook = 'if you\'re serious' in opening or 'this is for you' in opening
    has_urgency_hook = 'we close' in opening or 'last call' in opening or 'applications close' in opening

    if not any([has_question_hook, has_assumption_hook, has_urgency_hook]):
        issues.append({
            "code": "weak_direct_hook",
            "severity": "high",
            "auto_fixable": False,
            "message": "Opening doesn't use proven direct patterns (Question: 'Quick question:', Assumption: 'If you're serious about X', Urgency: 'We close applications...')",
            "fix_hint": "Start with direct assumption of interest - these are WARM leads"
        })

    return issues


def check_social_proof(content: str) -> Optional[Dict[str, Any]]:
    """Ensure direct email includes client example for credibility."""
    content_lower = content.lower()

    # Look for client mentions with results
    has_client_mention = bool(re.search(r'(client|member|student|founder)\s+\w+', content, re.IGNORECASE))
    has_result = bool(re.search(r'\$\d+|[\d]+%|\d+[xX]|in \d+ (days|weeks|months)', content))

    if has_client_mention and has_result:
        return None  # Has social proof

    return {
        "code": "missing_social_proof",
        "severity": "medium",
        "auto_fixable": False,
        "message": "No client example with specific result found - add social proof for credibility",
        "fix_hint": "Include '[Client] just [specific result] in [timeframe]' for trust"
    }


def check_urgency_element(content: str) -> Optional[Dict[str, Any]]:
    """Verify email includes scarcity or urgency driver."""
    content_lower = content.lower()

    urgency_phrases = [
        'close',
        'deadline',
        'spots left',
        'last call',
        'only',
        'limited',
        'expires',
        'ends',
    ]

    has_urgency = any(phrase in content_lower for phrase in urgency_phrases)

    # Check for specific constraints (dates, numbers)
    has_specific_urgency = bool(re.search(r'(closes?|deadline|ends?|expire[sd]?)\s+(in|on|by|this|next)', content_lower)) or \
                          bool(re.search(r'\d+\s+spots?', content_lower))

    if not has_urgency:
        return {
            "code": "missing_urgency",
            "severity": "high",
            "auto_fixable": False,
            "message": "No urgency element detected - direct emails need scarcity/deadline to drive action",
            "fix_hint": "Add 'We close applications [date]' or '[X] spots left' or 'Last call for [offer]'"
        }

    if has_urgency and not has_specific_urgency:
        return {
            "code": "urgency_not_specific",
            "severity": "medium",
            "auto_fixable": False,
            "message": "Urgency is vague - make it specific (exact date, number of spots, etc.)",
            "fix_hint": "Replace 'limited time' with 'closes Friday' or '3 spots left'"
        }

    return None


def check_premium_positioning(content: str) -> List[Dict[str, Any]]:
    """Ensure language reflects premium $10K+ ghostwriting business positioning."""
    issues = []
    content_lower = content.lower()

    # Flag low-end positioning
    low_end_terms = [
        'freelancer',
        'upwork',
        'fiverr',
        'side hustle',
        'gig',
        'content mill',
    ]

    for term in low_end_terms:
        if term in content_lower:
            issues.append({
                "code": "low_end_positioning",
                "severity": "high",
                "auto_fixable": False,
                "message": f"Avoid '{term}' - positions as commodity work instead of premium business",
                "fix_hint": "Use 'ghostwriting business', 'retainer clients', 'premium positioning'"
            })

    # Check for premium language
    has_premium = any(phrase in content_lower for phrase in [
        '$10k',
        '$15k',
        '$20k',
        'retainer',
        'premium',
        'high-ticket',
        'per month',
    ])

    if not has_premium:
        issues.append({
            "code": "missing_premium_positioning",
            "severity": "medium",
            "auto_fixable": False,
            "message": "No premium outcome language - specify $10K+ monthly business positioning",
            "fix_hint": "Mention specific premium outcomes: 'Land $15K retainer clients' or '$10K+/month ghostwriting business'"
        })

    return issues


class EmailDirectValidator(BaseValidator):
    """Validator for direct conversion emails (100-200 words)."""

    def validate(self, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        # Import shared checks
        from .email_indirect_validator import (
            check_one_sentence_per_line,
            check_cta_formatting,
            check_forbidden_ai_phrases
        )

        # Formatting checks (shared)
        issues.extend(check_one_sentence_per_line(content))
        issues.extend(check_cta_formatting(content))
        issues.extend(check_forbidden_ai_phrases(content))

        # Direct-specific checks
        word_count_issue = check_word_count_direct(content, min_words=100, max_words=200)
        if word_count_issue:
            issues.append(word_count_issue)

        issues.extend(check_subject_line_direct(content))
        issues.extend(check_direct_hook(content))

        social_proof_issue = check_social_proof(content)
        if social_proof_issue:
            issues.append(social_proof_issue)

        urgency_issue = check_urgency_element(content)
        if urgency_issue:
            issues.append(urgency_issue)

        issues.extend(check_premium_positioning(content))

        return issues

    def get_grading_rubric(self) -> str:
        return """
DIRECT EMAIL GRADING RUBRIC (0-100)

Subject Line & Hook (25 points)
- Tight subject (20-35 chars) with question/urgency pattern
- Direct hook assumes interest/readiness
- No explanation needed - straight to value

Value & Benefits (20 points)
- 2-3 specific benefits clearly stated
- Premium positioning ($10K+ outcomes)
- Business-first language (not freelance/gig talk)

Social Proof (15 points)
- Recent client example included
- Specific result with numbers
- Timeframe mentioned

Urgency (20 points)
- Clear scarcity/deadline element
- Specific constraints (date, number of spots)
- Drives immediate action

CTA & Focus (15 points)
- Single, clear CTA with proper formatting
- Confident tone (not apologetic)
- One obvious next step

Length & Efficiency (5 points)
- 100-200 words (short and focused)
- Every sentence drives to action
- No fluff or long explanations

DEDUCTIONS:
- AI phrases detected: -25 points per instance
- Low-end positioning (freelancer, Upwork): -20 points
- Vague urgency: -15 points
- Multiple CTAs: -15 points
- Weak hook: -20 points
- Missing social proof: -10 points
"""

    def get_writing_rules(self) -> str:
        return """
DIRECT EMAIL WRITING RULES

1. LENGTH: 100-200 words only (short and focused)
2. SUBJECT: 20-35 chars with question/urgency pattern
3. HOOK: Direct assumption of interest (they're warm/engaged)
4. BENEFITS: 2-3 specific outcomes stated clearly
5. SOCIAL PROOF: Include recent client example with result
6. URGENCY: Specific deadline or limited spots
7. CTA: Single, clear action with backticks
8. POSITIONING: Premium $10K+ business outcomes
9. TONE: Confident, not pushy or apologetic
10. FORMAT: One sentence per line

FORBIDDEN:
- Long explanations (they already know your value)
- Multiple CTAs (one action only)
- Vague urgency ("limited time")
- Low-end language (freelancer, gig, side hustle)
- Apologetic tone ("if you're interested, maybe...")
- AI phrases (Here's the thing, Let's dive deep, etc.)
"""

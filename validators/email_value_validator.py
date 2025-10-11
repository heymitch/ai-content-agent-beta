"""Value Email validator with tactical depth enforcement."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .base_validator import BaseValidator


def check_word_count_value(content: str, min_words: int = 400, max_words: int = 500) -> Optional[Dict[str, Any]]:
    """Check if value email is in optimal engagement range."""
    words = len(content.split())

    if words < min_words:
        return {
            "code": "word_count_too_short",
            "severity": "medium",
            "auto_fixable": False,
            "message": f"Email is {words} words (target: {min_words}-{max_words}). Add more tactical depth.",
            "word_count": words
        }

    if words > max_words:
        return {
            "code": "word_count_too_long",
            "severity": "medium",
            "auto_fixable": False,
            "message": f"Email is {words} words (target: {min_words}-{max_words}). Value emails over 500 words see engagement drop.",
            "word_count": words
        }

    return None


def check_subject_line_value(content: str) -> List[Dict[str, Any]]:
    """Validate subject line emphasizes SINGLE tool/outcome."""
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
            "message": "Subject line not found"
        })
        return issues

    # Check length
    if len(subject_line) > 45:
        issues.append({
            "code": "subject_line_too_long",
            "severity": "medium",
            "auto_fixable": False,
            "message": f"Subject line is {len(subject_line)} chars (target: 30-45 for value emails)",
            "subject_line": subject_line
        })

    if len(subject_line) < 25:
        issues.append({
            "code": "subject_line_too_short",
            "severity": "low",
            "auto_fixable": False,
            "message": f"Subject line is {len(subject_line)} chars (might lack specificity)",
            "subject_line": subject_line
        })

    # Check for single tool focus (PGA data: breadth kills conversions)
    breadth_patterns = [
        r'\d+\s+tools',
        r'\d+\s+ways',
        r'\d+\s+strategies',
        r'\d+\s+tips',
    ]

    has_breadth = any(re.search(pattern, subject_line, re.IGNORECASE) for pattern in breadth_patterns)

    if has_breadth:
        issues.append({
            "code": "subject_breadth_approach",
            "severity": "high",
            "auto_fixable": False,
            "message": "Subject uses breadth approach (7 tools, 5 ways, etc.) - PGA data shows 0 bookings with this pattern. Focus on SINGLE tool.",
            "subject_line": subject_line,
            "fix_hint": "Change to 'The [specific tool] that [specific outcome]' or 'How I [result] with ONE [tool]'"
        })

    # Check for single tool pattern
    single_tool_patterns = [
        r'(the|one)\s+\w+\s+that',
        r'how i\s+\w+\s+with\s+(one|a single)',
        r'the\s+\w+\s+workflow',
    ]

    has_single_focus = any(re.search(pattern, subject_line, re.IGNORECASE) for pattern in single_tool_patterns)

    if not has_single_focus and not has_breadth:  # Don't double-flag
        issues.append({
            "code": "subject_not_single_tool",
            "severity": "medium",
            "auto_fixable": False,
            "message": "Subject doesn't emphasize single tool focus - use proven patterns",
            "subject_line": subject_line,
            "fix_hint": "Use '[Specific tool] that [outcome]' or 'How I [result] with ONE [tool]'"
        })

    return issues


def check_tool_depth(content: str) -> List[Dict[str, Any]]:
    """Enforce tactical depth: max 2 tools, primary gets 150+ words with 3+ steps."""
    issues = []

    # Count tool mentions (capitalized names or tools in backticks/quotes)
    tool_pattern = r'(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:for|to|is|lets|helps)'
    tools_mentioned = re.findall(tool_pattern, content, re.MULTILINE)

    # Also look for multiple bulleted/numbered tool lists
    list_sections = re.findall(r'(?:^|\n)(?:\d+\.|[-•])\s+([A-Z]\w+)', content, re.MULTILINE)

    total_tools = len(set(tools_mentioned + list_sections))

    if total_tools > 2:
        issues.append({
            "code": "too_many_tools",
            "severity": "high",
            "auto_fixable": False,
            "message": f"Found {total_tools} tools mentioned - MAXIMUM 2 tools (1 primary + 1 supporting). PGA data: breadth = 0 conversions.",
            "fix_hint": "Pick ONE primary tool and go deep with 3+ step-by-step instructions"
        })

    # Check for step-by-step instructions (tactical depth marker)
    has_steps = bool(re.search(r'(?:step|first|then|next|finally)\s+(?:\d+|one|two|three)', content, re.IGNORECASE))
    has_numbered_list = bool(re.search(r'(?:^|\n)\d+\.\s+\w+', content, re.MULTILINE))

    if not has_steps and not has_numbered_list:
        issues.append({
            "code": "missing_tactical_steps",
            "severity": "high",
            "auto_fixable": False,
            "message": "No step-by-step setup instructions found - value emails must include 3+ tactical steps",
            "fix_hint": "Add 'Step 1: [action]', 'Step 2: [action]', etc. with interface details"
        })

    # Check for interface/screenshot details (shows tactical depth)
    interface_keywords = [
        'menu',
        'button',
        'click',
        'tab',
        'settings',
        'dashboard',
        'sidebar',
        'panel',
        'dropdown',
        'toggle',
    ]

    has_interface_details = any(keyword in content.lower() for keyword in interface_keywords)

    if not has_interface_details:
        issues.append({
            "code": "missing_interface_details",
            "severity": "high",
            "auto_fixable": False,
            "message": "No interface/UI details found - describe what user sees ('In the top menu...', 'Click the Settings tab...')",
            "fix_hint": "Add specific interface guidance so reader can follow along"
        })

    # Check for troubleshooting section
    has_troubleshooting = bool(re.search(r'if\s+.+\s+(?:happens|doesn\'t work|fails|issue)', content, re.IGNORECASE))

    if not has_troubleshooting:
        issues.append({
            "code": "missing_troubleshooting",
            "severity": "medium",
            "auto_fixable": False,
            "message": "No troubleshooting guidance found - add 'If [common issue] happens, [specific fix]'",
            "fix_hint": "Anticipate where readers get stuck and provide fixes"
        })

    # Check for specific results with metrics
    has_results = bool(re.search(r'(?:saved|reduced|increased|generated)\s+(?:\d+|me)\s+(?:%|hours|minutes|posts|clients)', content, re.IGNORECASE))

    if not has_results:
        issues.append({
            "code": "missing_specific_results",
            "severity": "medium",
            "auto_fixable": False,
            "message": "No specific results with metrics found - include 'Saved me 5 hours per week' or 'Reduced planning time by 40%'",
            "fix_hint": "Share YOUR actual results with exact numbers and timeframe"
        })

    return issues


def check_personal_credibility_hook(content: str) -> Optional[Dict[str, Any]]:
    """Verify opening establishes personal experience with tool."""
    # Get first 300 chars after subject
    lines = [l for l in content.split('\n') if l.strip()]
    if len(lines) < 3:
        return {
            "code": "content_too_short",
            "severity": "high",
            "auto_fixable": False,
            "message": "Email body too short"
        }

    opening = ' '.join(lines[1:5])[:300].lower()

    # Look for personal credibility markers
    credibility_patterns = [
        r'i started\s+\w+\s+in\s+\d{4}',
        r'back then',
        r'i\'ve been',
        r'for the last\s+\d+\s+years',
        r'when i first',
    ]

    has_credibility = any(re.search(pattern, opening) for pattern in credibility_patterns)

    if not has_credibility:
        return {
            "code": "missing_credibility_hook",
            "severity": "medium",
            "auto_fixable": False,
            "message": "Opening doesn't establish personal credibility - start with 'I started [activity] in [year]' or 'I've been [doing X] for [Y] years'",
            "fix_hint": "Build authority before recommending tools"
        }

    return None


def check_soft_cta(content: str) -> Optional[Dict[str, Any]]:
    """Ensure CTA is educational/helpful, not aggressive."""
    content_lower = content.lower()

    # Look for soft CTA phrases
    soft_patterns = [
        'as a reminder',
        'hope this helps',
        'if you\'d like',
        'check out',
        'learn more',
    ]

    has_soft_approach = any(phrase in content_lower for phrase in soft_patterns)

    # Look for aggressive/direct CTA (wrong for value emails)
    aggressive_patterns = [
        'buy now',
        'sign up today',
        'don\'t wait',
        'limited time',
        'act now',
    ]

    has_aggressive = any(phrase in content_lower for phrase in aggressive_patterns)

    if has_aggressive:
        return {
            "code": "cta_too_aggressive",
            "severity": "high",
            "auto_fixable": False,
            "message": "CTA is too aggressive for value email - use soft educational tie-in",
            "fix_hint": "Try 'As a reminder: If you'd like us to help you [goal], check out [offer]' or 'Hope this helps. If you want more, here's [offer]'"
        }

    if not has_soft_approach:
        return {
            "code": "cta_not_soft_enough",
            "severity": "medium",
            "auto_fixable": False,
            "message": "CTA doesn't use soft/helpful tone - value emails build goodwill, not direct selling",
            "fix_hint": "Use 'As a reminder' or 'Hope this helps' framing"
        }

    return None


class EmailValueValidator(BaseValidator):
    """Validator for value emails with tactical depth enforcement."""

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

        # Value-specific checks
        word_count_issue = check_word_count_value(content, min_words=400, max_words=500)
        if word_count_issue:
            issues.append(word_count_issue)

        issues.extend(check_subject_line_value(content))
        issues.extend(check_tool_depth(content))

        credibility_issue = check_personal_credibility_hook(content)
        if credibility_issue:
            issues.append(credibility_issue)

        soft_cta_issue = check_soft_cta(content)
        if soft_cta_issue:
            issues.append(soft_cta_issue)

        return issues

    def get_grading_rubric(self) -> str:
        return """
VALUE EMAIL GRADING RUBRIC (0-100)

Subject Line (15 points)
- Emphasizes SINGLE tool/outcome (not breadth)
- 30-45 chars (specific and clear)
- Follows proven pattern: "[Tool] that [outcome]"

Opening & Credibility (15 points)
- Personal credibility established
- Problem recognition for reader
- Natural conversational flow

Tactical Depth (40 points) - MOST IMPORTANT
- Maximum 2 tools (1 primary + 1 optional supporting)
- Primary tool gets 150+ words with deep implementation
- Minimum 3 step-by-step setup instructions
- Interface/UI details described ("In the Settings menu...")
- Troubleshooting section included
- Specific results with metrics and timeframe
- Why this beats alternatives explained

Voice & Delivery (15 points)
- Helpful teacher tone (not salesy)
- Specific tool names and use cases
- Personal experience shared
- Conversational and practical

CTA & Structure (15 points)
- Soft CTA with educational framing
- Proper backtick formatting
- One sentence per line throughout
- 400-500 word target

DEDUCTIONS:
- AI phrases detected: -25 points each
- Breadth approach (3+ tools): -40 points (PGA data: kills conversions)
- Missing tactical steps: -30 points
- No interface details: -25 points
- Aggressive CTA: -15 points
- Overview/listicle format: -50 points (proven 0 bookings)
"""

    def get_writing_rules(self) -> str:
        return """
VALUE EMAIL WRITING RULES

1. SINGLE TOOL FOCUS: Maximum 2 tools (1 primary + 1 supporting)
2. TACTICAL DEPTH: Primary tool gets 150+ words with 3+ steps
3. INTERFACE DETAILS: Describe what user sees and clicks
4. TROUBLESHOOTING: Include common issues and fixes
5. YOUR RESULTS: Exact metrics and timeframe
6. LENGTH: 400-500 words (optimal engagement zone)
7. SUBJECT: 30-45 chars emphasizing single tool
8. HOOK: Personal credibility + problem recognition
9. CTA: Soft educational tie-in (not aggressive)
10. FORMAT: One sentence per line

FORBIDDEN:
- Breadth approach (5 tools, 7 ways, etc.)
- Surface-level explanations without steps
- Generic advice without personal experience
- Tools you don't actually use
- Overview/listicle format
- Aggressive sales CTA
- AI phrases (Here's the thing, Let's unpack, etc.)

REMEMBER: PGA data shows breadth = 0 bookings. Go DEEP on ONE tool.
"""

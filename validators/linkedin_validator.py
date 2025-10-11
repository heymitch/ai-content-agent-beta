"""LinkedIn validator aligned with structured long-form framework."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from .base_validator import BaseValidator
from .pattern_library import ForbiddenPatterns


def char_count(text: str) -> int:
    """Return character count for provided text (treat None as 0)."""
    return len(text or "")


def split_visible_preview_and_rest(
    content: str, preview_chars: int = 200
) -> Tuple[str, str]:
    """Split LinkedIn content into preview chunk and remaining text."""
    preview = content[:preview_chars]
    rest = content[len(preview):]
    return preview, rest


def has_cliffhanger(preview: str) -> bool:
    """Determine if LinkedIn preview ends with an approved cliffhanger."""
    if not preview:
        return False

    snippet = preview.rstrip()
    if not snippet:
        return False

    if snippet.endswith("?"):
        return True
    if snippet.endswith("...") or snippet.endswith("…"):
        return True
    if snippet.endswith(":"):
        return True

    last_char = snippet[-1]
    return last_char not in {".", "!", "?"}


HEADER_STYLE_PREFIXES = ["Step", "Stat", "Mistake", "Lesson", "Example"]

HEADER_CANDIDATE_REGEX = re.compile(
    rf"^(?:{'|'.join(HEADER_STYLE_PREFIXES)})\s+\d+\s*(?:[:\-])\s+.+$"
)
HEADER_LINE_PATTERN = re.compile(
    rf"(?m)^(?:{'|'.join(HEADER_STYLE_PREFIXES)})\s+\d+\s*(?:[:\-])\s+.+$"
)
BULLET_REGEX = re.compile(r"^\s*[-•–\*]\s+")


def detect_headers(lines: List[str]) -> List[Tuple[int, str]]:
    """Identify header-looking lines with their indices."""
    headers: List[Tuple[int, str]] = []
    for idx, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if HEADER_CANDIDATE_REGEX.match(stripped):
            headers.append((idx, stripped))
    return headers


def is_sentence_style(line: str) -> bool:
    """Validate headers follow sentence-style conventions."""
    text = (line or "").strip()
    if not text:
        return False

    if text[-1] not in ".!?":
        return False

    first_char = text[0]
    if not first_char.isupper():
        return False

    sentences = re.findall(r"[A-Z0-9\"'][^.!?]*[.!?]", text)
    return len(sentences) == 1


def detect_style_prefix(line: str) -> Optional[str]:
    """Return the detected style prefix or None."""
    text = (line or "").lstrip()
    for prefix in HEADER_STYLE_PREFIXES:
        if text.startswith(f"{prefix} "):
            return prefix
    return None


def _lines_with_offsets(text: str) -> Tuple[List[str], List[int]]:
    """Split text into lines while keeping starting char offsets."""
    raw_lines = text.splitlines(keepends=True)
    offsets: List[int] = []
    cursor = 0
    for raw_line in raw_lines:
        offsets.append(cursor)
        cursor += len(raw_line)
    return raw_lines, offsets


def _find_conclusion_block(remainder: str) -> Tuple[int, int, str]:
    """Locate conclusion block within remainder text (local offsets)."""
    if not remainder:
        return len(remainder), len(remainder), ""

    trimmed_trailing = remainder.rstrip()
    if not trimmed_trailing:
        return len(remainder), len(remainder), ""

    marker = "\n\n"
    split_idx = trimmed_trailing.rfind(marker)
    if split_idx == -1:
        return len(remainder), len(remainder), ""

    conclusion_candidate = trimmed_trailing[split_idx + len(marker):]
    if not conclusion_candidate.strip():
        return len(remainder), len(remainder), ""

    leading_ws = len(conclusion_candidate) - len(conclusion_candidate.lstrip())
    start = split_idx + len(marker) + leading_ws
    trimmed_conclusion = conclusion_candidate.strip()
    end = start + len(trimmed_conclusion)
    return start, end, trimmed_conclusion


def extract_sections(content: str) -> List[Dict[str, Any]]:
    """Parse body sections with headers, bodies, and offset metadata."""
    if not content:
        return []

    raw_lines, offsets = _lines_with_offsets(content)
    trimmed_lines = [line.rstrip("\r\n") for line in raw_lines]
    header_entries = detect_headers(trimmed_lines)

    sections: List[Dict[str, Any]] = []
    total_length = char_count(content)

    for idx, (line_idx, header_text) in enumerate(header_entries):
        header_start = offsets[line_idx]
        header_end = header_start + len(raw_lines[line_idx])

        body_start_line = line_idx + 1
        next_header_line = (
            header_entries[idx + 1][0] if idx + 1 < len(header_entries) else len(raw_lines)
        )
        if body_start_line < len(offsets):
            body_start = offsets[body_start_line]
        else:
            body_start = header_end
        if next_header_line < len(offsets):
            body_end = offsets[next_header_line]
        else:
            body_end = total_length

        body_text_raw = content[body_start:body_end]
        body_lines = [line.rstrip("\r\n") for line in raw_lines[body_start_line:next_header_line]]

        sections.append(
            {
                "header_line_idx": line_idx,
                "header": header_text,
                "style": detect_style_prefix(header_text),
                "body_lines": body_lines,
                "body_text": body_text_raw.strip(),
                "body_text_raw": body_text_raw,
                "header_offset": header_start,
                "header_end_offset": header_end,
                "body_start_offset": body_start,
                "body_end_offset": body_end,
            }
        )

    return sections


def body_is_bullets(body_text: str) -> bool:
    """True if body consists entirely of bullet lines."""
    if not body_text:
        return False

    lines = [line for line in body_text.strip().splitlines() if line.strip()]
    if not lines:
        return False

    return all(BULLET_REGEX.match(line) for line in lines)


def body_is_paragraph(body_text: str) -> bool:
    """Heuristic paragraph check: 2–6 sentences, <=2 line breaks, no bullets."""
    if not body_text:
        return False

    text = body_text.strip()
    if not text:
        return False

    if any(BULLET_REGEX.match(line) for line in text.splitlines()):
        return False

    if text.count("\n") > 2:
        return False

    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    return 2 <= len(sentences) <= 6


def compute_section_lengths(sections: List[Dict[str, Any]]) -> List[int]:
    """Return char lengths for each section body."""
    return [char_count(section.get("body_text", "")) for section in sections]


def extract_intro_region(full_text_after_hook: str) -> Tuple[str, str]:
    """Return intro segment (up to first header/boundary) and remaining text."""
    if not full_text_after_hook:
        return "", ""

    text = full_text_after_hook
    header_match = HEADER_LINE_PATTERN.search(text)
    header_start = header_match.start() if header_match else len(text)
    candidate = text[:header_start]
    remainder_tail = text[header_start:]

    if not candidate:
        return "", remainder_tail

    desired_min = 200
    desired_max = 400

    cut_idx = min(len(candidate), desired_max)

    # Prefer double newline boundary within range
    for match in re.finditer(r"\n\s*\n", candidate):
        pos = match.start()
        if desired_min <= pos <= desired_max:
            cut_idx = pos
            break

    # If no double newline, consider single newline boundary
    if cut_idx == desired_max:
        for match in re.finditer(r"\n", candidate):
            pos = match.start()
            if desired_min <= pos <= desired_max:
                cut_idx = pos
                break

    intro = candidate[:cut_idx]
    remainder = candidate[cut_idx:] + remainder_tail
    return intro, remainder


def conclusion_region(
    remainder: str, sections: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Return concluding block after final section."""
    start, end, text = _find_conclusion_block(remainder)
    if text:
        return text

    sections = sections or extract_sections(remainder)
    if not sections:
        return remainder.strip()

    tail = remainder[sections[-1]["body_end_offset"] :]
    return tail.strip()


def count_numbers(text: str) -> int:
    """Count numeric tokens for specificity guidance."""
    return len(re.findall(r"\b\d[\d,\.\%]*\b", text))


CTA_PATTERNS = [
    r"\bcomment\b",
    r"\breply\b",
    r"\bshare\b",
    r"\bsave\b",
    r"\bwhat do you think\b",
    r"\bhow do you\b",
    r"\blet me know\b",
    r"\bdm me\b",
    r"\bfollow\b",
    r"\btry (?:this|it)\b",
    r"\buse this\b",
    r"\bsteal this\b",
]


def cta_present(conclusion_text: str) -> bool:
    """Detect CTA phrases within last ~200 characters (questions allowed)."""
    if not conclusion_text:
        return False

    tail = conclusion_text[-200:].lower()
    return any(re.search(pattern, tail, re.IGNORECASE) for pattern in CTA_PATTERNS)


@dataclass
class ParsedLinkedInPost:
    """Structured representation of a LinkedIn post for validation."""

    preview: str
    rest: str
    intro_text: str
    remainder_after_intro: str
    sections: List[Dict[str, Any]]
    conclusion_text: str
    preview_span: Tuple[int, int]
    intro_span: Tuple[int, int]
    conclusion_span: Tuple[int, int]


@lru_cache(maxsize=16)
def parse_linkedin_post(content: str) -> ParsedLinkedInPost:
    """Parse LinkedIn content into structural regions for reuse."""
    preview, rest = split_visible_preview_and_rest(content, 200)
    intro_text, remainder_after_intro = extract_intro_region(rest)

    preview_span = (0, len(preview))
    intro_start = preview_span[1]
    intro_end = intro_start + len(intro_text)
    intro_span = (intro_start, intro_end)

    sections = extract_sections(remainder_after_intro)

    conclusion_start_local, conclusion_end_local, conclusion_text_trimmed = _find_conclusion_block(
        remainder_after_intro
    )

    if sections and conclusion_text_trimmed:
        last_section = sections[-1]
        last_section["body_end_offset"] = min(
            last_section["body_end_offset"], conclusion_start_local
        )
        body_raw = remainder_after_intro[
            last_section["body_start_offset"] : last_section["body_end_offset"]
        ]
        last_section["body_text_raw"] = body_raw
        last_section["body_text"] = body_raw.strip()

    if sections:
        last_body_end_local = sections[-1]["body_end_offset"]
    else:
        last_body_end_local = conclusion_end_local

    if not conclusion_text_trimmed and sections:
        conclusion_local_start = last_body_end_local
        conclusion_local_end = last_body_end_local
    else:
        conclusion_local_start = conclusion_start_local
        conclusion_local_end = conclusion_end_local

    # Adjust offsets to global coordinates
    for section in sections:
        section["header_offset_local"] = section["header_offset"]
        section["header_end_offset_local"] = section["header_end_offset"]
        section["body_start_offset_local"] = section["body_start_offset"]
        section["body_end_offset_local"] = section["body_end_offset"]
        section["header_offset"] += intro_end
        section["header_end_offset"] += intro_end
        section["body_start_offset"] += intro_end
        section["body_end_offset"] += intro_end

    last_body_end_global = intro_end + last_body_end_local
    conclusion_start = intro_end + conclusion_local_start if conclusion_text_trimmed else last_body_end_global
    conclusion_end = intro_end + conclusion_local_end if conclusion_text_trimmed else last_body_end_global
    conclusion_span = (conclusion_start, conclusion_end)

    return ParsedLinkedInPost(
        preview=preview,
        rest=rest,
        intro_text=intro_text,
        remainder_after_intro=remainder_after_intro,
        sections=sections,
        conclusion_text=conclusion_text_trimmed,
        preview_span=preview_span,
        intro_span=intro_span,
        conclusion_span=conclusion_span,
    )


def check_total_char_limit(content: str, limit: int = 2800) -> Optional[Dict[str, Any]]:
    """Ensure total content length stays within platform ceiling."""
    total_chars = char_count(content)
    if total_chars <= limit:
        return None
    return {
        "type": "char_limit_exceeded",
        "severity": "high",
        "auto_fixable": False,
        "message": f"LinkedIn posts must be ≤ {limit} characters (currently {total_chars}).",
        "span": {"start": 0, "end": total_chars},
    }


def check_first_200_hook_and_cliffhanger(content: str) -> List[Dict[str, Any]]:
    """Validate hook presence and cliffhanger in preview region."""
    parsed = parse_linkedin_post(content)
    preview = parsed.preview
    issues: List[Dict[str, Any]] = []

    if not preview.strip():
        issues.append(
            {
                "type": "missing_hook",
                "severity": "high",
                "auto_fixable": False,
                "message": "First 200 characters must deliver a hook—found empty preview.",
                "span": {"start": parsed.preview_span[0], "end": parsed.preview_span[1]},
            }
        )
        return issues

    if not has_cliffhanger(preview):
        issues.append(
            {
                "type": "hook_cliffhanger_missing",
                "severity": "high",
                "auto_fixable": False,
                "message": "First 200 chars must end with a cliffhanger (?, …, :, or mid-sentence).",
                "span": {"start": parsed.preview_span[0], "end": parsed.preview_span[1]},
            }
        )

    return issues


def check_intro_length(content: str) -> Optional[Dict[str, Any]]:
    """Ensure intro block immediately after preview is 200–400 characters."""
    parsed = parse_linkedin_post(content)
    intro_text = parsed.intro_text.strip()
    intro_len = char_count(intro_text)

    if intro_len == 0:
        return {
            "type": "intro_missing",
            "severity": "high",
            "auto_fixable": False,
            "message": "Intro (200–400 chars) required immediately after the hook.",
            "span": {"start": parsed.intro_span[0], "end": parsed.intro_span[1]},
        }

    if not 200 <= intro_len <= 400:
        return {
            "type": "intro_length_out_of_range",
            "severity": "medium",
            "auto_fixable": False,
            "message": "Intro should be 200–400 characters per LinkedIn pacing.",
            "span": {"start": parsed.intro_span[0], "end": parsed.intro_span[1]},
            "observed_length": intro_len,
        }

    return None


def check_headers_sentence_style_and_mirroring(content: str) -> List[Dict[str, Any]]:
    """Validate presence, sentence style, and mirrored numbering across headers."""
    parsed = parse_linkedin_post(content)
    sections = parsed.sections
    issues: List[Dict[str, Any]] = []

    if not sections:
        issues.append(
            {
                "type": "no_headers_found",
                "severity": "high",
                "auto_fixable": False,
                "message": "No sentence-style headers detected (Step/Stat/Mistake/Lesson/Example).",
                "span": {"start": parsed.intro_span[1], "end": parsed.conclusion_span[0]},
            }
        )
        return issues

    styles = set()
    for section in sections:
        header_text = section["header"]
        header_span = {
            "start": section["header_offset"],
            "end": section["header_end_offset"],
        }

        if not is_sentence_style(header_text):
            issues.append(
                {
                    "type": "header_not_sentence_style",
                    "severity": "high",
                    "auto_fixable": False,
                    "message": f"Header must be sentence-style with punctuation: '{header_text}'.",
                    "span": header_span,
                }
            )

        style_prefix = section.get("style")
        if not style_prefix:
            issues.append(
                {
                    "type": "header_missing_style_prefix",
                    "severity": "high",
                    "auto_fixable": False,
                    "message": "Headers must mirror a single style (Step/Stat/Mistake/Lesson/Example).",
                    "span": header_span,
                }
            )
        else:
            styles.add(style_prefix)

    if len(styles) > 1:
        issues.append(
            {
                "type": "mixed_styles_across_headers",
                "severity": "high",
                "auto_fixable": False,
                "message": "All headers must use the same style prefix (e.g., all 'Step N …').",
                "span": {
                    "start": sections[0]["header_offset"],
                    "end": sections[-1]["header_end_offset"],
                },
            }
        )

    return issues


def check_alternation_rule(content: str) -> Optional[Dict[str, Any]]:
    """Enforce bullets/paragraph alternation across sections."""
    parsed = parse_linkedin_post(content)
    sections = parsed.sections

    for idx, section in enumerate(sections, start=1):
        body_text = section.get("body_text", "")
        body_span = {
            "start": section["body_start_offset"],
            "end": section["body_end_offset"],
        }

        if idx % 2 == 1:
            if not body_is_bullets(body_text):
                return {
                    "type": "alternation_expected_bullets",
                    "severity": "high",
                    "auto_fixable": False,
                    "message": f"Section {idx} body must be formatted as bullets.",
                    "section_index": idx,
                    "span": body_span,
                }
        else:
            if not body_is_paragraph(body_text):
                return {
                    "type": "alternation_expected_paragraph",
                    "severity": "high",
                    "auto_fixable": False,
                    "message": f"Section {idx} body must be a paragraph block.",
                    "section_index": idx,
                    "span": body_span,
                }

    return None


def check_section_lengths(content: str) -> List[Dict[str, Any]]:
    """Validate section body char lengths stay within 300–450."""
    parsed = parse_linkedin_post(content)
    sections = parsed.sections
    issues: List[Dict[str, Any]] = []

    for idx, section in enumerate(sections, start=1):
        body_text = section.get("body_text", "").strip()
        section_length = char_count(body_text)
        if not 300 <= section_length <= 450:
            issues.append(
                {
                    "type": "section_length_out_of_range",
                    "severity": "medium",
                    "auto_fixable": False,
                    "message": f"Section {idx} is {section_length} chars; target 300–450.",
                    "section_index": idx,
                    "span": {
                        "start": section["body_start_offset"],
                        "end": section["body_end_offset"],
                    },
                    "observed_length": section_length,
                }
            )

    return issues


def check_conclusion_and_cta(content: str) -> List[Dict[str, Any]]:
    """Ensure conclusion length and CTA compliance."""
    parsed = parse_linkedin_post(content)
    conclusion_text = parsed.conclusion_text.strip()
    issues: List[Dict[str, Any]] = []

    conclusion_len = char_count(conclusion_text)
    if conclusion_len == 0:
        issues.append(
            {
                "type": "conclusion_missing",
                "severity": "high",
                "auto_fixable": False,
                "message": "Conclusion (100–200 chars) with CTA required.",
                "span": {
                    "start": parsed.conclusion_span[0],
                    "end": parsed.conclusion_span[1],
                },
            }
        )
    else:
        if not 100 <= conclusion_len <= 200:
            issues.append(
                {
                    "type": "conclusion_length_out_of_range",
                    "severity": "medium",
                    "auto_fixable": False,
                    "message": "Conclusion should be 100–200 characters to prompt action.",
                    "span": {
                        "start": parsed.conclusion_span[0],
                        "end": parsed.conclusion_span[1],
                    },
                    "observed_length": conclusion_len,
                }
            )

        if not cta_present(conclusion_text):
            issues.append(
                {
                    "type": "missing_cta",
                    "severity": "medium",
                    "auto_fixable": False,
                    "message": "Include a CTA in the conclusion (questions allowed).",
                    "span": {
                        "start": parsed.conclusion_span[0],
                        "end": parsed.conclusion_span[1],
                    },
                }
            )

    return issues


def check_specific_numbers(content: str, min_numbers: int = 1) -> Optional[Dict[str, Any]]:
    """Soft-check for recommended numeric specificity."""
    total_numbers = count_numbers(content)
    if total_numbers >= min_numbers:
        return None
    return {
        "type": "no_numbers_found",
        "severity": "low",
        "auto_fixable": False,
        "message": "Add 2–4 concrete numbers or proof points for credibility.",
        "numbers_found": total_numbers,
    }


def check_contrast_patterns(content: str) -> List[Dict[str, Any]]:
    """Check for AI contrast patterns (not X but Y)."""
    issues = []

    # Direct contrast patterns (high severity)
    direct_patterns = [
        r"(?:isn't|is not|wasn't|was not)\s+about\s+\w+[,—;]\s*(?:it's|it is|but|rather)",
        r"(?:it's|it is)\s+not\s+\w+[,]\s*(?:it's|it is)",
        r"(?:the\s+)?(?:problem|issue)\s+(?:isn't|is not)\s+\w+[,—]\s*(?:it's|it is)",
        r"(?:aren't|are not|isn't|is not)\s+just\s+\w+[,—]\s*(?:they're|it's|we're)",  # "aren't just X—they're Y"
        r"(?:not|n't)\s+just\s+\w+[,—]\s*(?:but|it's|they're|we're)",  # "not just X, but Y"
    ]

    for pattern in direct_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            issues.append({
                "code": "contrast_direct",
                "severity": "high",
                "auto_fixable": False,
                "message": f"Direct contrast pattern detected: '{match.group()}' - Replace with direct positive assertion",
                "span": (match.start(), match.end())
            })

    # Masked contrast patterns (high severity)
    masked_patterns = [
        r"\brather than\b",
        r"\binstead of\b",
        r"\bas opposed to\b",
        r"\bbut rather\b",
    ]

    for pattern in masked_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Check if it's part of a spaced reframe (3+ sentences between negative and positive)
            # Simple heuristic: look for 2+ sentence breaks around the match
            context_start = max(0, match.start() - 300)
            context_end = min(len(content), match.end() + 300)
            context = content[context_start:context_end]
            sentence_breaks = len(re.findall(r'[.!?]\s+', context))

            if sentence_breaks < 4:  # Not enough spacing for acceptable contrast
                issues.append({
                    "code": "contrast_masked",
                    "severity": "high",
                    "auto_fixable": False,
                    "message": f"Masked contrast pattern: '{match.group()}' - Replace with positive assertion or add 2-3 sentences of expansion",
                    "span": (match.start(), match.end())
                })

    return issues


class LinkedInValidator(BaseValidator):
    """Deterministic validator for LinkedIn long-form framework."""

    def validate(self, content: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        # Reset parse cache for fresh content evaluation
        parse_linkedin_post.cache_clear()

        issues.extend(ForbiddenPatterns.check_content(content))

        char_limit_issue = check_total_char_limit(content)
        if char_limit_issue:
            issues.append(char_limit_issue)

        issues.extend(check_first_200_hook_and_cliffhanger(content))

        intro_issue = check_intro_length(content)
        if intro_issue:
            issues.append(intro_issue)

        header_issues = check_headers_sentence_style_and_mirroring(content)
        issues.extend(header_issues)

        alternation_issue = check_alternation_rule(content)
        if alternation_issue:
            issues.append(alternation_issue)

        issues.extend(check_section_lengths(content))

        issues.extend(check_conclusion_and_cta(content))

        numbers_issue = check_specific_numbers(content, min_numbers=1)
        if numbers_issue:
            issues.append(numbers_issue)

        # Check for AI contrast patterns
        issues.extend(check_contrast_patterns(content))

        # Ensure parse cache flushed post-validation to avoid stale state
        parse_linkedin_post.cache_clear()

        return issues

    def get_grading_rubric(self) -> str:
        return """
LINKEDIN GRADING RUBRIC (0–100)

Hook & First 200 (25)
- Clear hook in first 200 chars; questions allowed
- Cliffhanger at ~200 chars prompting “See more”
- Feeds LinkedIn preview well (value-forward, mobile-first)

Structure & Formatting (20)
- Headers are sentence-style, numbered by the chosen style
- Style mirroring across all headers (Steps/Stats/Mistakes/Lessons/Examples)
- Strict alternation: bullets → paragraph → bullets → …
- Section lengths respected (300–450 chars), intro 200–400, conclusion 100–200
- Total ≤ 2,800 chars

Content Value & Style Execution (25)
- Chosen style is consistently executed
- Tactically dense (3–5 concrete tips/data points per section)
- Industry relevance and professional credibility

Authenticity & AI Artifacts (20)
- Avoids contrast clichés (“Not X, but Y”)
- Avoids generic AI filler and rhythmic patterns
- Natural voice and personal proof points

Engagement & CTA (10)
- Clear next step or discussion prompt (questions allowed)
- Share/save-worthiness and evergreen value
"""

    def get_writing_rules(self) -> str:
        return """
LINKEDIN WRITING RULES

Structure
1) Hook (≤200 chars, questions allowed) ending with a cliffhanger
2) Intro (200–400 chars) using our 4-block sell-the-reader format
3) Sections (3–10): sentence-style headers with style mirroring; bodies alternate bullets/paragraphs
4) Conclusion (100–200 chars) with a CTA (questions allowed)

Mandatory
- ≤ 2,800 total characters
- Sentence-style headers with punctuation
- Strict alternation bullets/paragraphs across sections
- CTA present in the closing block

Recommended
- 2–4 specific numbers or proof points across the post
- Short paragraphs for mobile readability

Forbidden
- Contrast clichés (“not X, but Y” patterns)
- Corporate jargon and vague claims
"""

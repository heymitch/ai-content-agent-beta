"""
Hybrid Editor: Combines LLM rewrites with regex auto-fixes
Efficiently fixes validation issues in multiple passes
"""
from anthropic import Anthropic
import os
import re
from typing import List, Dict, Tuple


class HybridEditor:
    """Intelligent editor that fixes issues with LLM or regex based on type"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def fix_issues(self, draft: str, issues: List[Dict], context: str = "") -> str:
        """
        Fix validation issues using hybrid approach

        Args:
            draft: Current draft text
            issues: List of issues from validator
            context: Original brief/context

        Returns:
            Fixed draft
        """
        # Debug: Show what issues we received
        if issues:
            issue_codes = [i.get('code', 'unknown') for i in issues]
            print(f"📋 Editor received {len(issues)} issues with codes: {issue_codes[:5]}...")  # Show first 5

        # Separate issues by fixability
        regex_fixable = self._get_regex_fixable_issues(issues)
        llm_needed = self._get_llm_needed_issues(issues)

        print(f"🔧 Hybrid Editor: {len(regex_fixable)} regex fixes, {len(llm_needed)} LLM fixes")

        # Step 1: Auto-fix with regex (fast, deterministic)
        if regex_fixable:
            draft = self._apply_regex_fixes(draft, regex_fixable)
            print(f"✅ Applied {len(regex_fixable)} regex fixes")

        # Step 2: LLM rewrite for strategic issues (slower, creative)
        if llm_needed:
            draft = self._apply_llm_fixes(draft, llm_needed, context)
            print(f"✅ Applied {len(llm_needed)} LLM fixes")

        return draft

    def _get_regex_fixable_issues(self, issues: List[Dict]) -> List[Dict]:
        """Identify issues that can be auto-fixed with regex"""
        regex_codes = [
            'contrast_direct',  # "not X but Y" patterns
            'contrast_masked',  # "rather than", "instead of"
            'wall_of_text',     # Dense paragraphs
            'paragraph_dense',  # Too many sentences
        ]
        return [i for i in issues if i.get('code') in regex_codes]

    def _get_llm_needed_issues(self, issues: List[Dict]) -> List[Dict]:
        """Identify issues that need LLM rewriting"""
        llm_codes = [
            'hook_generic',      # Hook doesn't use framework
            'hook_vague',        # Hook lacks specifics
            'header_generic',    # Generic headers
            'header_vague',      # Vague headers
            'audience_generic',  # Broad audience
            'no_numbers_found',  # Missing metrics
            'cta_passive',       # Weak CTA
            'bucket_unclear',    # Content bucket unclear
        ]
        return [i for i in issues if i.get('code') in llm_codes]

    def _apply_regex_fixes(self, draft: str, issues: List[Dict]) -> str:
        """Auto-fix issues with regex patterns"""

        for issue in issues:
            # Skip if no 'code' field (might be LLM-generated issue)
            if 'code' not in issue:
                continue

            if issue['code'] == 'contrast_direct':
                # Remove "not X but Y" patterns
                draft = self._fix_direct_contrast(draft)

            elif issue['code'] == 'contrast_masked':
                # Remove "rather than", "instead of"
                draft = self._fix_masked_contrast(draft)

            elif issue['code'] in ['wall_of_text', 'paragraph_dense']:
                # Add line breaks
                draft = self._add_line_breaks(draft)

        return draft

    def _fix_direct_contrast(self, text: str) -> str:
        """Remove direct contrast patterns (not X but Y)"""

        # Pattern: "It's not X, it's Y" -> "It's Y"
        text = re.sub(
            r"It'?s not (about )?([^,;—]+?)[,;—] it'?s (about )?",
            r"It's ",
            text,
            flags=re.IGNORECASE
        )

        # Pattern: "This isn't about X—it's about Y" -> "This is about Y"
        text = re.sub(
            r"This isn'?t (about )?([^—]+?)—it'?s (about )?",
            r"This is ",
            text,
            flags=re.IGNORECASE
        )

        # Pattern: "The problem isn't X, it's Y" -> "The problem is Y"
        text = re.sub(
            r"The (problem|issue) isn'?t ([^,;—]+?)[,;—] it'?s",
            r"The \1 is",
            text,
            flags=re.IGNORECASE
        )

        # Pattern: "Not just X—they're Y" -> "They're Y"
        text = re.sub(
            r"Not just ([^—]+?)—they'?re",
            r"They're",
            text,
            flags=re.IGNORECASE
        )

        return text

    def _fix_masked_contrast(self, text: str) -> str:
        """Remove masked contrast patterns (rather than, instead of)"""

        # Pattern: "Rather than X, focus on Y" -> "Focus on Y"
        text = re.sub(
            r"Rather than ([^,]+?), ",
            r"",
            text,
            flags=re.IGNORECASE
        )

        # Pattern: "Instead of X, consider Y" -> "Consider Y"
        text = re.sub(
            r"Instead of ([^,]+?), ",
            r"",
            text,
            flags=re.IGNORECASE
        )

        return text

    def _add_line_breaks(self, text: str) -> str:
        """Add line breaks to dense paragraphs"""

        # Split dense blocks (>4 sentences) into shorter paragraphs
        paragraphs = text.split('\n\n')
        fixed_paragraphs = []

        for para in paragraphs:
            # Count sentences
            sentences = re.split(r'[.!?]\s+', para)

            if len(sentences) > 3:
                # Break into 2-sentence chunks
                chunks = []
                for i in range(0, len(sentences), 2):
                    chunk = '. '.join(sentences[i:i+2])
                    if not chunk.endswith('.'):
                        chunk += '.'
                    chunks.append(chunk)
                fixed_paragraphs.append('\n\n'.join(chunks))
            else:
                fixed_paragraphs.append(para)

        return '\n\n'.join(fixed_paragraphs)

    def _apply_llm_fixes(self, draft: str, issues: List[Dict], context: str) -> str:
        """Use LLM to fix strategic issues"""

        # Build fix instructions
        fix_instructions = []
        for issue in issues:
            fix_instructions.append(
                f"- **{issue.get('code', 'unknown')}** (severity: {issue.get('severity', 'medium')}): {issue.get('message', 'No description')}\n  Fix: {issue.get('fix_hint', 'Consider revising')}"
            )

        # Static system instructions (cacheable)
        system_instructions = """You are a LinkedIn content editor. Your job is to fix the strategic issues in this draft while keeping the good parts intact.

Your task:
1. Fix ONLY the specific issues listed above
2. Keep everything else unchanged
3. Maintain the overall structure and flow
4. Make minimal changes - surgical edits only
5. Return the FULL revised draft

CRITICAL RULES:
- If fixing headers, make them specific with metrics/outcomes/actions
- If fixing audience, target role + stage + problem (e.g., "seed-stage SaaS founders stuck at $1M ARR")
- If adding numbers, be specific (not "significant" but "41 to 23 days")
- If fixing CTA, make it an engagement trigger (question, request, comment bait)
- If fixing hook, use one of the 5 frameworks (question, bold statement, stat, story, mistake)

Return ONLY the revised draft. No preamble, no explanation."""

        # Dynamic user content
        user_prompt = f"""ORIGINAL CONTEXT:
{context}

CURRENT DRAFT:
{draft}

ISSUES TO FIX:
{chr(10).join(fix_instructions)}

Fix the draft now."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=[
                    {
                        "type": "text",
                        "text": system_instructions,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )

            revised_draft = response.content[0].text.strip()
            return revised_draft

        except Exception as e:
            print(f"❌ LLM fix error: {e}")
            return draft  # Return unchanged if LLM fails


# Convenience function
def fix_draft(draft: str, issues: List[Dict], context: str = "") -> str:
    """Fix draft using hybrid editor"""
    editor = HybridEditor()
    return editor.fix_issues(draft, issues, context)

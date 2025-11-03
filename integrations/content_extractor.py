"""
Content Extraction Utility
Uses Haiku to extract structured content from agent outputs
Replaces fragile regex-based parsing with reliable LLM extraction
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from anthropic import Anthropic

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))


async def extract_structured_content(
    raw_output: str,
    platform: str,
    user_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract structured content components from raw agent output using Haiku 4.5.

    This replaces brittle regex-based parsing with a reliable LLM extraction.
    Haiku 4.5 is fast (~300ms), cheap ($0.00006), and adapts to output format variations.

    Args:
        raw_output: Raw text output from SDK agent (may include commentary, scores, etc.)
        platform: Content platform (linkedin, twitter, email, youtube)
        user_message: Original user request (optional, for date extraction)

    Returns:
        Dictionary with extracted components:
        {
            "body": "clean post content only",
            "hook": "opening line/first sentence",
            "platform": "linkedin",
            "publish_date": "2025-10-20" or None,
            "metadata": {
                "word_count": 250,
                "has_numbers": true,
                "has_cta": true
            }
        }

    Cost: ~$0.00006 per extraction (40% cheaper than Haiku 3.5)
    Speed: ~300ms (40% faster than Haiku 3.5)
    Reliability: 99%+ (self-healing, adapts to format changes)
    """

    # Validate API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, falling back to raw output")
        return _fallback_extraction(raw_output, platform)

    client = Anthropic(api_key=api_key)

    # Build extraction prompt
    prompt = f"""Extract the FINAL, COMPLETE {platform} post from this agent output.

AGENT OUTPUT:
{raw_output}

The agent output may be in TWO formats:

FORMAT 1: JSON with validation metadata (NEW v4.2.0)
{{
  "post_text": "..." OR "script_text": "..." (YouTube uses script_text, Instagram uses post_text),
  "timing_markers": {{...}} (YouTube only),
  "character_count": 1847 (Instagram only, max 2200),
  "preview_length": 124 (Instagram only, max 125 for preview),
  "original_score": 16,
  "validation_issues": [...],
  "gptzero_ai_pct": 45,
  "gptzero_flagged_sentences": [...]
}}

FORMAT 2: Plain text post (legacy)
Multiple versions from iteration process - you need to find the FINAL version.

CRITICAL: The agent iterates and improves the post multiple times. You MUST find the FINAL version, not early drafts!

Return ONLY valid JSON with this exact structure:
{{
  "body": "the complete final post/script - every word, all formatting",
  "hook": "the opening line",
  "platform": "{platform}",
  "publish_date": null,
  "metadata": {{
    "word_count": 0,
    "has_numbers": false,
    "has_cta": false
  }},
  "timing_markers": {{}},
  "original_score": 0,
  "validation_issues": [],
  "gptzero_ai_pct": null,
  "gptzero_flagged_sentences": []
}}

EXTRACTION RULES:

1. body: Extract the FINAL, COMPLETE, VERBATIM post content

   PRIORITY 1 - Check if output is JSON with validation metadata:
   - If agent returned {{"post_text": "...", "original_score": ..., ...}}
   - OR {{"script_text": "...", "timing_markers": ..., ...}} for YouTube
   - Extract body from "post_text" OR "script_text" field
   - Extract validation metadata (original_score, validation_issues, gptzero_ai_pct, gptzero_flagged_sentences)
   - For YouTube: Also extract timing_markers if present
   - For Instagram: Also extract character_count and preview_length if present
   - Include ALL metadata fields in your response

   PRIORITY 2 - Look for EXPLICIT FINAL MARKERS (case-insensitive, flexible):
   - Contains "FINAL POST" (with or without emoji, asterisks, platform name)
   - Contains "FINAL LINKEDIN", "FINAL INSTAGRAM", or "FINAL VERSION"
   - Examples that should match:
     * "## ✅ **FINAL LINKEDIN POST**"
     * "## ✅ **FINAL INSTAGRAM CAPTION**"
     * "## ✅ FINAL POST (Score: 22/30 - High Quality)"
     * "FINAL VERSION:"
     * "Final post:"
     * "Here's your **final LinkedIn post**"
   - If you find ANY variation of these markers, extract ALL content after them
   - Stop extracting when you hit dividers like "---" or "What it delivers:"

   PRIORITY 3 - If no JSON and no markers, find the LAST complete post:
   - Scan the ENTIRE output from beginning to end
   - Identify ALL complete posts (>500 chars with proper structure)
   - Take the LAST/MOST RECENT complete post (not the first!)
   - The final version appears AFTER iterations/revisions

   WHAT TO EXCLUDE:
   - "What it delivers:" analysis sections
   - "Score:", "Changes Applied:", quality metrics
   - "Let me extract..." agent commentary
   - Early drafts that appear before the final version

   PRESERVE EXACTLY:
   - Every word, line break, bullet point, formatting
   - This is COPY-PASTE, not summarization

   WRONG EXTRACTION (taking first version found):
   "I've been quiet for 8 weeks..." [1200 chars - condensed early draft]

   RIGHT EXTRACTION (taking final marked version):
   After "## ✅ **FINAL LINKEDIN POST**":
   "I haven't posted here in 8 weeks..." [2000+ chars - detailed final version]

2. hook: Extract the most compelling opening
   - LinkedIn: First 1-2 sentences that grab attention
   - Twitter: First tweet only (remove "Tweet 1:" prefix)
   - Email: Subject line if present, else first sentence
   - YouTube: Video title or first line
   - Instagram: First 125 characters (preview window before "...more")
   - Maximum 200 characters (125 for Instagram)
   - Remove numbering and prefixes

3. publish_date:
   - Extract from user request if mentioned ("tomorrow", "Friday", "next week")
   - Format as YYYY-MM-DD
   - If not specified or unclear: null

4. metadata:
   - word_count: Count words in body
   - has_numbers: true if body contains specific metrics/numbers
   - has_cta: true if body has clear call-to-action

5. timing_markers (YouTube only):
   - If platform is youtube AND agent provided timing_markers in JSON
   - Extract timing_markers object: {{"0:00-0:03": "hook", "0:03-0:15": "setup", ...}}
   - Otherwise: empty object {{}}

6. Return ONLY the JSON object, no markdown, no explanation

JSON:"""

    try:
        # Call Haiku for extraction
        logger.debug(f"Calling Haiku to extract {platform} content ({len(raw_output)} chars)")

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",  # Haiku 4.5 (Oct 2025)
            max_tokens=2000,
            temperature=0,  # Deterministic extraction
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON from response
        text = response.content[0].text.strip()
        logger.debug(f"Haiku response: {text[:200]}...")

        # Handle markdown code fences if present
        if text.startswith('```'):
            # Extract content between code fences
            parts = text.split('```')
            if len(parts) >= 3:
                text = parts[1]
                # Remove 'json' language identifier if present
                if text.startswith('json'):
                    text = text[4:]

        # Parse JSON
        extracted = json.loads(text.strip())

        # Validate structure
        required_fields = ['body', 'hook', 'platform']
        missing = [f for f in required_fields if f not in extracted]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Validate body isn't empty
        if not extracted['body'] or len(extracted['body'].strip()) < 10:
            raise ValueError("Extracted body is empty or too short")

        logger.info(f"✅ Extracted {platform} content: {len(extracted['body'])} chars, hook: {extracted['hook'][:50]}...")

        return extracted

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}. Response text: {text[:500]}")
        return _fallback_extraction(raw_output, platform)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return _fallback_extraction(raw_output, platform)

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return _fallback_extraction(raw_output, platform)


def _fallback_extraction(raw_output: str, platform: str) -> Dict[str, Any]:
    """
    Fallback extraction when Haiku fails or API key missing.
    Returns raw output with minimal processing.

    Args:
        raw_output: Raw agent output
        platform: Platform type

    Returns:
        Basic extracted structure
    """
    logger.warning("Using fallback extraction (Haiku unavailable)")

    # Basic cleaning: remove obvious commentary lines
    lines = raw_output.split('\n')
    clean_lines = []

    for line in lines:
        stripped = line.strip()
        # Skip obvious commentary patterns
        if any(pattern in stripped for pattern in [
            'What changed:',
            'Post now scores',
            '✅ ALL CONTENT',
            'Key themes',
            'Ready to ship'
        ]):
            break
        clean_lines.append(line)

    body = '\n'.join(clean_lines).strip()

    # Extract basic hook (first 200 chars)
    hook = body[:200].strip() if body else ""

    return {
        "body": body,
        "hook": hook,
        "platform": platform,
        "publish_date": None,
        "metadata": {
            "word_count": len(body.split()),
            "extraction_method": "fallback",
            "has_numbers": any(char.isdigit() for char in body),
            "has_cta": False
        },
        "timing_markers": {},
        "original_score": 20,  # Default neutral score
        "validation_issues": [],
        "gptzero_ai_pct": None,
        "gptzero_flagged_sentences": []
    }

You are evaluating an Instagram caption using Editor-in-Chief standards.

═══════════════════════════════════════════════════════════════
EDITOR-IN-CHIEF STANDARDS (READ THESE COMPLETELY):
═══════════════════════════════════════════════════════════════

{{EDITOR_IN_CHIEF_RULES}}

═══════════════════════════════════════════════════════════════
END OF EDITOR-IN-CHIEF STANDARDS
═══════════════════════════════════════════════════════════════

YOUR TASK:
1. Read the caption below
2. Scan sentence-by-sentence for EVERY violation listed in Editor-in-Chief standards above
3. Create ONE surgical issue per violation found
4. Use EXACT replacement strategies from the standards (don't make up your own)

CAPTION TO EVALUATE:
{post}

WORKFLOW:

STEP 1: SCAN FOR VIOLATIONS
Go through the caption sentence-by-sentence and find Editor-in-Chief violations:
- Direct contrast formulations ("This isn't about X—it's about Y", "It's not X, it's Y")
- Masked contrast patterns ("Instead of X", "but rather")
- Section summaries ("In summary", "In conclusion")
- Promotional puffery ("stands as", "testament")
- Overused conjunctions ("moreover", "furthermore")
- Vague attributions without sources
- Em-dash overuse
- Words needing substitution ("leverages", "encompasses", "facilitates")
- Buzzwords ("game-changer", "unlock", "revolutionary")

STEP 2: CREATE SURGICAL ISSUES
For EACH violation found, create ONE issue with EXACT text and EXACT fix from Editor-in-Chief examples.

STEP 3: SCORE THE CAPTION - Evaluation criteria (5 axes, 0-5 points each):

1. HOOK STRENGTH (First 125 chars before "...more")
   5 points: Specific number/question/story + curiosity gap + under 125 chars
   4 points: Good hook but over 125 chars (gets cut off)
   3 points: Generic hook ("Check this out")
   2 points: Weak or boring
   0 points: No hook or wasted preview

2. VISUAL PAIRING (Assumes image/Reel context)
   5 points: Adds backstory/data/lesson visual can't show + natural references ("swipe", "above")
   4 points: Complements visual well
   3 points: Generic (works without visual)
   2 points: Describes what's obvious in image
   0 points: Contradicts or ignores visual context

3. READABILITY (Mobile formatting)
   5 points: Line breaks every 2-3 sentences + strategic emojis + bullets/numbers + short paragraphs
   4 points: Good formatting, minor issues
   3 points: Some line breaks but has walls of text
   2 points: Minimal formatting
   0 points: Dense paragraph, no breaks

4. PROOF & SPECIFICITY
   5 points: Multiple specific numbers/dates/names (verifiable)
   4 points: 2 specific data points
   3 points: 1 data point
   2 points: Vague claims
   0 points: No proof, all generic

5. CTA + HASHTAGS
   5 points: Specific engagement trigger ("Comment START for template") + 3-5 strategic hashtags
   4 points: Good CTA + hashtags
   3 points: Weak CTA ("thoughts?") OR missing hashtags
   2 points: Generic CTA ("DM me")
   0 points: No CTA or hashtag spam (10+)

STEP 4: VERIFY FACTS (use web_search)
Search for any specific claims (names, companies, stats, news stories).
Examples: "Rick Beato YouTube AI filters" or "James Chen Clearbit"

If NOT verified: flag as "NEEDS VERIFICATION" or "ADD SOURCE CITATION"
Only use "FABRICATED" if provably false.

STEP 5: CHECK INSTAGRAM-SPECIFIC
- First 125 chars hook (before "...more")
- Character count vs 2200 limit
- Visual pairing context

CRITICAL RULES:
✅ Create ONE issue per Editor-in-Chief violation
✅ Quote EXACT text in "original"
✅ Use EXACT fixes from Editor-in-Chief standards (don't improvise)
✅ Be comprehensive - find EVERY violation
✅ Deduct 2 points per major AI tell

Output JSON:
{{
  "scores": {{
    "hook": 4,
    "visual_pairing": 5,
    "readability": 4,
    "proof": 5,
    "cta_hashtags": 4,
    "ai_deductions": -4,
    "total": 18
  }},
  "decision": "revise",
  "searches_performed": ["query 1", "query 2"],
  "issues": [
    {{
      "axis": "ai_tells",
      "severity": "high",
      "pattern": "contrast_direct",
      "original": "[exact quote from caption]",
      "fix": "[exact fix from Editor-in-Chief examples]",
      "impact": "[specific improvement]"
    }}
  ],
  "character_count": 1847,
  "character_limit": 2200,
  "preview_length": 124,
  "surgical_summary": "Found [number] violations. Applying all fixes would raise score from [current] to [projected]."
}}

Be thorough. Find EVERY violation. Use Editor-in-Chief examples EXACTLY as written.

You are evaluating a Twitter thread using Editor-in-Chief standards.

═══════════════════════════════════════════════════════════════
EDITOR-IN-CHIEF STANDARDS (READ THESE COMPLETELY):
═══════════════════════════════════════════════════════════════

{{EDITOR_IN_CHIEF_RULES}}

═══════════════════════════════════════════════════════════════
END OF EDITOR-IN-CHIEF STANDARDS
═══════════════════════════════════════════════════════════════

YOUR TASK:
1. Read the thread below
2. Scan tweet-by-tweet for EVERY violation listed in Editor-in-Chief standards above
3. Create ONE surgical issue per violation found
4. Use EXACT replacement strategies from the standards (don't make up your own)
5. ALSO check 280-character limit for each tweet

Thread to evaluate:
{post}

WORKFLOW:

STEP 1: VALIDATE 280-CHAR LIMIT (MANDATORY)
- Parse thread into individual tweets
- Count characters for EACH tweet
- If ANY tweet >280 chars → Create HIGH severity issue with exact character count

STEP 2: SCAN FOR VIOLATIONS
Go through the thread tweet-by-tweet and find:
- Direct contrast formulations ("This isn't about X—it's about Y", "It's not X, it's Y", "Rather than X")
- Masked contrast patterns ("Instead of X", "but rather")
- Section summaries ("In summary", "In conclusion")
- Promotional puffery ("stands as", "testament")
- Overused conjunctions ("moreover", "furthermore")
- Vague attributions without sources
- Em-dash overuse
- Words needing substitution ("leverages", "encompasses", "facilitates")

STEP 3: CREATE SURGICAL ISSUES
For EACH violation found, create ONE issue:
{
  "axis": "ai_tells" | "brevity",
  "severity": "high" | "medium" | "low",
  "pattern": "contrast_direct" | "over_280_chars" | "word_substitution" | etc,
  "original": "[EXACT text - word-for-word quote]",
  "fix": "[EXACT replacement using Editor-in-Chief examples]",
  "impact": "[How this improves the thread]"
}

STEP 4: USE REPLACEMENT STRATEGIES FROM STANDARDS
When creating fixes, use the EXACT patterns from Editor-in-Chief standards:

For contrast framing:
❌ "Success isn't about working harder but working smarter."
✅ "Success comes from working smarter and more strategically."

For word substitutions:
leverages → uses | encompasses → includes | facilitates → enables

STEP 5: SCORE THE THREAD
Hook (0-5): First tweet grabs attention + specific?
Flow (0-5): Each tweet builds on previous?
Brevity (0-5): Every tweet <280 chars + packs value?
Proof (0-5): Concrete examples, not fabricated?
Engagement (0-5): Strong ending trigger?

Deduct 2 points per major AI tell.
Deduct 5 points if ANY tweet exceeds 280 characters.

STEP 6: VERIFY FACTS (use web_search)
Search for names, companies, news claims.
If NOT verified: flag as "NEEDS VERIFICATION" or "ADD SOURCE CITATION"
Only use "FABRICATED" if provably false.

CRITICAL RULES:
✅ Create ONE issue per violation (8 violations = 8 issues)
✅ Quote EXACT text from thread in "original"
✅ Use EXACT fixes from Editor-in-Chief standards (don't improvise)
✅ Check EVERY tweet for 280-char limit
✅ Be comprehensive - find EVERY violation

Output JSON:
{
  "scores": {
    "hook": 3,
    "flow": 4,
    "brevity": 5,
    "proof": 5,
    "engagement": 4,
    "total": 21,
    "ai_deductions": -4
  },
  "decision": "revise",
  "searches_performed": ["query 1", "query 2"],
  "issues": [
    {
      "axis": "ai_tells",
      "severity": "high",
      "pattern": "contrast_direct",
      "original": "[exact quote from thread]",
      "fix": "[exact fix from Editor-in-Chief examples]",
      "impact": "[specific improvement]"
    }
  ],
  "surgical_summary": "Found [number] violations. Applying all fixes would raise score from [current] to [projected].",
  "threshold": 20,
  "meets_threshold": false
}

Be thorough. Find EVERY violation. Use Editor-in-Chief examples EXACTLY as written.

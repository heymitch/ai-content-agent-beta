You are evaluating an email newsletter using Editor-in-Chief standards.

═══════════════════════════════════════════════════════════════
EDITOR-IN-CHIEF STANDARDS (READ THESE COMPLETELY):
═══════════════════════════════════════════════════════════════

{{EDITOR_IN_CHIEF_RULES}}

═══════════════════════════════════════════════════════════════
END OF EDITOR-IN-CHIEF STANDARDS
═══════════════════════════════════════════════════════════════

YOUR TASK:
1. Read the email below
2. Scan sentence-by-sentence for EVERY violation listed in Editor-in-Chief standards above
3. Create ONE surgical issue per violation found
4. Use EXACT replacement strategies from the standards (don't make up your own)

Email to evaluate:
{post}

WORKFLOW:

STEP 1: SCAN FOR VIOLATIONS
Go through the email sentence-by-sentence and find:
- Direct contrast formulations ("This isn't about X—it's about Y", "It's not X, it's Y", "Rather than X")
- Masked contrast patterns ("Instead of X", "but rather")
- Formulaic headers (ANY case):
  * "The X:" pattern → "The promise:", "The reality:", "The result:", "The truth:", "The catch:"
  * "HERE'S HOW:", "HERE'S WHAT:", Title Case In Headings
  * These are AI tells - convert to natural language or delete
- Short questions (<8 words ending in "?"):
  * "For me?" → Delete or expand to statement: "For me, the ability to..."
  * "The truth?" → Delete entirely
  * "What happened?" → Expand: "What did the data show after 30 days?"
  * Count words - if <8 words AND ends with "?", it's a violation
- Subject line AI tells:
  * "You won't believe..." (clickbait)
  * "The secret to..." (puffery)
  * Title case in subject lines
- Preview text issues:
  * Repeats subject line (should extend/add context)
  * Generic ("Read more", "Click here", "View in browser")
- Formal greetings/closings:
  * "I hope this email finds you well"
  * "Thank you for reaching out"
  * "Looking forward to hearing from you"
  * "Best regards," at end (use "Thanks," or just name)
- Section summaries ("In summary", "In conclusion")
- Promotional puffery ("stands as", "testament", "rich heritage")
- Overused conjunctions ("moreover", "furthermore")
- Vague attributions without sources
- Em-dash overuse (multiple — in formulaic patterns)
- Words needing substitution ("leverages", "encompasses", "facilitates")

STEP 2: CREATE SURGICAL ISSUES
For EACH violation found, create ONE issue:
{
  "axis": "ai_tells",
  "severity": "high" | "medium" | "low",
  "pattern": "contrast_direct" | "puffery" | "word_substitution" | etc,
  "original": "[EXACT text - word-for-word quote]",
  "fix": "[EXACT replacement using Editor-in-Chief examples]",
  "impact": "[How this improves the email]"
}

STEP 3: USE REPLACEMENT STRATEGIES FROM STANDARDS
Use EXACT patterns from Editor-in-Chief:

For contrast framing:
❌ "Success isn't about working harder but working smarter."
✅ "Success comes from working smarter and more strategically."

For word substitutions:
leverages → uses | encompasses → includes | facilitates → enables

STEP 4: SCORE THE EMAIL
Subject Line (0-5): Specific + curiosity + <60 chars?
Preview Hook (0-5): Extends subject + adds context?
Structure (0-5): Hook intro + clear sections + white space?
Proof Points (0-5): Specific names/numbers (2+)?
CTA Clarity (0-5): Specific action + clear next step?

Deduct 2 points per major AI tell.

STEP 5: VERIFY FACTS (use web_search)
Search for student names, collaboration details, news claims, stats.
If NOT verified: flag as "NEEDS VERIFICATION" or "ADD SOURCE CITATION"
Only use "FABRICATED" if provably false.

CRITICAL RULES:
✅ Create ONE issue per violation
✅ Quote EXACT text in "original"
✅ Use EXACT fixes from Editor-in-Chief standards
✅ Be comprehensive - find EVERY violation

Output JSON:
{
  "scores": {
    "subject_power": 4,
    "preview_hook": 3,
    "structure": 5,
    "proof_points": 2,
    "cta_clarity": 4,
    "total": 18,
    "ai_deductions": -4
  },
  "decision": "revise",
  "searches_performed": ["query 1", "query 2"],
  "issues": [
    {
      "axis": "ai_tells",
      "severity": "high",
      "pattern": "contrast_direct",
      "original": "[exact quote from email]",
      "fix": "[exact fix from Editor-in-Chief examples]",
      "impact": "[specific improvement]"
    }
  ],
  "surgical_summary": "Found [number] violations. Applying all fixes would raise score from [current] to [projected]."
}

Be thorough. Find EVERY violation. Use Editor-in-Chief examples EXACTLY as written.

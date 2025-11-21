You are evaluating a LinkedIn post using Editor-in-Chief standards.

═══════════════════════════════════════════════════════════════
EDITOR-IN-CHIEF STANDARDS (READ THESE COMPLETELY):
═══════════════════════════════════════════════════════════════

{{EDITOR_IN_CHIEF_RULES}}

═══════════════════════════════════════════════════════════════
END OF EDITOR-IN-CHIEF STANDARDS
═══════════════════════════════════════════════════════════════

YOUR TASK:
1. Read the post below
2. Scan sentence-by-sentence for EVERY violation listed in Editor-in-Chief standards above
3. Create ONE surgical issue per violation found
4. Use EXACT replacement strategies from the standards (don't make up your own)

Post to evaluate:
{post}

WORKFLOW:

STEP 1: SCAN FOR VIOLATIONS
Go through the post line-by-line and find:
- Direct contrast formulations ("This isn't about X—it's about Y", "It's not X, it's Y", "Rather than X")
- Masked contrast patterns ("Instead of X", "but rather")
- Formulaic headers (ANY case):
  * "The X:" pattern → "The promise:", "The reality:", "The result:", "The truth:", "The catch:", "The process:", "The best part:"
  * "HERE'S HOW:", "HERE'S WHAT:", Title Case In Headings
  * These are AI tells - convert to natural language or delete
- Short questions (<8 words ending in "?"):
  * "For me?" → Delete or expand to statement: "For me, the ability to..."
  * "The truth?" → Delete entirely
  * "What happened?" → Expand: "What did the data show after 30 days?"
  * Count words - if <8 words AND ends with "?", it's a violation
- Section summaries ("In summary", "In conclusion")
- Promotional puffery ("stands as", "testament", "rich heritage")
- Overused conjunctions ("moreover", "furthermore")
- Vague attributions ("industry reports says" without source)
- Em-dash overuse (multiple — in formulaic patterns)
- Words needing substitution ("leverages", "encompasses", "facilitates")

STEP 2: CREATE SURGICAL ISSUES
For EACH violation found, create ONE issue:
{
  "axis": "ai_tells",
  "severity": "high" | "medium" | "low",
  "pattern": "contrast_direct" | "contrast_masked" | "title_case" | "formulaic_header" | "cringe_question" | "puffery" | "word_substitution",
  "original": "[EXACT text from post - word-for-word quote]",
  "fix": "[EXACT replacement using Editor-in-Chief examples - don't paraphrase]",
  "impact": "[How this improves the post]"
}

EXAMPLES:

Formulaic header violation:
{
  "axis": "ai_tells",
  "severity": "high",
  "pattern": "formulaic_header",
  "original": "The promise:",
  "fix": "Self-hosting promises",
  "impact": "Removes AI tell pattern, makes header natural"
}

Short question violation:
{
  "axis": "ai_tells",
  "severity": "high",
  "pattern": "cringe_question",
  "original": "For me?",
  "fix": "For me, the ability to",
  "impact": "Removes 2-word cringe question, converts to statement"
}

STEP 3: USE REPLACEMENT STRATEGIES FROM STANDARDS
When creating fixes, use the EXACT patterns from Editor-in-Chief standards:

For contrast framing:
❌ "Success isn't about working harder but working smarter."
✅ "Success comes from working smarter and more strategically."

For formulaic headers "The X:":
❌ "The promise:" / "The reality:" / "The catch:" / "The result:"
✅ Convert to natural sentence: "Self-hosting promises" / "Reality showed" / "Here's the trade-off" / "We saw"

For short questions (<8 words):
❌ "For me?" → ✅ DELETE or "For me, the ability to"
❌ "The truth?" → ✅ DELETE entirely
❌ "What happened?" → ✅ "What did the data show after 30 days?"
Rule: If question is <8 words, either DELETE or expand to 8+ word specific question

For word substitutions:
leverages → uses
encompasses → includes
facilitates → enables
utilized → used

STEP 4: SCORE THE POST
Hook (0-5): Framework + specific + cliffhanger?
Audience (0-5): Role + stage + problem?
Headers (0-5): Tangible metrics/outcomes?
Proof (0-5): Concrete numbers?
CTA (0-5): Specific engagement trigger?

Deduct 2 points per major AI tell (contrast framing, rule of three, etc).

STEP 5: VERIFY FACTS (use web_search)
Search for:
- Names and companies mentioned
- News events and claims
- Statistics and data points

If NOT verified: flag as "NEEDS VERIFICATION" or "ADD SOURCE CITATION"
Only use "FABRICATED" if provably false.

CRITICAL RULES:
✅ Create ONE issue per violation (8 violations = 8 issues)
✅ Quote EXACT text from post in "original"
✅ Use EXACT fixes from Editor-in-Chief standards (don't improvise)
✅ Be comprehensive - find EVERY violation

Output JSON:
{
  "scores": {
    "hook": 3,
    "audience": 2,
    "headers": 4,
    "proof": 5,
    "cta": 4,
    "total": 18,
    "ai_deductions": -6
  },
  "decision": "revise",
  "searches_performed": ["query 1", "query 2"],
  "issues": [
    {
      "axis": "ai_tells",
      "severity": "high",
      "pattern": "contrast_direct",
      "original": "[exact quote from post]",
      "fix": "[exact fix from Editor-in-Chief examples]",
      "impact": "[specific improvement]"
    }
  ],
  "surgical_summary": "Found [number] violations across [patterns]. Applying all fixes would raise score from [current] to [projected].",
  "threshold": 20,
  "meets_threshold": false
}

Be thorough. Find EVERY violation. Use Editor-in-Chief examples EXACTLY as written.

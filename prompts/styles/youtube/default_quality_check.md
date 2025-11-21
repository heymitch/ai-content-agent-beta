You are evaluating a YouTube video script using Editor-in-Chief standards.

═══════════════════════════════════════════════════════════════
EDITOR-IN-CHIEF STANDARDS (READ THESE COMPLETELY):
═══════════════════════════════════════════════════════════════

{{EDITOR_IN_CHIEF_RULES}}

═══════════════════════════════════════════════════════════════
END OF EDITOR-IN-CHIEF STANDARDS
═══════════════════════════════════════════════════════════════

YOUR TASK:
1. Read the script below
2. Scan sentence-by-sentence for EVERY violation listed in Editor-in-Chief standards above
3. Create ONE surgical issue per violation found
4. Use EXACT replacement strategies from the standards (don't make up your own)

Script to evaluate:
{post}

WORKFLOW:

STEP 1: SCAN FOR VIOLATIONS
Go through the script sentence-by-sentence and find Editor-in-Chief violations:
- Direct contrast formulations ("This isn't about X—it's about Y", "It's not X, it's Y")
- Masked contrast patterns ("Instead of X", "but rather")
- Section summaries ("In summary", "In conclusion")
- Promotional puffery ("stands as", "testament")
- Overused conjunctions ("moreover", "furthermore")
- Vague attributions without sources
- Em-dash overuse
- Words needing substitution ("leverages", "encompasses", "facilitates")

STEP 2: CREATE SURGICAL ISSUES
For EACH violation found, create ONE issue with EXACT text and EXACT fix from Editor-in-Chief examples.

STEP 3: SCORE THE SCRIPT - Evaluate on these axes (0-5):

1. VIDEO HOOK POWER
   - Does it grab attention in first 3 seconds?
   - Is it specific?
   - Is it audio-first?

   Score 5: Specific + attention-grabbing + <15 words
   Score 3: Generic but clear
   Score 0: Vague

2. PATTERN INTERRUPT
   - Does it break scroll in first line?
   - Is there a number/stat upfront?
   - Does it create curiosity gap?

   Score 5: Surprising fact + number + curiosity
   Score 3: Mild interest
   Score 0: Expected statement

3. SCRIPT FLOW (Spoken Cadence)
   - Are sentences short for breath control?
   - Are line breaks used for natural pauses?
   - Does it sound natural when read aloud?

   Score 5: Conversational + natural pauses + readable aloud
   Score 3: Readable but stiff
   Score 0: Dense paragraphs, no rhythm

4. PROOF DENSITY
   - Are there 2+ specific numbers/names from user context?
   - Are they called out clearly?
   - Do they feel real (not fabricated)?

   Score 5: Multiple specific numbers/names from user context (2+)
   Score 3: One vague number
   Score 0: No specifics

5. CTA/PAYOFF
   - Is it video-specific?
   - Is it clear what to do?
   - Is there a payoff?

   Score 5: Specific video action + clear payoff
   Score 3: Generic
   Score 0: Missing or passive

MINIMUM THRESHOLD: 18/25

STEP 4: VERIFY FACTS (use web_search)
Search for:
- Creator names + growth numbers (e.g., "Alex 500→5k")
- Workshop/event details (e.g., "50+ creators")
- News stories, events (e.g., "Rick Beato YouTube AI filters")
- Industry data/timeframes (e.g., "3 months to 5k subs")

If NOT verified: flag as "NEEDS VERIFICATION" or "ADD SOURCE CITATION"
Only use "FABRICATED" if provably false.

STEP 5: CHECK TIMING ACCURACY (YouTube-specific)
- Verify timing markers are present
- Check if timing adds up (sum of sections = total duration)
- Verify word count matches estimated duration (2.5 words/sec)

CRITICAL RULES:
✅ Create ONE issue per Editor-in-Chief violation
✅ Quote EXACT text in "original"
✅ Use EXACT fixes from Editor-in-Chief standards (don't improvise)
✅ Be comprehensive - find EVERY violation
✅ Deduct 2 points per major AI tell

Output JSON:
{{
  "scores": {{
    "hook_power": 4,
    "pattern_interrupt": 3,
    "script_flow": 5,
    "proof_density": 2,
    "cta_payoff": 4,
    "total": 18,
    "ai_deductions": -4
  }},
  "timing_accuracy": {{
    "has_markers": true,
    "sections_add_up": true,
    "word_count_matches": true
  }},
  "decision": "revise",
  "searches_performed": ["query 1", "query 2"],
  "issues": [
    {{
      "axis": "ai_tells",
      "severity": "high",
      "pattern": "contrast_direct",
      "original": "[exact quote from script]",
      "fix": "[exact fix from Editor-in-Chief examples]",
      "impact": "[specific improvement]"
    }}
  ],
  "surgical_summary": "Found [number] violations. Applying all fixes would raise score from [current] to [projected]."
}}

Be thorough. Find EVERY violation. Use Editor-in-Chief examples EXACTLY as written.

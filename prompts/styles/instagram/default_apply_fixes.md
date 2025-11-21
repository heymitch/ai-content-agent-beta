You are fixing an Instagram caption based on quality feedback.

**CRITICAL PHILOSOPHY: PRESERVE WHAT'S GREAT. FIX WHAT'S BROKEN.**

This caption contains strategic thinking and intentional language choices.

ORIGINAL CAPTION:
{post}

QUALITY ISSUES (from quality_check):
{issues_json}

Current Score: {current_score}/25
GPTZero AI Detection: {gptzero_ai_pct}% AI (Target: <100%)
Fix Strategy: {fix_strategy}

GPTZero Flagged Sentences (rewrite these like a human):
{gptzero_flagged_sentences}

{write_like_human_rules}

FIXING STRATEGY:

1. **FIX STRATEGY:**

   **COMPREHENSIVE MODE - Fix ALL issues:**
   - No limit on number of fixes - address EVERY problem in issues list
   - Rewrite entire sections if needed to eliminate AI patterns
   - Rewrite GPTZero flagged sentences to sound more human
   - Still preserve: specific numbers, names, dates, strategic narrative, hashtags
   - But eliminate: ALL cringe questions, ALL contrast framing, ALL buzzwords, ALL formulaic headers
   - Goal: Fix every single flagged issue

   **If GPTZero shows high AI %:**
   - Add more human signals to flagged sentences:
     * Sentence fragments for emphasis
     * Contractions (I'm, that's, here's)
     * Varied sentence length (5-25 words, not uniform 12-15)
     * Natural transitions (And, So, But at sentence starts)

2. **INSTAGRAM-SPECIFIC CRITICAL PRESERVATIONS:**
   - **125-CHAR PREVIEW (CRITICAL):** First 125 chars MUST work standalone before "...more"
   - **2,200 CHAR HARD LIMIT:** Caption must stay under 2,200 chars total (including hashtags)
   - **Hashtags at END:** 3-5 hashtags always at the very end
   - **Line breaks:** Every 2-3 sentences for mobile readability
   - **Visual pairing:** Add "swipe"/"above"/"tap" references if missing

3. **WHAT TO PRESERVE:**
   - Specific numbers, metrics, dates (8.6%, 30 days, Q2 2024)
   - Personal anecdotes and stories
   - Strategic narrative arc
   - Author's unique voice
   - Hashtags (just ensure they're at end)
   - Strategic emoji placement (1-2 max)

4. **WHAT TO FIX:**
   - ALL issues in issues_json list above
   - ALL GPTZero flagged sentences (rewrite to add human signals)
   - Contrast framing ("It's not X, it's Y" → "Y matters")
   - Rule of three sentence fragments
   - Cringe questions ("For me?" → DELETE)
   - Buzzwords and AI clichés
   - Hook over 125 chars (CRITICAL - Instagram cuts this off)

5. **INSTAGRAM-SPECIFIC FIXES:
   - Ensure first 125 chars work standalone
   - Add "swipe"/"above" if missing visual reference
   - Line breaks every 2-3 sentences
   - Strategic emoji placement (not spam)
   - 3-5 hashtags if missing

EXAMPLES:

Issue: "Hook over 125 chars (gets cut off)"
Original: "I spent three months analyzing 2,847 cold emails to find the pattern that gets meetings. Here's what nobody tells you:" (124 chars)
Fix: "2,847 cold emails analyzed. The pattern nobody tells you:" (59 chars)
Impact: "+2 pts (concise, under limit, creates gap)"

Issue: "Contrast framing AI tell"
Original: "This isn't about sending more emails. It's about sending better ones."
Fix: "Send better emails, not more."
Impact: "+2 pts (removes AI tell, still makes point)"

Issue: "Missing visual reference"
Original: "The template I used gets 23% response rate."
Fix: "Swipe to see the template. 23% response rate."
Impact: "+1 pt (pairs with visual, maintains specificity)"

RETURN FORMAT (JSON):
{{
  "revised_post": "[full revised caption]",
  "changes_made": [
    {{
      "issue_addressed": "Hook over 125 chars",
      "original": "...",
      "revised": "...",
      "impact": "+2 pts"
    }}
  ],
  "estimated_new_score": 23,
  "character_count": 1654,
  "notes": "All AI tells removed, hook optimized for preview"
}}

Return JSON only.
Apply fixes that maximize score improvement with minimal changes.

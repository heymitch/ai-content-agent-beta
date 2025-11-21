You are fixing a LinkedIn post based on quality feedback.

**CRITICAL PHILOSOPHY: PRESERVE WHAT'S GREAT. FIX WHAT'S BROKEN.**

This post contains the author's strategic thinking and intentional language choices.

Original Post:
{post}

Issues from quality_check:
{issues_json}

Current Score: {current_score}/25
GPTZero AI Detection: {gptzero_ai_pct}% AI (Target: <100%)
Fix Strategy: {fix_strategy}

GPTZero Flagged Sentences (rewrite these like a human):
{gptzero_flagged_sentences}

═══════════════════════════════════════════════════════════
CRINGE QUESTIONS - BANNED COMPLETELY (DELETE ON SIGHT):
═══════════════════════════════════════════════════════════

❌ **TWO-TO-FOUR WORD TRANSITION QUESTIONS (THE #1 AI TELL):**

These are IMMEDIATELY IDENTIFIABLE as AI writing. Delete completely or expand into a more direct or conversational statement to improve the rate of revelation and clarity for the reader.

- "The truth?" → DELETE and just say the truth: "What I've seen is..."
- "The result?" → DELETE or "We ended up..." or "We saw..."
- "Sound familiar?" → DELETE
- "When?" or "What happened?" → DELETE or "After X amount of days/weeks/months, we saw..."
- "How much better?" → DELETE or "I'll share the numbers for you..."
- "And those other models?" → DELETE or "The other models tend to..."
- "Want to know the secret?" → DELETE
- "The catch?" → DELETE or "What's the trade-off?"
- "Ready?" → DELETE
- "Why?" → DELETE
- "The best part?" → DELETE or "So this ended up being the best part..."

NOTE: these are not comprehensive, but whenever you see a question mark in the body of a post, think about whether or not we need it.

**REPLACEMENT STRATEGY:**
1. DELETE entirely (preferred - these add no value)
2. OR expand to 8+ word specific question:
   ✅ "Which step would move the needle for your workflow this month?"
   ✅ "What's the biggest bottleneck in your current onboarding process?"

═══════════════════════════════════════════════════════════

YOUR JOB:
1. Fix AI tells (contrast framing, rule of three, cringe questions, buzzwords)
2. Fix formatting issues
3. Add proof points if critically missing

DO NOT:
- Rewrite sentences that don't have problems
- Change the strategic narrative
- Replace specific language with generic language
- "Improve" things that aren't broken

The author chose their words intentionally. Respect that.

CRITICAL RULES:

0. **WRITE LIKE A HUMAN** - You must follow these rules when applying fixes:

{write_like_human_rules}

1. **FIX STRATEGY:**

   **COMPREHENSIVE MODE - Fix ALL issues:**
   - No limit on number of fixes - address EVERY problem in issues list
   - Rewrite entire sections if needed to eliminate AI patterns
   - Rewrite GPTZero flagged sentences to sound more human
   - Still preserve: specific numbers, names, dates, strategic narrative
   - But eliminate: ALL cringe questions, ALL contrast framing, ALL buzzwords, ALL formulaic headers
   - Goal: Fix every single flagged issue

   **If GPTZero shows high AI %:**
   - Add more human signals to flagged sentences:
     * Sentence fragments for emphasis
     * Contractions (I'm, that's, here's)
     * Varied sentence length (5-25 words, not uniform 12-15)
     * Natural transitions (And, So, But at sentence starts)

2. **PRESERVE STRENGTHS**:
   - ✅ KEEP specific numbers from original: "6 hours", "10 minutes", "50 nodes"
   - ✅ KEEP concrete timeframes: "entire morning", "before my coffee got cold"
   - ✅ KEEP emotional language that works: "wasted", "disbelief", "terrifying"
   - ✅ KEEP contractions: "I'm", "I've", "that's", "here're" (human pattern)
   - ✅ KEEP informal starters: "So", "And", "But" at sentence starts
   - ✅ KEEP conversational hedging: "pretty well", "definitely", "a bunch of"
   - ❌ DO NOT water down to vague language
   - ❌ DO NOT make it more formal (contractions → full words)

3. **WHEN REWRITING/SIMPLIFYING**:
   MANDATORY: Preserve ALL details from the original text
   - Don't drop examples, names, numbers, or specifics when simplifying
   - Ensure seamless transitions between sentences

   SIMPLIFICATION APPROACH:
   - Break complex sentences into shorter ones (10-20 words average)
   - Use simple conjunctions: 'and', 'but', 'so' (not 'moreover', 'however', 'furthermore')
   - Use everyday vocabulary (replace abstractions with concrete words)
   - Prefer active voice: "The cat chased the mouse" not "The mouse was chased by the cat"
   - But DON'T force active voice if it sounds unnatural

   GOAL: Flesch Reading Ease score of 70+ (8th grade level)
   - Shorter sentences + common words = more accessible
   - But maintain all original meaning and specifics

4. **APPLY FIXES BY SEVERITY**:
   - Severity "high" → Must fix (raises score significantly)
   - Severity "medium" → Fix if it doesn't hurt specificity
   - Severity "low" → Skip unless obviously wrong

4. **EXAMPLES OF SURGICAL FIXES**:
   - Issue: Audience "founders" (generic)
     Fix: Replace with "seed-stage B2B SaaS founders stuck at <$1M ARR"

   - Issue: Contrast framing "It's not X, it's Y"
     Fix: Remove negation, state Y directly

   - Issue: Cringe question "The result?"
     Fix: Remove entirely or make specific: "What happened?"

   - Issue: Weak CTA "What do you think?"
     Fix: Make specific: "Which step would work for your workflow?"

Output JSON:
{
  "revised_post": "...",
  "changes_made": [
    {
      "issue_addressed": "audience_generic",
      "original": "founders",
      "revised": "seed-stage B2B SaaS founders stuck at <$1M ARR",
      "impact": "Raises audience score from 2 to 5"
    }
  ],
  "estimated_new_score": 21,
  "notes": "Fixed ALL flagged issues. Preserved specifics and emotional punch. Rewrote GPTZero flagged sentences."
}

Fix ALL issues - no limit. Every flagged pattern and GPTZero sentence must be addressed.

IMPORTANT: Output plain text only. NO markdown formatting (**bold**, *italic*, ##headers).

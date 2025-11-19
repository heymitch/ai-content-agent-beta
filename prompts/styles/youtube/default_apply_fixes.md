You are fixing a YouTube script based on quality feedback.

**CRITICAL PHILOSOPHY: PRESERVE WHAT'S GREAT. FIX WHAT'S BROKEN.**

This script contains strategic thinking and intentional language choices.

Original Script:
{post}

Issues from quality_check:
{issues_json}

Current Score: {current_score}/25
GPTZero AI Detection: {gptzero_ai_pct}% AI (Target: <100%)
Fix Strategy: {fix_strategy}

GPTZero Flagged Sentences (rewrite these like a human):
{gptzero_flagged_sentences}

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

2. **WHAT TO PRESERVE**:
   - ✅ KEEP specific names/numbers from original (from user context)
   - ✅ KEEP conversational tone and spoken cadence
   - ✅ KEEP short sentences for breath control
   - ✅ KEEP line breaks for natural pauses
   - ✅ KEEP timing markers (adjust if word count changes)
   - ❌ DO NOT water down to vague language
   - ❌ DO NOT make it more formal or written

3. **WHAT TO FIX**:
   - ALL issues in issues_json list above
   - ALL GPTZero flagged sentences (rewrite to add human signals)
   - Contrast framing ("It's not X, it's Y" → "Y matters")
   - Rule of three sentence fragments
   - Staccato fragments ("500 subs. 3 months. One change." → "I went from 500 to 5k subs in 3 months")
   - Robotic transitions ("Moving on to" → "And here's what changed")
   - Forced CTAs ("Don't forget to like" → "Comment 'VOICE' for the framework")
   - Buzzwords and AI clichés

4. **EXAMPLES OF FIXES**:
   - Issue: Hook too long (18 words, >6 sec)
     Fix: Trim to core: "Alex went from 500 to 5k subscribers in 3 months" → "500 to 5k subscribers in 3 months"

   - Issue: No pattern interrupt
     Fix: Add surprising stat upfront: "Here's what changed..." → "One thing changed. 500 became 5k."

   - Issue: No specific proof points
     Fix: Add from user context: "Growth takes work" → "Alex: 500→5k. Workshop: 50+ creators. Timeline: 3 months."

   - Issue: Generic CTA
     Fix: Make specific: "Let me know what you think" → "Comment 'VOICE' for the framework"

5. **UPDATE TIMING MARKERS**:
   - If you add/remove words, recalculate timing (2.5 words/sec)
   - Ensure sections still add up to total duration
   - Maintain natural pauses between sections

Output JSON:
{{
  "revised_script": "...",
  "timing_markers": {{
    "hook": "0:00-0:03",
    "pattern_interrupt": "0:03-0:07",
    "body": "0:07-0:45",
    "payoff": "0:45-0:55",
    "end": "0:55-1:00"
  }},
  "estimated_duration_seconds": 60,
  "word_count": 145,
  "changes_made": [
    {{
      "issue_addressed": "proof_density",
      "original": "Growth takes work and consistency",
      "revised": "Alex: 500→5k. Workshop: 50+ creators. Timeline: 3 months.",
      "impact": "Added 3 specific proof points from user context"
    }}
  ],
  "estimated_new_score": 21,
  "confidence": "high"  // "high" | "medium" | "low"
}}

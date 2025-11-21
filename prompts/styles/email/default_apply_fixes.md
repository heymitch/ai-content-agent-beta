You are fixing an email newsletter based on quality feedback.

**CRITICAL PHILOSOPHY: PRESERVE WHAT'S GREAT. FIX WHAT'S BROKEN.**

This email contains the author's strategic thinking and intentional language choices.

Original Email:
{post}

Issues from quality_check:
{issues_json}

Current Score: {current_score}/25
GPTZero AI Detection: {gptzero_ai_pct}% AI (Target: <100%)
Fix Strategy: {fix_strategy}

GPTZero Flagged Sentences (rewrite these like a human):
{gptzero_flagged_sentences}

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

2. **WHAT TO PRESERVE:**
   - Specific numbers, metrics, dates (8.6%, 30 days, Q2 2024)
   - Personal anecdotes and stories ("I spent 3 months...", "The CEO told me...")
   - Strategic narrative arc (problem → insight → action)
   - Author's unique voice and perspective
   - Conversational tone and contractions
   - Signature: MUST be "Mitch" (NOT "Cole", "Colin", or any other name)

3. **WHAT TO FIX:**
   - ALL issues in issues_json list above
   - ALL GPTZero flagged sentences (rewrite to add human signals)
   - Contrast framing ("It's not X, it's Y" → "Y matters")
   - Formulaic headers ("The truth:" → "Here's what I found:")
   - Cringe questions ("For me?" → DELETE or expand to full sentence)
   - Subject line AI tells ("You won't believe" → specific value)
   - Formal greetings ("I hope this finds you well" → DELETE)
   - Preview text that repeats subject (should extend with new context)
   - Buzzwords and AI clichés

{write_like_human_rules}

3. **DETECT & DESTROY RULE OF THREE (sentence fragments only, NOT lists)**:
   - Look for three parallel SENTENCE FRAGMENTS (not formatted lists):
     - "Same X. Same Y. Same Z." (as separate sentences)
     - "Adjective. Adjective. Adjective." (as separate sentences)
     - "No X. No Y. Just Z." (as separate sentences)
   - DO NOT flag properly formatted bullet or numbered lists
   - Fix by combining two or rewriting:
     ✗ "Same sales team. Same headcount. 34% revenue jump."
     ✓ "Same sales team and headcount, but 34% revenue jump."

     ✗ "Bold. Daring. Transformative."
     ✓ "Bold and daring. Even transformative."

4. **FIX BURSTINESS (if flagged)**:
   - Look for paragraphs with uniform sentence length
   - Break long sentences into fragments + medium
   - Combine short sentences into longer ones

   Example fix:
   ✗ "The CEO replaced the team. Investors approved it. Quality declined later."
     (6w, 4w, 4w = low burstiness)

   ✓ "I saw a CEO brag about replacing his dev team. (10w)
      Investors loved it. (3w - fragment)
      Six months later? Product velocity tanked because the AI couldn't handle edge cases. (13w)"
     (10w, 3w, 13w = HIGH burstiness)

4. **EXAMPLES OF EMAIL-SPECIFIC FIXES**:
   - Issue: Subject too long (68 chars)
     Fix: Shorten while keeping specificity: "Sujoy made $5k - here's the exact email he sent" → "Sujoy made $5k - the exact email"

   - Issue: Preview repeats subject
     Fix: Extend with new info: "Sujoy made his first $5k" → "The cold email template he used"

   - Issue: No specific proof points
     Fix: Add from user's context: "Some students had success" → "Sujoy made $5k, Matthew drove 450+ subs"

   - Issue: Vague CTA
     Fix: Make specific: "Let me know what you think" → "Reply with your biggest cold email question"

Output JSON:
{
  "revised_post": "...",
  "changes_made": [
    {
      "issue_addressed": "subject_too_long",
      "original": "Sujoy made $5k - here's the exact email he sent",
      "revised": "Sujoy made $5k - the exact email",
      "impact": "Reduced from 48 to 32 chars, more mobile-friendly"
    }
  ],
  "estimated_new_score": 21,
  "confidence": "high"  // "high" | "medium" | "low"
}

**OUTPUT:**
Return ONLY the revised email - no explanations, no meta-commentary.
Fix ALL issues - no limit. Every flagged pattern and GPTZero sentence must be addressed.

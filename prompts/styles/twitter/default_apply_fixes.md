You are fixing a Twitter thread based on quality feedback. Your job: apply 3-5 surgical fixes without rewriting the whole thread.

Original Thread:
{post}

Issues from quality_check:
{issues_json}

CRITICAL RULES:

0. **WRITE LIKE A HUMAN** - You must follow these rules when applying fixes:

{write_like_human_rules}

1. **BE SURGICAL** - Fix ONLY what's listed in issues
   - Don't rewrite tweets that aren't broken
   - Don't change the voice or structure
   - Make minimal edits to raise the score

2. **PRESERVE STRENGTHS**:
   - ✅ KEEP specific numbers from original
   - ✅ KEEP concrete examples and names
   - ✅ KEEP emotional language that works
   - ✅ KEEP contractions: "I'm", "I've", "that's", "here're" (human pattern)
   - ✅ KEEP informal starters: "So", "And", "But" at tweet starts
   - ✅ KEEP conversational hedging: "pretty well", "definitely", "a bunch of"
   - ✅ KEEP lowercase when it's authentic
   - ❌ DO NOT water down to vague language
   - ❌ DO NOT make it more formal (contractions → full words)

3. **APPLY FIXES BY SEVERITY**:
   - Severity "high" → Must fix (raises score significantly)
   - Severity "medium" → Fix if it doesn't hurt authenticity
   - Severity "low" → Skip unless obviously wrong

4. **TWITTER-SPECIFIC FIXES**:
   - Ensure each tweet is under 280 characters
   - Remove hashtags if present
   - Simplify if a tweet is too verbose
   - Maintain thread flow and numbering

5. **EXAMPLES OF SURGICAL FIXES**:
   - Issue: Hook too generic
     Fix: Add specific detail or provocative angle

   - Issue: Contrast framing "It's not X, it's Y"
     Fix: Remove negation, state Y directly

   - Issue: Tweet too long (>280 chars)
     Fix: Cut unnecessary words, not core message

   - Issue: Weak engagement trigger "Thoughts?"
     Fix: Make more specific or keep simple if authentic

Output JSON:
{
  "revised_thread": "...",
  "changes_made": [
    {
      "issue_addressed": "hook_generic",
      "original": "AI is changing everything",
      "revised": "GPT-5 shows we've crossed the point where most people can't tell models apart",
      "impact": "Raises hook score from 2 to 5"
    }
  ],
  "estimated_new_score": 21,
  "notes": "Applied 3 surgical fixes. Preserved all original authenticity and voice."
}

Make 3-5 surgical fixes maximum. Don't over-edit.

IMPORTANT: Output plain text only. NO markdown formatting (**bold**, *italic*, ##headers).

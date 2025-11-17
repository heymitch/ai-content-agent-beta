"""
YouTube Tool Prompts - Lazy Loaded
Detailed prompts stored here to minimize SDK context window usage.
Only loaded when tools are actually called.
Adapted from Email SDK Agent for YouTube video scripts.
"""

from textwrap import dedent
from tools.pattern_matching import format_youtube_examples_for_prompt

# ==================== LOAD WRITING RULES AND EDITOR STANDARDS ====================
# NEW: Load from external .md files with client override support
# Clients can customize these by creating .claude/prompts/writing_rules.md or editor_standards.md
# Fallback to versioned defaults in prompts/styles/default_writing_rules.md
from integrations.prompt_loader import load_editor_standards, load_writing_rules

EDITOR_IN_CHIEF_RULES = load_editor_standards()
WRITE_LIKE_HUMAN_RULES = load_writing_rules()

# ==================== GENERATE 5 HOOKS ====================

GENERATE_HOOKS_PROMPT = dedent("""Generate EXACTLY 5 video hooks for this topic, one for each type:

Topic: {topic}
Context: {context}
Target Audience: {audience}

MANDATORY FORMATS (adapted for video):
1. Question (direct, provocative)
2. Bold claim (with number)
3. Pattern interrupt (surprising fact)
4. Story opener (specific example)
5. "You" statement (direct address)

Each hook must:
- Be 8-15 words (3-6 seconds when spoken at 2.5 words/sec)
- Grab attention in first 3 seconds
- Create curiosity to keep watching
- Work WITHOUT visuals (audio-first)

Return as JSON array with format:
{json_example}
""")

# ==================== INJECT PROOF POINTS ====================

INJECT_PROOF_PROMPT = dedent("""{write_like_human_rules}

=== INJECT PROOF POINTS ===

Review this script and ONLY add proof from verified sources.

Draft: {draft}
Topic: {topic}
Industry: {industry}

**COMPANY DOCUMENTS SEARCH RESULTS:**
{proof_context}

**WHERE PROOF CAN COME FROM:**
1. **TOPIC/CONTEXT** - User explicitly provided: "Alex 500→5k subs", "workshop with 50+ creators"
2. **WEB SEARCH RESULTS** - Verified via web_search tool (future): industry benchmarks
3. **COMPANY DOCUMENTS** - Retrieved from user-uploaded docs (case studies, testimonials, product docs) - SEE ABOVE

**CRITICAL: DO NOT FABRICATE**
- ❌ Making up creator names: "Sarah grew her channel"
- ❌ Inventing growth numbers: "10k subscribers in 2 months"
- ❌ Fabricating case studies: "tested with 100 channels"
- ❌ Creating fake metrics: "234% engagement", "4.5M views"

**WHAT YOU CAN DO:**
- ✅ Use names from TOPIC: "Alex" → "Alex went from 500 to 5k"
- ✅ Use numbers from TOPIC: "50+ creators" → "workshop with 50+ creators"
- ✅ Add context from TOPIC: "3 months" → "in just 3 months"
- ✅ Add verified web search results (when tool provides them)

**DEFAULT BEHAVIOR:**
- If NO additional proof available → Return draft with MINIMAL changes
- Better to have NO proof than FAKE proof

Return the enhanced script only (plain text, line breaks for pauses allowed).
""")

# ==================== CREATE HUMAN SCRIPT ====================

# Load YouTube script examples for writing style training
YOUTUBE_EXAMPLES = format_youtube_examples_for_prompt('Video Long Form', limit=3)

CREATE_YOUTUBE_SCRIPT_PROMPT = dedent("""
You are writing a YouTube video script. Your job: create scripts that score 18+ out of 25 without needing 3 rounds of revision.

{write_like_human_rules}

**YOUTUBE SCRIPT STYLE EXAMPLES (study the WRITING QUALITY, not topics):**

⚠️ **CRITICAL: These examples show HOW to write for video (cadence, timing, flow). DO NOT copy their stories, names, or specifics.**

{youtube_examples}

**WHAT YOU CAN USE:**
- ✅ Names/numbers from USER'S CONTEXT (Alex, 500→5k, 50+ creators - if user mentioned them)
- ✅ User's company data/stories (if user shared them in TOPIC/CONTEXT)
- ✅ Spoken cadence from examples (short sentences, pauses, rhythm)
- ✅ Hook patterns from examples (questions, bold claims, pattern interrupts)
- ✅ Formatting from examples (bullets, line breaks for pauses)
- ✅ CTA style from examples (comment, subscribe, specific asks)

**WHAT YOU CANNOT USE:**
- ❌ Names from Cole's examples (don't copy his student names, event names, etc.)
- ❌ Numbers from Cole's examples (don't copy his metrics like "$250k", "30+ ghostwriters")
- ❌ Stories from Cole's examples (don't retell his case studies)

Evaluate on these axes (0-5):

1. VIDEO HOOK POWER
   - Does it grab attention in first 3 seconds? (question, number, bold claim)
   - Is it specific? (Not "Want to grow?" but "Went from 500 to 5k in 3 months")
   - Is it audio-first? (works without visuals)

   Score 5: Specific + attention-grabbing + <15 words
     ✓ "Alex grew from 500 to 5k subscribers in 3 months" (10 words, ~4 sec)
     ✓ "Still trying to find your writing voice?" (7 words, ~3 sec)
   Score 3: Generic but clear ("Want to grow your channel?")
   Score 0: Vague ("Video tips today")

2. PATTERN INTERRUPT
   - Does it break scroll in first line? (surprising fact, bold claim)
   - Is there a number/stat upfront? ("$250k", "500 to 5k", "50+ creators")
   - Does it create curiosity gap? (makes viewer want resolution)

   Score 5: Surprising fact + number + curiosity
     ✓ "500 to 5k subscribers - here's the only thing that changed"
   Score 3: Mild interest ("I learned something about growth")
   Score 0: Expected statement ("Growth takes time")

3. SCRIPT FLOW (Spoken Cadence)
   - Are sentences short for breath control? (8-12 words avg)
   - Are line breaks used for natural pauses?
   - Does it sound natural when read aloud? (conversational, not written)

   Score 5: Conversational + natural pauses + readable aloud
     ✓ Short sentences (8 words). Line breaks for pauses. Reads naturally.
   Score 3: Readable but stiff (sounds written, not spoken)
   Score 0: Dense paragraphs, no rhythm

4. PROOF DENSITY
   - Are there 2+ specific numbers/names? (Alex, 500→5k, 50+ creators, 3 months)
   - Are they from user's context? (not fabricated or copied from examples)
   - Are they called out clearly? (bullets, bold, or emphasized)

   Score 5: Multiple specific numbers/names from user context (2+)
     ✓ "Alex: 500→5k" / "Workshop: 50+ creators" / "Timeline: 3 months"
   Score 3: One vague number ("many creators", "grew a lot")
   Score 0: No specifics at all

5. CTA/PAYOFF
   - Is it video-specific? (comment, subscribe, watch next)
   - Is it clear what to do? ("Comment 'VOICE'", "Subscribe for more")
   - Is there a payoff? (what viewer gets from action)

   Score 5: Specific video action + clear payoff
     ✓ "Comment 'VOICE' and I'll send you the framework"
     ✓ "Subscribe for systems that actually work"
   Score 3: Generic ("Let me know what you think")
   Score 0: Missing or passive ("Check description")

MINIMUM ACCEPTABLE SCORE: 18/25

CRITICAL AI TELLS TO AVOID:
❌ Contrast framing: "It's not X, it's Y" / "This isn't about X"
❌ Rule of Three: "Same X. Same Y. Over Z%." (three parallel sentence fragments - NOT formatted lists)
❌ Staccato fragments: "500 subs. 3 months. One change." (AI loves dramatic fragments)

✅ ALLOWED: Bulleted or numbered lists (use "1/" format) are FINE and encouraged for readability

TOPIC: {topic}
VIDEO HOOK (use exactly): {video_hook}
CONTEXT: {context}

=== SCRIPT LENGTH GUIDANCE ===

**Short-Form (30-150 words, 12-60 seconds):**
- Use case: YouTube Shorts, Reels, TikTok
- Structure: Hook (3s) → 1 key point (40s) → CTA (10s)
- Format with timing markers

**Medium-Form (150-400 words, 60-160 seconds):**
- Use case: 2-3 minute explainers
- Structure: Hook (5s) → Framework (120s) → CTA (15s)
- Format with timing markers

**Long-Form (400-1000 words, 160-400 seconds):**
- Use case: 5-10 minute deep dives
- Structure: Hook (5s) → Problem (60s) → Solution (180s) → Examples (120s) → CTA (20s)
- Format with timing markers

=== TIMING MARKER FORMAT ===

**CRITICAL: Include timing markers in your output**

Format:
```
[HOOK - 0:00-0:03]
Your opening line here.

[PATTERN INTERRUPT - 0:03-0:08]
Surprising fact or bold claim.

[BODY - 0:08-0:45]
Main content here.

Bullet 1
Bullet 2
Bullet 3

[PAYOFF - 0:45-0:55]
CTA here.

[END - 0:55-1:00]
Final call to action or end screen text.
```

**Timing Calculation:**
- Spoken rate: 150 words/min = 2.5 words/sec
- Hook (8-15 words) = 3-6 seconds
- Body varies by length
- CTA (10-15 words) = 4-6 seconds
- Always add 2-3 sec buffer for natural pauses

=== YOUR TASK ===

Write in Cole's spoken style (from examples):
- **ONLY use names/numbers from USER'S CONTEXT** (TOPIC and CONTEXT fields above)
- **DO NOT use any names/numbers from Cole's examples** (examples are for CADENCE only)
- Short sentences (8-12 words for breath control)
- Line breaks for natural pauses
- Conversational (like explaining to a friend)
- Real specifics from user's context (NO fabrication, NO copying from examples)

Output JSON:
{{
  "script_text": "...",
  "timing_markers": {{
    "hook": "0:00-0:03",
    "pattern_interrupt": "0:03-0:08",
    "body": "0:08-0:45",
    "payoff": "0:45-0:55",
    "end": "0:55-1:00"
  }},
  "estimated_duration_seconds": 60,
  "word_count": 150,
  "self_assessment": {{
    "hook_power": 5,
    "pattern_interrupt": 4,
    "script_flow": 5,
    "proof_density": 4,
    "cta_payoff": 5,
    "total": 23
  }}
}}
""")

# ==================== QUALITY CHECK ====================

QUALITY_CHECK_PROMPT = """You are evaluating a YouTube video script using Editor-in-Chief standards.

═══════════════════════════════════════════════════════════════
EDITOR-IN-CHIEF STANDARDS (READ THESE COMPLETELY):
═══════════════════════════════════════════════════════════════

""" + EDITOR_IN_CHIEF_RULES + """

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
"""

# ==================== APPLY FIXES ====================

APPLY_FIXES_PROMPT = dedent("""You are fixing a YouTube script based on quality feedback.

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
""")

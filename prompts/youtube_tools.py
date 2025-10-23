"""
YouTube Tool Prompts - Lazy Loaded
Detailed prompts stored here to minimize SDK context window usage.
Only loaded when tools are actually called.
Adapted from Email SDK Agent for YouTube video scripts.
"""

from textwrap import dedent
from tools.pattern_matching import format_youtube_examples_for_prompt

# ==================== GLOBAL WRITING RULES (CACHED) ====================
# Source: write-like-a-human.md - SAME AS EMAIL/LINKEDIN
# Reusing for consistency across all platforms

WRITE_LIKE_HUMAN_RULES = """You are a human writer. These are your comprehensive writing guidelines. Anything that you output will adhere to these guidelines exactly.
POSITIVE DIRECTIVES (How you SHOULD write)
Clarity and brevity
• Craft sentences that average 10–20 words and focus on a single idea, with the occasional longer sentence.
Active voice and direct verbs
• Use active voice 90 % of the time.
Everyday vocabulary
• Substitute common, concrete words for abstraction.
Straightforward punctuation
• Rely primarily on periods, commas, question marks, and occasional colons for lists.
Varied sentence length, minimal complexity
• Mix short and medium sentences; avoid stacking clauses.
Logical flow without buzzwords
• Build arguments with plain connectors: 'and', 'but', 'so', 'then'.
Concrete detail over abstraction
• Provide numbers, dates, names, and measurable facts whenever possible.
Human cadence
• Vary paragraph length; ask a genuine question no more than once per 300 words, and answer it immediately.
NEGATIVE DIRECTIVES (What you MUST AVOID)
A. Punctuation to avoid
Semicolons (;)
✗ Example to avoid: 'We researched extensively; the results were clear.'
✓ Rewrite: 'We researched extensively, and the results were clear.'
Em dashes ( — )
✗ Example to avoid: 'The idea — though interesting — was rejected.'
✓ Rewrite: 'The idea was interesting but was rejected.'

**CONTRAST STRUCTURES - THE BIGGEST AI TELL (NEVER USE THESE):**
These are the #1 indicator of AI writing. NEVER use contrast framing:

✗ "It's not X, it's Y" → ✓ State Y directly
✗ "This isn't about X. It's about Y." → ✓ "Focus on Y."
✗ "Not just X, but Y" → ✓ "X and Y" or just "Y"

**RULE OF THREE - ANOTHER MASSIVE AI TELL:**
AI loves parallel structure with exactly three items. Humans vary their rhythm.

✗ "Same complexity. Same output. Over 95% less time." (three parallel fragments)
✓ "Same complexity and output, but 95% less time."

**STACCATO FRAGMENTS - ANOTHER AI TELL:**
AI loves short dramatic fragments at the start. Humans write complete sentences.

✗ "50 nodes. 6 hours of my time. An AI agent rebuilt it."
✓ "I spent 6 hours building a 50-node workflow."
"""

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

**WHERE PROOF CAN COME FROM:**
1. **TOPIC/CONTEXT** - User explicitly provided: "Alex 500→5k subs", "workshop with 50+ creators"
2. **WEB SEARCH RESULTS** - Verified via web_search tool (future): industry benchmarks
3. **RAG/DATABASE** - Retrieved from user's past content, case studies (future)

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
❌ Rule of Three: "Same X. Same Y. Over Z%." (three parallel fragments)
❌ Staccato fragments: "500 subs. 3 months. One change." (AI loves dramatic fragments)

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

QUALITY_CHECK_PROMPT = dedent("""You are evaluating a YouTube video script. Your job: determine if this hooks viewers and keeps them watching.

Script to evaluate:
{post}

Evaluate on these axes (0-5):

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

**AI TELLS TO FLAG:**
- Contrast framing ("It's not X, it's Y")
- Rule of Three (three parallel fragments)
- Staccato fragments ("500 subs. 3 months. One change.")

**VERIFICATION CHECK:**
Use web_search tool to verify specific claims:
- Creator names + growth numbers (e.g., "Alex 500→5k")
- Workshop/event details (e.g., "50+ creators")
- News stories, events, product launches: "Rick Beato YouTube AI filters"
- Industry data/timeframes (e.g., "3 months to 5k subs")

If verified → Note as "verified claim"
If NOT verified:
  * Personal anecdotes/client stories → FLAG AS "NEEDS VERIFICATION" (severity: medium)
  * News reporting/industry events → FLAG AS "ADD SOURCE CITATION" (severity: low, suggest adding link)
  * Only flag as "FABRICATED" if claim is clearly false or contradicts verified info

**TIMING ACCURACY CHECK:**
- Verify timing markers are present
- Check if timing adds up (sum of sections = total duration)
- Verify word count matches estimated duration (2.5 words/sec)

Output JSON:
{{
  "scores": {{
    "hook_power": 4,
    "pattern_interrupt": 3,
    "script_flow": 5,
    "proof_density": 2,
    "cta_payoff": 4,
    "total": 18
  }},
  "timing_accuracy": {{
    "has_markers": true,
    "sections_add_up": true,
    "word_count_matches": true
  }},
  "decision": "revise",  // "accept" (≥20) | "revise" (18-19) | "reject" (<18)
  "issues": [
    {{
      "axis": "proof_density",
      "severity": "high",
      "problem": "Only one vague number, need 2+ specific from user context",
      "fix": "Add concrete examples from TOPIC/CONTEXT (e.g., 'Alex 500→5k', '50+ creators')"
    }}
  ],
  "surgical_summary": "2 fixes needed: Add specific proof points from user context (high priority), tighten pattern interrupt with surprising stat (medium priority)"
}}
""")

# ==================== APPLY FIXES ====================

APPLY_FIXES_PROMPT = dedent("""You are fixing a YouTube script based on quality feedback. Your job: apply 3-5 surgical fixes without rewriting the whole script.

Original Script:
{post}

Issues from quality_check:
{issues_json}

CRITICAL RULES:

0. **WRITE LIKE A HUMAN** - You must follow these rules when applying fixes:

{write_like_human_rules}

1. **BE SURGICAL** - Fix ONLY what's listed in issues
   - Don't rewrite sentences that aren't broken
   - Don't change the cadence or spoken rhythm
   - Make minimal edits to raise the score

2. **PRESERVE STRENGTHS**:
   - ✅ KEEP specific names/numbers from original (from user context)
   - ✅ KEEP conversational tone and spoken cadence
   - ✅ KEEP short sentences for breath control
   - ✅ KEEP line breaks for natural pauses
   - ✅ KEEP timing markers (adjust if word count changes)
   - ❌ DO NOT water down to vague language
   - ❌ DO NOT make it more formal or written

3. **APPLY FIXES BY SEVERITY**:
   - Severity "high" → Must fix (raises score significantly)
   - Severity "medium" → Fix if it doesn't hurt specificity
   - Severity "low" → Skip unless obviously wrong

4. **EXAMPLES OF SURGICAL FIXES**:
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

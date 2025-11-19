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
from integrations.prompt_loader import load_editor_standards, load_writing_rules, load_prompt

EDITOR_IN_CHIEF_RULES = load_editor_standards()
WRITE_LIKE_HUMAN_RULES = load_writing_rules()

# ==================== GENERATE 5 HOOKS ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/youtube/generate_hooks.md

GENERATE_HOOKS_PROMPT = load_prompt("generate_hooks", platform="youtube")

# ==================== INJECT PROOF POINTS ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/youtube/inject_proof.md

INJECT_PROOF_PROMPT = load_prompt("inject_proof", platform="youtube")

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
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/youtube/quality_check.md

_quality_check_template = load_prompt("quality_check", platform="youtube")
QUALITY_CHECK_PROMPT = _quality_check_template.replace(
    "{{EDITOR_IN_CHIEF_RULES}}",
    EDITOR_IN_CHIEF_RULES
)

# ==================== APPLY FIXES ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/youtube/apply_fixes.md

_apply_fixes_template = load_prompt("apply_fixes", platform="youtube")
APPLY_FIXES_PROMPT = _apply_fixes_template.replace(
    "{write_like_human_rules}",
    WRITE_LIKE_HUMAN_RULES
)

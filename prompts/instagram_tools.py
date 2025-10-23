"""
Instagram Tool Prompts - Lazy Loaded
Detailed prompts stored here to minimize SDK context window usage.
Only loaded when tools are actually called.

Instagram-specific adaptations:
- 2,200 character limit (HARD CAP)
- First 125 characters critical (preview before "...more")
- Visual pairing emphasis (assumes accompanying image/Reel)
- Emoji + line break formatting
- Hashtag strategy (3-5 tags)
"""

from textwrap import dedent

# ==================== GLOBAL WRITING RULES (REUSED FROM LINKEDIN) ====================
# Import the same WRITE_LIKE_HUMAN_RULES to maintain consistency across platforms
from prompts.linkedin_tools import WRITE_LIKE_HUMAN_RULES

# ==================== GENERATE 5 HOOKS (INSTAGRAM-OPTIMIZED) ====================

GENERATE_HOOKS_PROMPT = dedent("""Generate EXACTLY 5 Instagram hooks for this topic, one for each type:

Topic: {topic}
Context: {context}
Target Audience: {audience}

CRITICAL INSTAGRAM CONSTRAINT: First 125 characters appear above "...more" button.
The hook MUST work standalone within this preview.

HOOK TYPES (one of each):

1. QUESTION HOOK (under 125 chars)
   - Specific question that makes them tap "...more"
   - Include number or specific detail
   Example: "What if I told you 12 hours/week disappear doing tasks that take 12 minutes?" (82 chars)

2. BOLD STATEMENT HOOK (under 125 chars)
   - Contrarian or surprising claim
   - No setup needed, direct impact
   Example: "Nobody talks about this productivity hack." (49 chars)

3. STAT HOOK (under 125 chars)
   - Lead with specific number
   - Create curiosity gap
   Example: "95% of founders don't know this about fundraising" (56 chars)

4. STORY HOOK (under 125 chars)
   - Personal experience with specific detail
   - Tease the lesson
   Example: "I spent $50K learning this the hard way:" (48 chars)

5. MISTAKE HOOK (under 125 chars)
   - Common error + why it matters
   - Create urgency
   Example: "Stop optimizing your funnel. Here's why:" (48 chars)

RULES:
✗ NO contrast framing ("It's not X, it's Y")
✗ NO generic statements ("This is important")
✗ NO cringe questions ("The truth?" / "Sound familiar?")
✗ NO buzzwords (game-changer, revolutionary, unlock)

Return JSON array: {json_example}

For Instagram, prioritize hooks that:
- Create visual curiosity (references image without describing it)
- Use emojis strategically (1 emoji max in hook)
- Work in 125-char preview window
""")

# ==================== CREATE CAPTION DRAFT ====================

CREATE_CAPTION_DRAFT_PROMPT = dedent("""
You are writing an Instagram caption. Your job: create content that stops the scroll and drives engagement.

{write_like_human_rules}

INSTAGRAM-SPECIFIC CONSTRAINTS:

1. CHARACTER LIMIT: 2,200 characters MAXIMUM (HARD LIMIT)
   - Instagram truncates at exactly 2,200
   - Leave room for hashtags (count toward limit)

2. PREVIEW OPTIMIZATION: First 125 characters appear before "...more"
   - Must work as standalone hook
   - Create curiosity gap to tap "more"
   - Don't waste space on setup

3. VISUAL PAIRING: Caption assumes accompanying image/video
   - Reference "this", "above", "swipe" when relevant
   - Add context the visual can't show (backstory, data, lesson)
   - DON'T describe what's obvious in the image

4. FORMATTING FOR MOBILE:
   - Line break every 2-3 sentences (readability)
   - Use bullets or numbered lists for steps
   - 1-2 strategic emojis (not emoji spam)
   - Short paragraphs (2-3 lines max)

5. HASHTAG STRATEGY:
   - 3-5 relevant hashtags at END of caption
   - Mix: 1 popular (#Productivity), 2 niche (#B2BSaaS), 1 branded
   - Hashtags COUNT toward 2,200 char limit

INSTAGRAM SCORING AXES (0-5 each, total 25):

1. HOOK (First 125 chars before "...more")
   Score 5: Specific stat/question/story + curiosity gap
   Score 3: Generic hook ("Check this out")
   Score 0: Wasted preview space

2. VISUAL PAIRING (How well caption complements image/video)
   Score 5: Adds context visual can't show + references visual naturally
   Score 3: Generic caption (works without image)
   Score 0: Repeats what's obvious in visual

3. READABILITY (Mobile formatting)
   Score 5: Line breaks every 2-3 sentences + emojis + bullets/numbers
   Score 3: Some line breaks but walls of text
   Score 0: Dense paragraph, no formatting

4. PROOF & SPECIFICITY
   Score 5: Multiple specific numbers/dates/names from context
   Score 3: One vague claim
   Score 0: No proof, generic statements

5. CTA + HASHTAGS
   Score 5: Specific engagement trigger + 3-5 strategic hashtags
   Score 3: Weak CTA ("thoughts?") or missing hashtags
   Score 0: No CTA or hashtag spam

TOPIC: {topic}
HOOK (use exactly): {hook}
CONTEXT: {context}

TASK: Write an Instagram caption optimized for mobile, under 2,200 characters.

Return ONLY the caption text (no metadata, no explanations).
Include hashtags at the end.
Use line breaks for readability.
""")

# ==================== CONDENSE TO LIMIT ====================

CONDENSE_TO_LIMIT_PROMPT = dedent("""You are condensing an Instagram caption to fit the 2,200 character limit.

CURRENT CAPTION ({current_length} chars):
{caption}

TARGET: {target_length} characters (2,200 max, leaving buffer)

CONDENSING STRATEGY (Nicolas Cole's "Caption Condenser"):
1. KEEP:
   - Hook (first 125 chars)
   - Key numbers/proof points
   - Call-to-action
   - Hashtags

2. REMOVE:
   - Redundant phrasing
   - Extra examples (keep best 1-2)
   - Transition words
   - Setup that hook already covered

3. TIGHTEN:
   - "in order to" → "to"
   - "the reason why" → "why"
   - "in the event that" → "if"
   - Multiple clauses → Short sentences

RULES:
✓ Preserve voice and emotional impact
✓ Keep specific numbers and names
✓ Maintain line breaks for readability
✗ Don't change hook (first 125 chars)
✗ Don't remove CTA or hashtags

Return the condensed caption only (no explanations).
Target: {target_length} characters or less.
""")

# ==================== QUALITY CHECK ====================

QUALITY_CHECK_PROMPT = dedent("""You are evaluating an Instagram caption. Your job: determine if this stops the scroll or gets skipped.

CAPTION TO EVALUATE:
{post}

EVALUATION CRITERIA (5 axes, 0-5 points each):

1. HOOK STRENGTH (First 125 chars before "...more")
   5 points: Specific number/question/story + curiosity gap + under 125 chars
   4 points: Good hook but over 125 chars (gets cut off)
   3 points: Generic hook ("Check this out")
   2 points: Weak or boring
   0 points: No hook or wasted preview

2. VISUAL PAIRING (Assumes image/Reel context)
   5 points: Adds backstory/data/lesson visual can't show + natural references ("swipe", "above")
   4 points: Complements visual well
   3 points: Generic (works without visual)
   2 points: Describes what's obvious in image
   0 points: Contradicts or ignores visual context

3. READABILITY (Mobile formatting)
   5 points: Line breaks every 2-3 sentences + strategic emojis + bullets/numbers + short paragraphs
   4 points: Good formatting, minor issues
   3 points: Some line breaks but has walls of text
   2 points: Minimal formatting
   0 points: Dense paragraph, no breaks

4. PROOF & SPECIFICITY
   5 points: Multiple specific numbers/dates/names (verifiable)
   4 points: 2 specific data points
   3 points: 1 data point
   2 points: Vague claims
   0 points: No proof, all generic

5. CTA + HASHTAGS
   5 points: Specific engagement trigger ("Comment START for template") + 3-5 strategic hashtags
   4 points: Good CTA + hashtags
   3 points: Weak CTA ("thoughts?") OR missing hashtags
   2 points: Generic CTA ("DM me")
   0 points: No CTA or hashtag spam (10+)

AI TELL DETECTION (auto-deduct 2 points each):
-2 pts: Contrast framing ("It's not X, it's Y")
-2 pts: Rule of three ("Same X. Same Y. Over Z%.")
-2 pts: Cringe questions ("The truth?" / "Sound familiar?")
-2 pts: Buzzwords (game-changer, unlock, revolutionary, leverage)

FABRICATION CHECK (use web_search tool):
- Search any specific claims (names, companies, stats)
- If unverifiable, mark severity="critical" in issues
- Don't block post, but flag for user review

RETURN FORMAT (JSON):
{{
  "scores": {{
    "hook": 4,
    "visual_pairing": 5,
    "readability": 4,
    "proof": 5,
    "cta_hashtags": 4,
    "ai_deductions": -2,
    "total": 20
  }},
  "decision": "accept",  # accept (≥20), revise (18-19), reject (<18)
  "issues": [
    {{
      "axis": "hook",
      "severity": "high",  # critical/high/medium/low
      "original": "Check this out...",
      "fix": "What if 12 hours/week vanish on 12-minute tasks?",
      "impact": "+2 pts (creates curiosity gap, under 125 chars)"
    }}
  ],
  "searches_performed": ["Nike air max release date", ...],
  "character_count": 1847,
  "character_limit": 2200,
  "preview_length": 124  # first 125 chars check
}}

Run web searches for any specific claims. Flag fabrications as severity="critical".
Return JSON only.
""")

# ==================== APPLY FIXES ====================

APPLY_FIXES_PROMPT = dedent("""You are fixing an Instagram caption based on quality feedback. Your job: apply 3-5 surgical fixes without rewriting the whole caption.

{write_like_human_rules}

ORIGINAL CAPTION:
{post}

QUALITY ISSUES (from quality_check):
{issues_json}

FIXING STRATEGY:

1. PRIORITIZE CRITICAL FIXES FIRST:
   - Fabrications (flag for user, don't invent)
   - Character limit violations (condense)
   - Hook over 125 chars (trim preview)
   - AI tells (contrast framing, rule of three)

2. SURGICAL EDITS (don't rewrite whole caption):
   - Replace specific phrases only
   - Preserve voice and emotional language
   - Keep all numbers/names/specifics
   - Maintain line break formatting

3. INSTAGRAM-SPECIFIC FIXES:
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
""")

# ==================== VALIDATE FORMAT ====================

VALIDATE_FORMAT_PROMPT = dedent("""Check this Instagram caption against ALL Instagram format rules.

CAPTION:
{post}

INSTAGRAM FORMAT CHECKLIST:

1. CHARACTER LIMIT:
   ✓ Under 2,200 characters (hard limit)
   ✗ Over 2,200 (gets truncated)

2. PREVIEW OPTIMIZATION:
   ✓ First 125 chars work as standalone hook
   ✓ Ends mid-sentence or with :... to create gap
   ✗ Preview wastes space or gives everything away

3. MOBILE READABILITY:
   ✓ Line breaks every 2-3 sentences
   ✓ Short paragraphs (2-3 lines)
   ✓ Bullets or numbers for lists
   ✗ Walls of text (hard to scan)

4. EMOJI USAGE:
   ✓ 1-2 strategic emojis (section breaks, emphasis)
   ✗ Emoji spam (every line, decorative only)
   ✗ No emojis (misses engagement opportunity)

5. HASHTAG PLACEMENT:
   ✓ 3-5 relevant hashtags at END
   ✓ Mix of popular and niche tags
   ✗ Hashtag spam (10+ tags)
   ✗ Hashtags mid-caption (breaks flow)
   ✗ Missing hashtags (loses discoverability)

6. CTA PLACEMENT:
   ✓ Clear engagement trigger before hashtags
   ✓ Specific action ("Comment START", "Tag someone who...")
   ✗ Passive CTA ("Link in bio", "DM me")
   ✗ Missing CTA

Return structured feedback with violations and recommendations.
""")

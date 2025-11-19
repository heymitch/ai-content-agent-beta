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

# ==================== LOAD WRITING RULES AND EDITOR STANDARDS ====================
# NEW: Load from external .md files with client override support
# Clients can customize these by creating .claude/prompts/writing_rules.md or editor_standards.md
# Fallback to versioned defaults in prompts/styles/default_writing_rules.md
from integrations.prompt_loader import load_editor_standards, load_writing_rules, load_prompt

EDITOR_IN_CHIEF_RULES = load_editor_standards()
WRITE_LIKE_HUMAN_RULES = load_writing_rules()

# ==================== GENERATE 5 HOOKS (INSTAGRAM-OPTIMIZED) ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/instagram/generate_hooks.md

GENERATE_HOOKS_PROMPT = load_prompt("generate_hooks", platform="instagram")

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
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/instagram/condense_to_limit.md

CONDENSE_TO_LIMIT_PROMPT = load_prompt("condense_to_limit", platform="instagram")

# ==================== QUALITY CHECK ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/instagram/quality_check.md

_quality_check_template = load_prompt("quality_check", platform="instagram")
QUALITY_CHECK_PROMPT = _quality_check_template.replace(
    "{{EDITOR_IN_CHIEF_RULES}}",
    EDITOR_IN_CHIEF_RULES
)

# ==================== APPLY FIXES ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/instagram/apply_fixes.md

_apply_fixes_template = load_prompt("apply_fixes", platform="instagram")
APPLY_FIXES_PROMPT = _apply_fixes_template.replace(
    "{write_like_human_rules}",
    WRITE_LIKE_HUMAN_RULES
)

# ==================== VALIDATE FORMAT ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/instagram/validate_format.md

VALIDATE_FORMAT_PROMPT = load_prompt("validate_format", platform="instagram")

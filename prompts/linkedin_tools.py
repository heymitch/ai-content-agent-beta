"""
LinkedIn Tool Prompts - Lazy Loaded
Detailed prompts stored here to minimize SDK context window usage.
Only loaded when tools are actually called.
"""

from pathlib import Path
from textwrap import dedent
import sys

# Add parent to path for prompt_loader import
sys.path.insert(0, str(Path(__file__).parent.parent))

# ==================== LOAD EDITOR-IN-CHIEF STANDARDS ====================
# Load comprehensive Editor-in-Chief standards for quality_check
# Now uses PromptLoader with client override support (.claude/prompts/)
from integrations.prompt_loader import load_editor_standards, load_writing_rules

EDITOR_IN_CHIEF_RULES = load_editor_standards()
WRITE_LIKE_HUMAN_RULES = load_writing_rules()

# Note: Writing rules now loaded from prompts/styles/default_writing_rules.md
# Clients can override by creating .claude/prompts/writing_rules.md

# ==================== GENERATE 5 HOOKS ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/linkedin/generate_hooks.md

GENERATE_HOOKS_PROMPT = load_prompt("generate_hooks", platform="linkedin")

# ==================== INJECT PROOF POINTS ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/linkedin/inject_proof.md

INJECT_PROOF_PROMPT = load_prompt("inject_proof", platform="linkedin")

# ==================== CREATE HUMAN DRAFT ====================
# Load draft prompt template (with client override support)
# Clients can customize by creating .claude/prompts/linkedin/create_draft.md
from integrations.prompt_loader import load_prompt

print("🔍 DEBUG: About to load create_draft prompt for LinkedIn...")
_draft_template = load_prompt("create_draft", platform="linkedin")
print(f"🔍 DEBUG: Loaded create_draft template ({len(_draft_template)} chars)")

# Inject writing rules into the template
CREATE_HUMAN_DRAFT_PROMPT = _draft_template.replace(
    "{{WRITE_LIKE_HUMAN_RULES}}",
    WRITE_LIKE_HUMAN_RULES
)

# ==================== DETECT AI CRINGE ====================

DETECT_AI_CRINGE_PROMPT = dedent("""You are an AI pattern hunter. Find EVERY instance of AI-sounding language in this post.

Post: {post}

HUNT FOR (be ULTRA aggressive - flag ANY occurrence of these words/structures):

**CONTRAST WORDS (flag if ANY of these appear):**
- isn't / is not / aren't / are not
- not / don't / doesn't / won't / can't
- just / only / merely / simply
- but / however / yet / though / although
- instead / rather / versus / vs
- difference / real / true / actual

If you see phrases like:
- "The difference isn't X"
- "It's not about X"
- "This isn't X, it's Y"
- "X isn't the answer"
- "Not just X, but Y"
- "The real X is..."
- "What really matters..."

→ FLAG IT. These are masked contrasts that sound preachy.

**FORMULAIC SECTION HEADERS (flag ANY of these):**
- "The process:"
- "The result:"
- "The results:"
- "The difference:"
- "The truth:"
- "The reality:"
- "The breakdown:"
- "The catch:"
- "The problem:"
- "The solution:"
- "Backstory:"
- "Context:"
- "Here's the thing:"
- "Here's why:"
- "Here's what:"
- "Here's how:"

→ These are lazy transitions. Real humans say "What happened next:" or just tell the story.

**CRINGE QUESTIONS:**
- "Sound familiar?"
- "Want to know?"
- "Can you relate?"
- "Does this resonate?"
- "What if I told you?"
- "Curious?"
- "Wonder why?"

**AI TIPOFF PHRASES:**
- "In today's landscape"
- "As we navigate"
- "Moreover" / "Furthermore" / "Additionally"
- "Let that sink in"
- "Think about it"
- "At the end of the day"

**HASHTAGS:**
- Any hashtags at all (#BuildInPublic, #SaaS, etc.)
→ Remove ALL hashtags. Real LinkedIn pros don't use them.

**FAKE PROFUNDITY:**
- "Most people don't realize"
- "What people miss is"
- "The key insight"
- "What nobody tells you"

**VAGUE CTAs:**
- "DM me to learn more"
- "Follow for more"
- "Link in bio"
- "Comment if you agree"

RETURN FORMAT (JSON array):
[
  {{
    "original": "exact phrase from post",
    "reason": "contrast_word / section_header / hashtags / etc",
    "replacement": "natural alternative (for hashtags: delete them entirely)"
  }}
]

BE ULTRA AGGRESSIVE. The LLM understands semantic meaning - it will find these patterns even when masked. Flag ANYTHING that smells like a formula or contrast structure.

Return empty array [] only if post is 100% clean with ZERO patterns found.
""")

# ==================== APPLY AI FIXES ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/linkedin/apply_fixes.md

_apply_fixes_template = load_prompt("apply_fixes", platform="linkedin")

# Inject writing rules into the template
APPLY_FIXES_PROMPT = _apply_fixes_template.replace(
    "{write_like_human_rules}",
    WRITE_LIKE_HUMAN_RULES
)

# ==================== VALIDATE FORMAT ====================

VALIDATE_FORMAT_PROMPT = dedent("""Check this LinkedIn post against ALL checklist format rules.

Post: {post}
Type: {post_type}

CHECKLIST (mark each with ✓ or ✗):

**HOOK & OPENING (First 200 chars):**
□ Ends with cliffhanger (?, :, ..., mid-sentence)
□ Line break immediately after hook (CRITICAL for mobile)
□ Hook under 200 chars
□ First 150 chars compelling on mobile preview

**STRUCTURE & WHITE SPACE:**
□ Paragraphs are 1-2 sentences max
□ White space between every section
□ Uses line breaks for readability
□ No walls of text

**HEADERS (if applicable):**
□ Headers are tangible (Step 1: / Item #1: / Stat 1: format)
□ NOT vague ("Here's what I learned")
□ Each header delivers on hook's promise

**ENGAGEMENT:**
□ Ends with ONE clear CTA
□ CTA is active (question/request/comment bait)
□ NOT generic ("DM me" / "Follow for more")

**MOBILE FORMATTING:**
□ First 150 chars strong (mobile preview test)
□ Max 3 emojis total
□ Hashtags: 3-5 only, at END
□ No lines over 3 sentences

**LENGTH:**
□ Short: 50-120 words (~300-450 chars)
□ Standard: 200-450 words (~1200-2200 chars)
□ Under 2800 char limit

Return validation results as:
{{
  "passes": true/false,
  "score": 0-100,
  "violations": ["list of specific issues"],
  "fixed_post": "corrected version if violations found"
}}
""")

# ==================== SCORE AND ITERATE ====================

SCORE_ITERATE_PROMPT = dedent("""Grade this LinkedIn post against the complete checklist rubric.

Post: {draft}
Target Score: {target_score}
Current Iteration: {iteration}

SCORING RUBRIC (100 points total):

**HOOK QUALITY (20 points)**
- Cliffhanger ending (10 pts)
- Under 200 chars (5 pts)
- Line break after hook (5 pts)

**PROOF & SPECIFICITY (25 points)**
- Specific numbers with WHO (10 pts)
- Before/after with dates (8 pts)
- Real examples named (7 pts)

**FORMAT & READABILITY (20 points)**
- 1-2 sentence paragraphs (8 pts)
- White space between sections (6 pts)
- Mobile-first formatting (6 pts)

**VALUE & CLARITY (20 points)**
- Clear takeaways (10 pts)
- Actionable insights (10 pts)

**ENGAGEMENT TRIGGER (15 points)**
- Strong CTA present (8 pts)
- Active engagement type (7 pts)

DEDUCTIONS:
- AI patterns found: -10 pts each
- Vague language: -5 pts
- Generic CTA: -8 pts
- Missing WHO in examples: -7 pts

Return as JSON:
{{
  "score": 0-100,
  "breakdown": {{"hook": X, "proof": Y, ...}},
  "ready_to_post": true/false,
  "improvements_needed": ["specific fixes if score < target"],
  "revised_draft": "improved version if score < target (null if ready)"
}}
""")

# ==================== QUALITY CHECK (COMBINED: AI CRINGE + FACT CHECK) ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/linkedin/quality_check.md

_quality_check_template = load_prompt("quality_check", platform="linkedin")

# Inject editor-in-chief rules into the template
QUALITY_CHECK_PROMPT = _quality_check_template.replace(
    "{{EDITOR_IN_CHIEF_RULES}}",
    EDITOR_IN_CHIEF_RULES
)

# ==================== CREATE CAROUSEL SLIDES ====================

CREATE_CAROUSEL_PROMPT = dedent("""Create a 7-slide LinkedIn carousel using the proven structure.

Topic: {topic}
Context: {context}

MANDATORY 7-SLIDE STRUCTURE:

**Slide 1: PROMISE** (Hook slide)
- Title: Bold promise/outcome
- Subtitle: Who this is for
- 30 words max

**Slide 2: STAKES** (Why you should care)
- Title: The problem/cost of inaction
- 3 bullets of pain points
- 30 words max

**Slide 3-5: FRAMEWORK** (The how-to)
- Each slide: 1 step/concept
- Title + 3-4 bullets
- Keep it scannable
- 30 words per slide max

**Slide 6: EXAMPLE** (Proof it works)
- Real example or case study
- Specific numbers
- Before/after format
- 30 words max

**Slide 7: CTA** (What to do next)
- Clear next action
- Benefit of taking action
- No generic "Follow me"
- 25 words max

DESIGN GUIDELINES:
- Large, bold headlines
- 3-4 bullets max per slide
- Contrasting colors
- Lots of white space
- Emoji for visual breaks (optional)

Return as JSON:
{{
  "slides": [
    {{"number": 1, "title": "...", "content": "...", "design_notes": "..."}},
    ...
  ],
  "total_slides": 7
}}
""")

# ==================== SEARCH VIRAL PATTERNS ====================

SEARCH_VIRAL_PATTERNS_PROMPT = dedent("""Analyze viral LinkedIn posts in this niche to find patterns.

Topic/Niche: {topic}
Industry: {industry}

SEARCH FOR PATTERNS IN:
1. **Hook styles** that get engagement
2. **Content structures** that perform
3. **CTAs** that drive comments
4. **Proof formats** (stats, stories, screenshots)
5. **Post lengths** that work

ANALYZE:
- What makes people stop scrolling?
- What triggers "See more" clicks?
- What prompts comments vs just likes?
- What formats get shared?

Return research findings as JSON:
{{
  "top_hooks": ["patterns found"],
  "winning_structures": ["format types"],
  "engagement_triggers": ["what works"],
  "examples": [
    {{"hook": "...", "engagement_reason": "why it worked"}}
  ]
}}

Note: This would ideally search real LinkedIn posts. For now, return best practices based on known patterns.
""")

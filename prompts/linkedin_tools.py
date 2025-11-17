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

GENERATE_HOOKS_PROMPT = dedent("""Generate EXACTLY 5 LinkedIn hooks for this topic, one for each type:

Topic: {topic}
Context: {context}
Target Audience: {audience}

MANDATORY FORMATS (from checklist):
1. Question (provokes curiosity)
2. Bold statement (counterintuitive)
3. Specific number/stat
4. Short story opener
5. Mistake/lesson framing

Each hook must:
- Be under 200 characters
- Create a cliffhanger for "See more"
- Target the specific audience
- Be direct and punchy

Return as JSON array with format:
{json_example}
""")

# ==================== INJECT PROOF POINTS ====================

INJECT_PROOF_PROMPT = dedent("""{write_like_human_rules}

=== INJECT PROOF POINTS ===

Review this draft and ONLY add proof from verified sources.

Draft: {draft}
Topic: {topic}
Industry: {industry}

**COMPANY DOCUMENTS SEARCH RESULTS:**
{proof_context}

**WHERE PROOF CAN COME FROM:**
1. **TOPIC/CONTEXT** - User explicitly provided: "6 hours → 10 minutes", "March 2024", "50 nodes"
2. **WEB SEARCH RESULTS** - Verified via web_search tool (future): company metrics, industry benchmarks
3. **COMPANY DOCUMENTS** - Retrieved from user-uploaded docs (case studies, testimonials, product docs) - SEE ABOVE

**CRITICAL: DO NOT FABRICATE**
- ❌ Making up dollar amounts: "$1,050", "$29"
- ❌ Inventing percentages: "97.2% reduction", "34% faster"
- ❌ Fabricating case studies: "12 client workflows", "tested across X companies"
- ❌ Creating fake names: "Sarah", "James Chen", "my colleague at X"
- ❌ Citing stats you don't have: "Gartner reported", "industry average of 4.3 hours"

**WHAT YOU CAN DO:**
- ✅ Use metrics from TOPIC: "6 hours vs 10 minutes" → Calculate: "~97% time reduction"
- ✅ Add context from TOPIC: "50 nodes" → "complex 50-node workflow"
- ✅ Use dates from TOPIC: "March 2024" → "Earlier this year in March 2024"
- ✅ Add verified web search results (when tool provides them)
- ✅ Add RAG-retrieved testimonials (when database provides them)

**DEFAULT BEHAVIOR:**
- If NO additional proof available → Return draft with MINIMAL changes
- Better to have NO proof than FAKE proof

**ROADMAP NOTE:**
In future iterations, this tool will receive:
- web_search results with verified industry stats
- RAG-retrieved real case studies from user's database
- Actual testimonials from user's clients

For now: ONLY use what's explicitly in TOPIC. Do NOT invent metrics.

Return the enhanced draft only (plain text, NO markdown formatting like **bold** or *italic*).
""")

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

APPLY_FIXES_PROMPT = dedent("""You are fixing a LinkedIn post based on quality feedback.

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
{{
  "revised_post": "...",
  "changes_made": [
    {{
      "issue_addressed": "audience_generic",
      "original": "founders",
      "revised": "seed-stage B2B SaaS founders stuck at <$1M ARR",
      "impact": "Raises audience score from 2 to 5"
    }}
  ],
  "estimated_new_score": 21,
  "notes": "Fixed ALL flagged issues. Preserved specifics and emotional punch. Rewrote GPTZero flagged sentences."
}}

Fix ALL issues - no limit. Every flagged pattern and GPTZero sentence must be addressed.

IMPORTANT: Output plain text only. NO markdown formatting (**bold**, *italic*, ##headers).
""")

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

QUALITY_CHECK_PROMPT = """You are evaluating a LinkedIn post using Editor-in-Chief standards.

═══════════════════════════════════════════════════════════════
EDITOR-IN-CHIEF STANDARDS (READ THESE COMPLETELY):
═══════════════════════════════════════════════════════════════

""" + EDITOR_IN_CHIEF_RULES + """

═══════════════════════════════════════════════════════════════
END OF EDITOR-IN-CHIEF STANDARDS
═══════════════════════════════════════════════════════════════

YOUR TASK:
1. Read the post below
2. Scan sentence-by-sentence for EVERY violation listed in Editor-in-Chief standards above
3. Create ONE surgical issue per violation found
4. Use EXACT replacement strategies from the standards (don't make up your own)

Post to evaluate:
{post}

WORKFLOW:

STEP 1: SCAN FOR VIOLATIONS
Go through the post line-by-line and find:
- Direct contrast formulations ("This isn't about X—it's about Y", "It's not X, it's Y", "Rather than X")
- Masked contrast patterns ("Instead of X", "but rather")
- Formulaic headers (ANY case):
  * "The X:" pattern → "The promise:", "The reality:", "The result:", "The truth:", "The catch:", "The process:", "The best part:"
  * "HERE'S HOW:", "HERE'S WHAT:", Title Case In Headings
  * These are AI tells - convert to natural language or delete
- Short questions (<8 words ending in "?"):
  * "For me?" → Delete or expand to statement: "For me, the ability to..."
  * "The truth?" → Delete entirely
  * "What happened?" → Expand: "What did the data show after 30 days?"
  * Count words - if <8 words AND ends with "?", it's a violation
- Section summaries ("In summary", "In conclusion")
- Promotional puffery ("stands as", "testament", "rich heritage")
- Overused conjunctions ("moreover", "furthermore")
- Vague attributions ("industry reports says" without source)
- Em-dash overuse (multiple — in formulaic patterns)
- Words needing substitution ("leverages", "encompasses", "facilitates")

STEP 2: CREATE SURGICAL ISSUES
For EACH violation found, create ONE issue:
{{
  "axis": "ai_tells",
  "severity": "high" | "medium" | "low",
  "pattern": "contrast_direct" | "contrast_masked" | "title_case" | "formulaic_header" | "cringe_question" | "puffery" | "word_substitution",
  "original": "[EXACT text from post - word-for-word quote]",
  "fix": "[EXACT replacement using Editor-in-Chief examples - don't paraphrase]",
  "impact": "[How this improves the post]"
}}

EXAMPLES:

Formulaic header violation:
{{
  "axis": "ai_tells",
  "severity": "high",
  "pattern": "formulaic_header",
  "original": "The promise:",
  "fix": "Self-hosting promises",
  "impact": "Removes AI tell pattern, makes header natural"
}}

Short question violation:
{{
  "axis": "ai_tells",
  "severity": "high",
  "pattern": "cringe_question",
  "original": "For me?",
  "fix": "For me, the ability to",
  "impact": "Removes 2-word cringe question, converts to statement"
}}

STEP 3: USE REPLACEMENT STRATEGIES FROM STANDARDS
When creating fixes, use the EXACT patterns from Editor-in-Chief standards:

For contrast framing:
❌ "Success isn't about working harder but working smarter."
✅ "Success comes from working smarter and more strategically."

For formulaic headers "The X:":
❌ "The promise:" / "The reality:" / "The catch:" / "The result:"
✅ Convert to natural sentence: "Self-hosting promises" / "Reality showed" / "Here's the trade-off" / "We saw"

For short questions (<8 words):
❌ "For me?" → ✅ DELETE or "For me, the ability to"
❌ "The truth?" → ✅ DELETE entirely
❌ "What happened?" → ✅ "What did the data show after 30 days?"
Rule: If question is <8 words, either DELETE or expand to 8+ word specific question

For word substitutions:
leverages → uses
encompasses → includes
facilitates → enables
utilized → used

STEP 4: SCORE THE POST
Hook (0-5): Framework + specific + cliffhanger?
Audience (0-5): Role + stage + problem?
Headers (0-5): Tangible metrics/outcomes?
Proof (0-5): Concrete numbers?
CTA (0-5): Specific engagement trigger?

Deduct 2 points per major AI tell (contrast framing, rule of three, etc).

STEP 5: VERIFY FACTS (use web_search)
Search for:
- Names and companies mentioned
- News events and claims
- Statistics and data points

If NOT verified: flag as "NEEDS VERIFICATION" or "ADD SOURCE CITATION"
Only use "FABRICATED" if provably false.

CRITICAL RULES:
✅ Create ONE issue per violation (8 violations = 8 issues)
✅ Quote EXACT text from post in "original"
✅ Use EXACT fixes from Editor-in-Chief standards (don't improvise)
✅ Be comprehensive - find EVERY violation

Output JSON:
{{
  "scores": {{
    "hook": 3,
    "audience": 2,
    "headers": 4,
    "proof": 5,
    "cta": 4,
    "total": 18,
    "ai_deductions": -6
  }},
  "decision": "revise",
  "searches_performed": ["query 1", "query 2"],
  "issues": [
    {{
      "axis": "ai_tells",
      "severity": "high",
      "pattern": "contrast_direct",
      "original": "[exact quote from post]",
      "fix": "[exact fix from Editor-in-Chief examples]",
      "impact": "[specific improvement]"
    }}
  ],
  "surgical_summary": "Found [number] violations across [patterns]. Applying all fixes would raise score from [current] to [projected].",
  "threshold": 20,
  "meets_threshold": false
}}

Be thorough. Find EVERY violation. Use Editor-in-Chief examples EXACTLY as written.
"""

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

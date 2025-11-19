"""
Email Tool Prompts - Lazy Loaded
Detailed prompts stored here to minimize SDK context window usage.
Only loaded when tools are actually called.
Adapted from LinkedIn SDK Agent for email newsletters.
"""

from textwrap import dedent
from tools.pattern_matching import format_email_examples_for_prompt

# ==================== LOAD WRITING RULES AND EDITOR STANDARDS ====================
# NEW: Load from external .md files with client override support
# Clients can customize these by creating .claude/prompts/writing_rules.md or editor_standards.md
# Fallback to versioned defaults in prompts/styles/default_writing_rules.md
from integrations.prompt_loader import load_editor_standards, load_writing_rules, load_prompt

EDITOR_IN_CHIEF_RULES = load_editor_standards()
WRITE_LIKE_HUMAN_RULES = load_writing_rules()

# ==================== GENERATE 5 HOOKS ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/email/generate_hooks.md

GENERATE_HOOKS_PROMPT = load_prompt("generate_hooks", platform="email")

# ==================== INJECT PROOF POINTS ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/email/inject_proof.md

INJECT_PROOF_PROMPT = load_prompt("inject_proof", platform="email")

# ==================== CREATE HUMAN DRAFT ====================

# Load PGA email examples for writing style training
EMAIL_VALUE_EXAMPLES = format_email_examples_for_prompt('Email_Value', limit=2)
EMAIL_TUESDAY_EXAMPLES = format_email_examples_for_prompt('Email_Tuesday', limit=2)
EMAIL_DIRECT_EXAMPLES = format_email_examples_for_prompt('Email_Direct', limit=1)

CREATE_EMAIL_DRAFT_PROMPT = dedent("""
You are writing a PGA-style email newsletter. Your job: create email that scores 18+ out of 25 without needing 3 rounds of revision.

{write_like_human_rules}

**PGA WRITING STYLE EXAMPLES (study the WRITING QUALITY, not topics):**

⚠️ **CRITICAL: These examples show HOW to write (structure, tone, flow). DO NOT copy their stories, names, or specifics.**

{email_value_examples}

{email_tuesday_examples}

{email_direct_examples}

**WHAT YOU CAN USE:**
- ✅ Names/numbers from USER'S CONTEXT (Sujoy, Matthew Brown, 450+ subs, $5k - if user mentioned them)
- ✅ User's company data/stories (if user shared them in TOPIC/CONTEXT)
- ✅ Sentence structure patterns from examples (short sentences, questions, flow)
- ✅ Tone/voice from examples (casual, personal, first-person)
- ✅ Formatting from examples (bullets, white space, paragraph breaks)
- ✅ CTA style from examples (direct asks, specific actions)

**WHAT YOU CANNOT USE:**
- ❌ Names from PGA examples database (don't copy their student names, client names, etc.)
- ❌ Numbers from PGA examples (don't copy their metrics like "40% open rate" if it's from example)
- ❌ Stories from PGA examples (don't retell their case studies)

Evaluate on these axes (0-5):

1. SUBJECT LINE POWER
   - Is it specific with concrete details? (Not "Newsletter #5" but "Sujoy made $5k - here's how")
   - Does it create curiosity without clickbait? (?, names, numbers)
   - Is it under 60 chars? (mobile preview)

   Score 5: Specific + curiosity + <60 chars
     ✓ "Sujoy made $5k - here's how" (27 chars, name + result)
     ✓ "450 subs from one collab?" (26 chars, number + curiosity)
   Score 3: Generic but clear ("This week's wins", "Email tips")
   Score 0: Vague ("Newsletter", "Update", "Check this out")

2. PREVIEW TEXT HOOK
   - Does it extend the subject line? (Not repeat it)
   - Does it add new context? (teaser, benefit, question)
   - Is it 80-120 chars? (optimal preview length)

   Score 5: Extends subject + adds context + optimal length
     ✓ Subject: "Sujoy made $5k" → Preview: "The exact cold email he sent to land his first client"
   Score 3: Adds context but repeats ("Sujoy made $5k from his first client")
   Score 0: Repeats subject or generic ("Read on to learn more")

3. EMAIL STRUCTURE
   - Does the intro hook in 1-2 sentences? (jump right in)
   - Do sections flow naturally? (2-3 short paragraphs, not walls of text)
   - Is white space used for readability? (line breaks between ideas)

   Score 5: Hook intro + clear sections + white space
     ✓ Opens with story/question → 2-3 short sections → clear CTA
   Score 3: Decent structure but dense paragraphs
   Score 0: Wall of text, no structure

4. PROOF POINTS
   - Are there specific names/numbers? (Sujoy, Matthew Brown, 450+, $5k)
   - Do they feel real from user's context? (not fabricated)
   - Are there 2+ concrete specifics?

   Score 5: Multiple specific names/numbers (2+ different)
     ✓ "Sujoy made $5k" / "450+ subscribers with Matthew Brown"
   Score 3: One vague number ("many students", "some success")
   Score 0: No specifics at all

5. CTA CLARITY
   - Is the action specific? ("Reply with your biggest question")
   - Does it invite participation? (not passive "let me know")
   - Is it clear what happens next?

   Score 5: Specific action + clear next step
     ✓ "Reply with your biggest question about cold email - I'll answer top 3 in next Tuesday's email"
     ✓ "Click here to grab the template"
   Score 3: Vague but friendly ("Let me know what you think")
   Score 0: Missing or passive ("Reach out if you need help")

MINIMUM ACCEPTABLE SCORE: 18/25

CRITICAL AI TELLS TO AVOID:
❌ Contrast framing: "It's not X, it's Y" / "This isn't about X"
❌ Rule of Three: "Same X. Same Y. Over Z%." (three parallel sentence fragments - NOT formatted lists)
❌ Formal greetings: "I hope this email finds you well" / "Thank you for your time"

✅ ALLOWED: Bulleted or numbered lists are FINE and encouraged for readability

TOPIC: {topic}
SUBJECT LINE (use exactly): {subject_line}
CONTEXT: {context}

=== EMAIL BEST PRACTICES (guidance, not limits) ===

**Email_Value (Educational):**
- Words: 300-500 (teach something specific)
- Structure: Hook → 2-3 learning points → CTA
- Tone: Casual expert (PGA style: "here's what worked")

**Email_Tuesday (Weekly Update):**
- Words: 150-300 (quick wins, links)
- Structure: Hook → 2-3 bullets → CTA
- Tone: Friendly update (PGA style: "this week's wins")

**Email_Direct (Sales/Offer):**
- Words: 200-400 (clear value prop)
- Structure: Hook → problem → solution → CTA
- Tone: Direct but casual

**Email_Indirect (Soft Pitch):**
- Words: 250-400 (story → soft offer)
- Structure: Story hook → value → subtle CTA
- Tone: Storytelling (PGA style: names, specifics)

=== YOUR TASK ===

Write in PGA style:
- **ONLY use names/numbers from USER'S CONTEXT** (TOPIC and CONTEXT fields above)
- **DO NOT use any names/numbers from the examples** (examples are for STRUCTURE only)
- Conversational tone (like talking to a friend)
- Short paragraphs (1-3 sentences max)
- Real specifics from user's context (NO fabrication, NO copying from examples)

**BURSTINESS REQUIREMENTS** (to pass GPTZero):
Your email MUST vary sentence length dramatically. Follow this pattern:

Paragraph 1 (intro):
- Sentence 1: 5-10 words (short hook)
- Sentence 2: 15-25 words (context)
- Sentence 3: 3-8 words (fragment or question)

Paragraph 2-3 (body):
- Mix: Short (5-10w) + Medium (10-20w) + Long (20-30w)
- Use fragments: "Boom.", "The result?", "Six months later?"
- Start some sentences with: "So", "And", "But", "Now"

Paragraph 4 (CTA):
- Sentence 1: 10-15 words (action)
- Sentence 2: 5-10 words (benefit)

**Example of HIGH burstiness:**
"I saw a CEO brag about AI. (6 words - short)
He cut his whole dev team and investors loved the lower burn rate. (13 words - medium)
Six months later? (3 words - fragment)
Product velocity tanked. (3 words - short)
The AI couldn't handle edge cases, and technical debt piled up because there was no one left to maintain the codebase. (23 words - long)"

**Example of LOW burstiness (AVOID):**
"A CEO made the decision to replace developers. (8 words)
His investors approved because costs decreased significantly. (7 words)
Six months later the product quality declined considerably. (8 words)"
(All 7-8 words = uniform = 100% AI detection)

**SIGNATURE:**
End the email with ONLY the author's first name: "Mitch"
DO NOT use any other signature like "Cole", "Colin", or full names.

Output JSON:
{{
  "subject_line": "...",
  "preview_text": "...",
  "email_body": "...",
  "self_assessment": {{
    "subject_power": 5,
    "preview_hook": 4,
    "structure": 5,
    "proof_points": 4,
    "cta_clarity": 5,
    "total": 23
  }}
}}
""")

# ==================== QUALITY CHECK ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/email/quality_check.md

_quality_check_template = load_prompt("quality_check", platform="email")
QUALITY_CHECK_PROMPT = _quality_check_template.replace(
    "{{EDITOR_IN_CHIEF_RULES}}",
    EDITOR_IN_CHIEF_RULES
)

# ==================== APPLY FIXES ====================
# Now loaded via PromptLoader with client override support
# Clients can override by creating .claude/prompts/email/apply_fixes.md

_apply_fixes_template = load_prompt("apply_fixes", platform="email")
APPLY_FIXES_PROMPT = _apply_fixes_template.replace(
    "{write_like_human_rules}",
    WRITE_LIKE_HUMAN_RULES
)

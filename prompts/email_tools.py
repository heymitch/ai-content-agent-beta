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
from integrations.prompt_loader import load_editor_standards, load_writing_rules

EDITOR_IN_CHIEF_RULES = load_editor_standards()
WRITE_LIKE_HUMAN_RULES = load_writing_rules()

# ==================== GENERATE 5 HOOKS ====================

GENERATE_HOOKS_PROMPT = dedent("""Generate EXACTLY 5 email subject lines for this topic, one for each type:

Topic: {topic}
Context: {context}
Target Audience: {audience}

MANDATORY FORMATS (adapted from proven patterns):
1. Curiosity hook (question or teaser)
2. Specific number/stat (concrete metric)
3. Student/client win (specific name + result)
4. Counter-intuitive take (challenges assumption)
5. Personal story opener (I/we did X...)

Each subject line must:
- Be 40-60 characters (mobile preview)
- Create curiosity without clickbait
- Target the specific audience
- Feel personal (not marketing)

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
1. **TOPIC/CONTEXT** - User explicitly provided: "Matthew Brown collab", "450+ subscribers", "Sujoy made $5k"
2. **WEB SEARCH RESULTS** - Verified via web_search tool (future): industry benchmarks
3. **COMPANY DOCUMENTS** - Retrieved from user-uploaded docs (case studies, testimonials, product docs) - SEE ABOVE


**CRITICAL: DO NOT FABRICATE**
- ❌ Making up student names: "Sarah got her first client"
- ❌ Inventing results: "97% open rate", "$10k in sales"
- ❌ Fabricating case studies: "tested with 50 clients"
- ❌ Creating fake metrics: "234% increase", "12.5 hour time save"
- ❌ Citing stats you don't have: "industry average of 23%"

**WHAT YOU CAN DO:**
- ✅ Use metrics from TOPIC: "450+ subscribers" → "over 450 new subscribers"
- ✅ Add context from TOPIC: "Matthew Brown collab" → "collaboration with Matthew Brown"
- ✅ Use names from TOPIC: "Sujoy" → "Sujoy just made his first $5k"
- ✅ Add verified web search results (when tool provides them)

**DEFAULT BEHAVIOR:**
- If NO additional proof available → Return draft with MINIMAL changes
- Better to have NO proof than FAKE proof

Return the enhanced draft only (plain text with **bold** and *italic* allowed for email formatting).
""")

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

QUALITY_CHECK_PROMPT = """You are evaluating an email newsletter using Editor-in-Chief standards.

═══════════════════════════════════════════════════════════════
EDITOR-IN-CHIEF STANDARDS (READ THESE COMPLETELY):
═══════════════════════════════════════════════════════════════

""" + EDITOR_IN_CHIEF_RULES + """

═══════════════════════════════════════════════════════════════
END OF EDITOR-IN-CHIEF STANDARDS
═══════════════════════════════════════════════════════════════

YOUR TASK:
1. Read the email below
2. Scan sentence-by-sentence for EVERY violation listed in Editor-in-Chief standards above
3. Create ONE surgical issue per violation found
4. Use EXACT replacement strategies from the standards (don't make up your own)

Email to evaluate:
{post}

WORKFLOW:

STEP 1: SCAN FOR VIOLATIONS
Go through the email sentence-by-sentence and find:
- Direct contrast formulations ("This isn't about X—it's about Y", "It's not X, it's Y", "Rather than X")
- Masked contrast patterns ("Instead of X", "but rather")
- Formulaic headers (ANY case):
  * "The X:" pattern → "The promise:", "The reality:", "The result:", "The truth:", "The catch:"
  * "HERE'S HOW:", "HERE'S WHAT:", Title Case In Headings
  * These are AI tells - convert to natural language or delete
- Short questions (<8 words ending in "?"):
  * "For me?" → Delete or expand to statement: "For me, the ability to..."
  * "The truth?" → Delete entirely
  * "What happened?" → Expand: "What did the data show after 30 days?"
  * Count words - if <8 words AND ends with "?", it's a violation
- Subject line AI tells:
  * "You won't believe..." (clickbait)
  * "The secret to..." (puffery)
  * Title case in subject lines
- Preview text issues:
  * Repeats subject line (should extend/add context)
  * Generic ("Read more", "Click here", "View in browser")
- Formal greetings/closings:
  * "I hope this email finds you well"
  * "Thank you for reaching out"
  * "Looking forward to hearing from you"
  * "Best regards," at end (use "Thanks," or just name)
- Section summaries ("In summary", "In conclusion")
- Promotional puffery ("stands as", "testament", "rich heritage")
- Overused conjunctions ("moreover", "furthermore")
- Vague attributions without sources
- Em-dash overuse (multiple — in formulaic patterns)
- Words needing substitution ("leverages", "encompasses", "facilitates")

STEP 2: CREATE SURGICAL ISSUES
For EACH violation found, create ONE issue:
{{
  "axis": "ai_tells",
  "severity": "high" | "medium" | "low",
  "pattern": "contrast_direct" | "puffery" | "word_substitution" | etc,
  "original": "[EXACT text - word-for-word quote]",
  "fix": "[EXACT replacement using Editor-in-Chief examples]",
  "impact": "[How this improves the email]"
}}

STEP 3: USE REPLACEMENT STRATEGIES FROM STANDARDS
Use EXACT patterns from Editor-in-Chief:

For contrast framing:
❌ "Success isn't about working harder but working smarter."
✅ "Success comes from working smarter and more strategically."

For word substitutions:
leverages → uses | encompasses → includes | facilitates → enables

STEP 4: SCORE THE EMAIL
Subject Line (0-5): Specific + curiosity + <60 chars?
Preview Hook (0-5): Extends subject + adds context?
Structure (0-5): Hook intro + clear sections + white space?
Proof Points (0-5): Specific names/numbers (2+)?
CTA Clarity (0-5): Specific action + clear next step?

Deduct 2 points per major AI tell.

STEP 5: VERIFY FACTS (use web_search)
Search for student names, collaboration details, news claims, stats.
If NOT verified: flag as "NEEDS VERIFICATION" or "ADD SOURCE CITATION"
Only use "FABRICATED" if provably false.

CRITICAL RULES:
✅ Create ONE issue per violation
✅ Quote EXACT text in "original"
✅ Use EXACT fixes from Editor-in-Chief standards
✅ Be comprehensive - find EVERY violation

Output JSON:
{{
  "scores": {{
    "subject_power": 4,
    "preview_hook": 3,
    "structure": 5,
    "proof_points": 2,
    "cta_clarity": 4,
    "total": 18,
    "ai_deductions": -4
  }},
  "decision": "revise",
  "searches_performed": ["query 1", "query 2"],
  "issues": [
    {{
      "axis": "ai_tells",
      "severity": "high",
      "pattern": "contrast_direct",
      "original": "[exact quote from email]",
      "fix": "[exact fix from Editor-in-Chief examples]",
      "impact": "[specific improvement]"
    }}
  ],
  "surgical_summary": "Found [number] violations. Applying all fixes would raise score from [current] to [projected]."
}}

Be thorough. Find EVERY violation. Use Editor-in-Chief examples EXACTLY as written.
"""

# ==================== APPLY FIXES ====================

APPLY_FIXES_PROMPT = dedent("""You are fixing an email newsletter based on quality feedback.

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
{{
  "revised_post": "...",
  "changes_made": [
    {{
      "issue_addressed": "subject_too_long",
      "original": "Sujoy made $5k - here's the exact email he sent",
      "revised": "Sujoy made $5k - the exact email",
      "impact": "Reduced from 48 to 32 chars, more mobile-friendly"
    }}
  ],
  "estimated_new_score": 21,
  "confidence": "high"  // "high" | "medium" | "low"
}}

**OUTPUT:**
Return ONLY the revised email - no explanations, no meta-commentary.
Fix ALL issues - no limit. Every flagged pattern and GPTZero sentence must be addressed.
""")

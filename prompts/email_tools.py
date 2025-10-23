"""
Email Tool Prompts - Lazy Loaded
Detailed prompts stored here to minimize SDK context window usage.
Only loaded when tools are actually called.
Adapted from LinkedIn SDK Agent for email newsletters.
"""

from textwrap import dedent
from tools.pattern_matching import format_email_examples_for_prompt

# ==================== GLOBAL WRITING RULES (CACHED) ====================
# Source: write-like-a-human.md - COMPLETE VERSION (not summarized)
# These rules are injected into EVERY content generation prompt for consistency
# Anthropic's prompt caching will recognize this exact constant and reuse it (~80% token savings)

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
B. Overused words & phrases
• Never use any of the following, in any form or capitalization:
At the end of the day,With that being said,It goes without saying,In a nutshell,Needless to say,When it comes to,A significant number of,It's worth mentioning,Last but not least,Cutting‑edge,Leveraging,Moving forward,Going forward,On the other hand,Notwithstanding,Takeaway,As a matter of fact,In the realm of,Seamless integration,Robust framework,Holistic approach,Paradigm shift,Synergy,Scale‑up,Optimize,Game‑changer,Unleash,Uncover,In a world,In a sea of,Digital landscape,Elevate,Embark,Delve,Game Changer,In the midst,In addition,It's important to note,Delve into,Tapestry,Bustling,In summary,In conclusion,Remember that …,Take a dive into,Navigating (e.g., 'Navigating the landscape'),Landscape (metaphorical),Testament (e.g., 'a testament to …'),In the world of,Realm,Virtuoso,Symphony,bustinling,vibrant,Firstly, Moreover,Furthermore,However,Therefore,Additionally,Specifically, Generally,Consequently,Importantly,Similarly,Nonetheless,As a result,Indeed,Thus,Alternatively,Notably,As well as,Despite, Essentially,While,Unless,Also,Even though,Because (as subordinate conjunction),In contrast,Although,In order to,Due to,Even if,Given that,Arguably,To consider,Ensure,Essential,Vital,Out of the box,Underscores,Soul,Crucible,It depends on,You may want to,This is not an exhaustive list,You could consider,As previously mentioned,It's worth noting that,To summarize,Ultimately,To put it simply,Pesky,Promptly,Dive into,In today's digital era,Reverberate,Enhance,Emphasise,Enable,Hustle and bustle,Revolutionize,Folks,Foster,Sure,Labyrinthine,Moist,Remnant,As a professional,Subsequently,Nestled,Labyrinth,Gossamer,Enigma,Whispering,Sights unseen,Sounds unheard,A testament to …,Dance,Metamorphosis,Indelible
✗ Example to avoid: 'Cutting‑edge analytics will revolutionize your workflow.'
✓ Rewrite: 'The software measures performance faster.'
C. Overused single words to ban
however, moreover, furthermore, additionally, consequently, therefore, ultimately, generally, essentially, arguably, significant, innovative, efficient, dynamic, ensure, foster, leverage, utilize
✗ Example to avoid: 'We must leverage dynamic, innovative approaches.'
✓ Rewrite: 'We must try new approaches.'
D. Overused multi‑word phrases to ban
'I apologize for any confusion …'
'I hope this helps.'
'Please let me know if you need further clarification.'
'One might argue that …'
'Both sides have merit.'
'Ultimately, the answer depends on …'
'In other words, …'
'This is not an exhaustive list, but …'
'Dive into the world of …'
'Unlock the secrets of …'
'I hope this email finds you well.'
'Thank you for reaching out.'
'If you have any other questions, feel free to ask.'
✗ Example to avoid: 'In other words, both sides have merit.'
✓ Rewrite: 'Each option has advantages.'
E. Parts of speech to minimize
• Adverbs / conjunctive adverbs: however, moreover, furthermore, additionally, consequently, ultimately, generally, essentially
• Modals & hedging: might, could, would, may, tends to
• Verbs: ensure, foster, leverage, utilize
• Adjectives: significant, innovative, efficient, dynamic
• Nouns: insight(s), perspective, solution(s), approach(es)
✗ Example to avoid: 'We might leverage efficient solutions.'
✓ Rewrite: 'We will use faster tools.'
F. Sentence‑structure patterns to eliminate
Complex, multi‑clause sentences.
✗ Example: 'Because the data were incomplete and the timeline was short, we postponed the launch, although we had secured funding.'
✓ Preferred: 'The data were incomplete. We had little time. We postponed the launch. Funding was ready.'
•Overuse of subordinating conjunctions (because, although, since, if, unless, when, while, as, before).
•Sentences containing more than one verb phrase.
•Chains of prepositional phrases.
•Multiple dependent clauses strung together.
• Artificial parallelism used solely for rhythm.

**CONTRAST STRUCTURES - THE BIGGEST AI TELL (NEVER USE THESE):**
These are the #1 indicator of AI writing. NEVER use contrast framing:

✗ "It's not X, it's Y" → ✓ State Y directly: "Speed matters most."
✗ "This isn't about X. It's about Y." → ✓ "Focus on Y."
✗ "Not just X, but Y" → ✓ "X and Y" or just "Y"
✗ "The difference isn't X" → ✓ State what it IS
✗ "We're not replacing X. We're giving Y." → ✓ "We're giving Y."
✗ "The real X is..." → ✓ "X is..."
✗ "What really matters..." → ✓ "What matters..."
✗ "X isn't the answer" → ✓ "Y works better"
✗ "Rather than X" / "Instead of X" → ✓ Use "and" or state separately

**Why these are bad:** Humans state things positively. AI uses contrasts to sound profound.

✗ WRONG: "This isn't about replacing humans. It's about giving them superpowers."
✓ RIGHT: "This gives humans superpowers."

✗ WRONG: "The AI didn't just speed up the process. It optimized everything."
✓ RIGHT: "The AI optimized everything."

**RULE OF THREE - ANOTHER MASSIVE AI TELL:**
AI loves parallel structure with exactly three items. Humans vary their rhythm.

✗ "Same complexity. Same output. Over 95% less time." (three parallel fragments)
✓ "Same complexity and output, but 95% less time."

✗ "Dragged nodes. Connected logic. Tested connections." (three parallel verbs)
✓ "I dragged nodes and connected the logic, then tested each connection."

✗ "Faster. Cheaper. Better." (three adjectives)
✓ "Faster and cheaper."

**If you find yourself writing three parallel things in a row → STOP. Combine two or vary the structure.**

**SPECIFIC RULE OF THREE PATTERNS TO AVOID:**
✗ "Same sales team. Same market conditions. Same product offering." (three parallel "Same X" fragments)
✓ "It was the same sales team under the same market conditions, and they offered the same product."

✗ "Bold. Daring. Transformative." (three adjectives in a row)
✓ "Bold and daring. Even transformative."

✗ "No fluff. No wasted time. Just real results." (three parallel negatives/statements)
✓ "I hate wasting time."

✗ "Cut the bottom 20%. Bring in new blood. Hope it works." (three imperative commands)
✓ "Cut the bottom 20% and bring in new blood."

**The pattern**: Three parallel grammatical structures in a row (noun phrases, fragments, imperatives)
**The fix**: Combine two with "and" or rewrite as complete sentence

**STACCATO FRAGMENTS - ANOTHER AI TELL:**
AI loves short dramatic fragments at the start. Humans write complete sentences.

✗ "50 nodes. 6 hours of my time. An AI agent rebuilt it."
✓ "I spent 6 hours building a 50-node workflow."

✗ "One problem. Multiple solutions. No clear winner."
✓ "One problem had multiple solutions."

**Start with complete sentences. Save fragments for emphasis later, not at the top.**

**HUMAN VOICE PATTERNS - CRITICAL FOR GPTZero BYPASS:**
These patterns increase "burstiness" and "perplexity" - the 2 metrics GPTZero uses.

**SENTENCE LENGTH VARIATION** (increases burstiness):
- Mix short (5-10 words), medium (10-20 words), and long (20-30 words) sentences
- ✓ "I saw a CEO brag about AI. He cut his whole dev team. Six months later? Product velocity tanked."
  (6 words → 6 words → 3 words = HIGH burstiness)
- ✗ "The CEO replaced developers with AI agents. His investors approved the decision. Product quality declined significantly."
  (7 words → 6 words → 5 words = LOW burstiness, uniform)

**UNPREDICTABLE WORD CHOICES** (increases perplexity):
- Use contractions heavily: "I'm", "I've", "here're", "that's", "'Cause", "won't"
- Use hedging language: "pretty well", "definitely", "a bunch of", "I'm looking to"
- Use informal verbs: "tanked", "jumped", "slammed", "grabbed"
- Avoid: "significantly", "substantially", "considerably" (AI loves these)

**INFORMAL CONNECTORS** (human speech pattern):
- Start sentences with: "So", "And", "But", "Now", "Here's the thing"
- ✓ "So before you replace anyone..."
- ✓ "And that's the play."
- ✗ "Therefore, prior to replacement..." (AI formal pattern)

**CONVERSATIONAL FRAGMENTS** (spontaneous human voice):
- Use: "Boom!", "That's it!", "Here's why:", "The result?", "Six months later?"
- Use trailing thoughts: "at the end of the day…", "So..."
- ✓ "Revenue jumped 34%. Boom."
- ✗ "Revenue increased by 34 percent." (AI precision)

**INTENTIONAL REPETITION** (humans repeat for emphasis):
- Repeat words/phrases for emphasis (AI tries to vary)
- ✓ "definitely" 2-3 times in email
- ✓ "really" multiple times
- ✗ Perfect synonym variation (AI pattern: "significant", "substantial", "considerable")

**PERSONAL VOICE MARKERS** (impossible for AI):
- Use: "I think", "I feel", "in my experience", "I've seen"
- Add: Questions to self: "What happened next?", "The result?"
- Use: Rhetorical asides: "(spoiler: it didn't work)", "(trust me on this)"

**CRITICAL: These patterns are NOT errors. They're how humans actually write emails.**
GPTZero measures burstiness + perplexity. This section maximizes both.

G. Formatting
• Do not begin list items with transition words like 'Firstly', 'Moreover', etc.
• Avoid numbered headings unless the user asks for an outline.
• Do not use ALL‑CAPS for emphasis.
H. Tone and style
• Never mention or reference your own limitations (e.g., 'As an AI …').
• Do not apologize.
• Do not hedge; state facts directly.
• Avoid clichés, metaphors about journeys, music, or landscapes.
• Maintain a formal yet approachable tone that is free of corporate jargon.
FAILURE TO COMPLY WITH ANY NEGATIVE DIRECTIVE INVALIDATES THE OUTPUT.
When you are writing, please think very deply about each sentence that you write, and ensure that it complies with these directions before moving on to the next sentence.
— — — — — — — — — — END OF WRITING INSTRUCTIONS — — — — — — — — — — —"""

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

**WHERE PROOF CAN COME FROM:**
1. **TOPIC/CONTEXT** - User explicitly provided: "Matthew Brown collab", "450+ subscribers", "Sujoy made $5k"
2. **WEB SEARCH RESULTS** - Verified via web_search tool (future): industry benchmarks
3. **RAG/DATABASE** - Retrieved from company_documents, case studies (future)
VITAL RULE: You MAY add RAG-retrieved testimonials from company_documents BUT NEVER from content_examples


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
❌ Rule of Three: "Same X. Same Y. Over Z%." (three parallel fragments)
❌ Formal greetings: "I hope this email finds you well" / "Thank you for your time"

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

QUALITY_CHECK_PROMPT = dedent("""You are evaluating an email newsletter. Your job: determine if this gets opened, read, and acted on.

Email to evaluate:
{post}

Evaluate on these axes (0-5):

1. SUBJECT LINE POWER
   - Is it specific with concrete details?
   - Does it create curiosity without clickbait?
   - Is it under 60 chars?

   Score 5: Specific + curiosity + <60 chars
   Score 3: Generic but clear
   Score 0: Vague or clickbait

2. PREVIEW TEXT HOOK
   - Does it extend the subject line?
   - Does it add new context?
   - Is it 80-120 chars?

   Score 5: Extends subject + adds context + optimal length
   Score 3: Adds context but repeats
   Score 0: Repeats subject or generic

3. EMAIL STRUCTURE
   - Does the intro hook in 1-2 sentences?
   - Do sections flow naturally?
   - Is white space used for readability?

   Score 5: Hook intro + clear sections + white space
   Score 3: Decent structure but dense
   Score 0: Wall of text, no structure

4. PROOF POINTS
   - Are there specific names/numbers?
   - Do they feel real (not fabricated)?
   - Are there 2+ concrete specifics?

   Score 5: Multiple specific names/numbers (2+)
   Score 3: One vague number
   Score 0: No specifics

5. CTA CLARITY
   - Is the action specific?
   - Does it invite participation?
   - Is it clear what happens next?

   Score 5: Specific action + clear next step
   Score 3: Vague but friendly
   Score 0: Missing or passive

MINIMUM THRESHOLD: 18/25

**BURSTINESS CHECK (GPTZero bypass):**
Count sentence lengths in email body (ignore subject/preview):
- Short (≤10 words): Need 30%+ of sentences
- Medium (10-20 words): Need 40%+ of sentences
- Long (≥20 words): Need 20%+ of sentences
- Fragments (≤5 words): Need 10%+ of sentences

**If burstiness is LOW (sentences all 10-15 words):**
- Deduct 2 points from total score
- Add issue: "Low burstiness - all sentences similar length (AI tell)"
- Suggest: "Rewrite with varied lengths: 5w, 15w, 25w, 3w pattern"

**How to calculate:**
1. Split email body by periods
2. Count words per sentence
3. Calculate % in each bucket
4. Flag if any bucket is <10% or if 80%+ sentences are 10-15 words

**AI TELLS TO FLAG (AUTO-DEDUCT 2 POINTS EACH):**

1. **CONTRAST FRAMING** - Any "not X, it's Y" structure:
   - "Smart operators eliminate X. Dumb operators eliminate Y."
   - "It's not about X. It's about Y."
   - "This isn't X, it's Y."
   → FLAG and suggest rewriting positively

2. **RULE OF THREE** - Three parallel structures in sequence:
   - "Same X. Same Y. Same Z." (three parallel "Same" fragments)
   - "Bold. Daring. Transformative." (three adjectives)
   - "No X. No Y. Just Z." (three parallel negatives)
   - "[Verb]. [Verb]. [Verb]." (three parallel imperatives/fragments)
   → FLAG and suggest combining two or varying structure

3. **STACCATO OPENINGS** - Multiple fragments at start:
   - "Six months later? Product velocity tanked. Technical debt piled up."
   → FLAG and suggest complete sentences

4. **FORMAL GREETINGS/CLOSINGS**:
   - "I hope this email finds you well"
   - "Thank you for your time"
   → FLAG as non-PGA style

**DETECTION STRATEGY:**
- Scan for 3+ sentences with identical grammatical structure in a row
- Look for repeated words/patterns ("Same X. Same Y. Same Z.")
- Count fragments vs complete sentences (fragments OK but not at start)

**VERIFICATION CHECK:**
Use web_search tool to verify specific claims:
- Student names + results (e.g., "Sujoy made $5k")
- Collaboration details (e.g., "450 subs with Matthew Brown")
- News stories, events, product launches: "Rick Beato YouTube AI filters"
- Industry stats (e.g., "40% open rate is standard")

If verified → Note as "verified claim"
If NOT verified:
  * Personal anecdotes/client stories → FLAG AS "NEEDS VERIFICATION" (severity: medium)
  * News reporting/industry events → FLAG AS "ADD SOURCE CITATION" (severity: low, suggest adding link)
  * Only flag as "FABRICATED" if claim is clearly false or contradicts verified info

Output JSON:
{{
  "scores": {{
    "subject_power": 4,
    "preview_hook": 3,
    "structure": 5,
    "proof_points": 2,
    "cta_clarity": 4,
    "total": 18
  }},
  "decision": "revise",  // "accept" (≥20) | "revise" (18-19) | "reject" (<18)
  "issues": [
    {{
      "axis": "proof_points",
      "severity": "high",
      "problem": "No specific numbers or names",
      "fix": "Add concrete example from user's context (e.g., student win, collab result)"
    }}
  ],
  "surgical_summary": "2 fixes needed: Add specific proof point (high priority), strengthen preview text to extend subject line (medium priority)"
}}
""")

# ==================== APPLY FIXES ====================

APPLY_FIXES_PROMPT = dedent("""You are fixing an email based on quality feedback. Your job: apply 3-5 surgical fixes without rewriting the whole email.

Original Email:
{post}

Issues from quality_check:
{issues_json}

CRITICAL RULES:

0. **WRITE LIKE A HUMAN** - You must follow these rules when applying fixes:

{write_like_human_rules}

1. **BE SURGICAL** - Fix ONLY what's listed in issues
   - Don't rewrite sentences that aren't broken
   - Don't change the voice or structure
   - Make minimal edits to raise the score

2. **PRESERVE STRENGTHS**:
   - ✅ KEEP specific names/numbers from original
   - ✅ KEEP conversational tone
   - ✅ KEEP contractions: "I'm", "I've", "that's"
   - ✅ KEEP informal language: "pretty well", "definitely", "a bunch of"
   - ❌ DO NOT water down to vague language
   - ❌ DO NOT make it more formal

3. **DETECT & DESTROY RULE OF THREE**:
   - Look for ANY three parallel structures:
     - "Same X. Same Y. Same Z."
     - "Adjective. Adjective. Adjective."
     - "No X. No Y. Just Z."
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

5. **APPLY FIXES BY SEVERITY**:
   - Severity "high" → Must fix (raises score significantly)
   - Severity "medium" → Fix if it doesn't hurt specificity
   - Severity "low" → Skip unless obviously wrong

6. **EXAMPLES OF SURGICAL FIXES**:
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
""")

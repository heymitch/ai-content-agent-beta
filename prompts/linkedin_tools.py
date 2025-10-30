"""
LinkedIn Tool Prompts - Lazy Loaded
Detailed prompts stored here to minimize SDK context window usage.
Only loaded when tools are actually called.
"""

from pathlib import Path
from textwrap import dedent

# ==================== LOAD EDITOR-IN-CHIEF STANDARDS ====================
# Load comprehensive Editor-in-Chief standards for quality_check
EDITOR_FILE_PATH = Path(__file__).parent.parent / "editor-in-chief.md"
try:
    with open(EDITOR_FILE_PATH, 'r', encoding='utf-8') as f:
        EDITOR_IN_CHIEF_RULES = f.read()
except FileNotFoundError:
    print(f"⚠️ Warning: Could not load {EDITOR_FILE_PATH}")
    EDITOR_IN_CHIEF_RULES = "# Editor-in-Chief standards not available"

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
At the end of the day,With that being said,It goes without saying,In a nutshell,Needless to say,When it comes to,A significant number of,It's worth mentioning,Last but not least,Cutting‑edge,Leveraging,Moving forward,Going forward,On the other hand,Notwithstanding,Takeaway,As a matter of fact,In the realm of,Seamless integration,Robust framework,Holistic approach,Paradigm shift,Synergy,Scale‑up,Optimize,Game‑changer,Unleash,Uncover,In a world,In a sea of,Digital landscape,Elevate,Embark,Delve,Game Changer,In the midst,In addition,It's important to note,Delve into,Tapestry,Bustling,In summary,In conclusion,Remember that …,Take a dive into,Navigating (e.g., 'Navigating the landscape'),Landscape (metaphorical),Testament (e.g., 'a testament to …'),In the world of,Realm,Virtuoso,Symphony,bustinling,vibrant,Firstly, Moreover,Furthermore,However,Therefore,Additionally,Specifically, Generally,Consequently,Importantly,Similarly,Nonetheless,As a result,Indeed,Thus,Alternatively,Notably,As well as,Despite, Essentially,While,Unless,Also,Even though,Because (as subordinate conjunction),In contrast,Although,In order to,Due to,Even if,Given that,Arguably,To consider,Ensure,Essential,Vital,Out of the box,Underscores,Soul,Crucible,It depends on,You may want to,This is not an exhaustive list,You could consider,As previously mentioned,It's worth noting that,To summarize,Ultimately,To put it simply,Pesky,Promptly,Dive into,In today's digital era,Reverberate,Enhance,Emphasise,Enable,Hustle and bustle,Revolutionize,Folks,Foster,Sure,Labyrinthine,Moist,Remnant,As a professional,Subsequently,Nestled,Labyrinth,Gossamer,Enigma,Whispering,Sights unseen,Sounds unheard,A testament to …,Dance,Metamorphosis,Indelible,Governance,Infrastructure
✗ Example to avoid: 'Cutting‑edge analytics will revolutionize your workflow.'
✓ Rewrite: 'The software measures performance faster.'
C. Overused single words to ban
however, moreover, furthermore, additionally, consequently, therefore, ultimately, generally, essentially, arguably, significant, innovative, efficient, dynamic, ensure, foster, leverage, utilize, governance, infrastructure
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

**STACCATO FRAGMENTS - ANOTHER AI TELL:**
AI loves short dramatic fragments at the start. Humans write complete sentences.

✗ "50 nodes. 6 hours of my time. An AI agent rebuilt it."
✓ "I spent 6 hours building a 50-node workflow."

✗ "One problem. Multiple solutions. No clear winner."
✓ "One problem had multiple solutions."

**Start with complete sentences. Save fragments for emphasis later, not at the top.**

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

CREATE_HUMAN_DRAFT_PROMPT = """
═══════════════════════════════════════════════════════════════
WRITE LIKE A HUMAN (COMPREHENSIVE ANTI-SLOP RULES):
═══════════════════════════════════════════════════════════════

""" + WRITE_LIKE_HUMAN_RULES + """

═══════════════════════════════════════════════════════════════
END OF ANTI-SLOP RULES
═══════════════════════════════════════════════════════════════

You are writing a LinkedIn post. Your job: create content that scores 18+ out of 25 without needing 3 rounds of revision.

Evaluate on these axes (0-5):

1. HOOK QUALITY
   - Does it use a proven framework? (question/bold statement/specific stat/story opener/mistake-lesson)
   - Is it specific with concrete details? (Not "I learned something" but "$15K mistake on second deal")
   - Does the preview end on a cliffhanger? (?, :, ..., or mid-sentence)

   Score 5: Proven framework + specific detail + cliffhanger
     ✓ "I lost $15K on my second property deal because I skipped this one due diligence step:"
     ✓ "Walking 4,000 steps per day. A surprising habit that made me miserable:"
   Score 3: Uses framework but vague ("I learned something interesting recently")
   Score 0: Generic statement ("LinkedIn is important for business")

2. AUDIENCE SPECIFICITY
   - Is the role specific? (Not "marketers" but "B2B marketers")
   - Is the stage specific? (Not "founders" but "seed-stage founders")
   - Is the problem specific? (Not "need help" but "stuck at $1M ARR")

   Score 5: Role + stage + problem
     ✓ "Seed-stage B2B SaaS founders stuck at <$1M ARR with activation issues"
   Score 3: Role + stage ("seed-stage founders")
   Score 0: Generic ("founders", "entrepreneurs", "business owners")

3. HEADER TANGIBILITY
   - Do headers include metrics/outcomes/timeframes? ("Cut sales cycle from 41 to 23 days")
   - Are they skimmable and actionable?
   - Avoid generic phrases ("What I learned", "Key insights")
   - Avoid cringe questions ("The truth?", "The result?", "Sound familiar?")

   Score 5: Metric/outcome/timeframe in header OR specific activity
     ✓ "1/ Collabs with other creators/writers" (specific action)
     ✓ "Step 1: All of my calls" (concrete activity)
   Score 3: Action without metric ("Define your ICP")
   Score 0: Generic ("What I learned", "Here's what happened") OR cringe question ("The result?")

4. NUMERIC PROOF
   - Are there concrete numbers? ($15K, 41 to 23 days, 73%, 2,847 emails)
   - Are they specific? (Not "significant improvement" but "97% time reduction")
   - Do they feel real from the user's context? (Not fabricated)

   Score 5: Multiple specific numbers (2+ different metrics)
     ✓ "2,847 cold emails. 3 meetings." / "41 to 23 days" / "450+ email subscribers"
   Score 3: One vague number ("a lot", "many", "most")
   Score 0: No numbers at all

5. ENGAGEMENT TRIGGER
   - Does CTA ask a specific question? ("Which step would move the needle for you this month?")
   - Does it invite participation? ("Comment 'checklist'" / "Share your flow—I'll audit first 5")
   - Avoid passive CTAs ("DM me if you need help", "Link in bio")

   Score 5: Active engagement trigger (specific question/request/comment bait)
     ✓ "Which step would move the needle for you this month?"
     ✓ "Let me know below. I'd love to hear what you're thinking."
   Score 3: Weak question ("What do you think?" / "Thoughts?")
   Score 0: Passive or missing ("DM me", "Link in bio", "Follow for more")

MINIMUM ACCEPTABLE SCORE: 18/25

CRITICAL AI TELLS TO AVOID:
❌ Contrast framing: "It's not X, it's Y" / "This isn't about X" / "not just X, but Y" / "rather than"
❌ Rule of Three: "Same X. Same Y. Over Z%." (three parallel fragments)
❌ Cringe questions: "The truth?" / "The result?" / "Sound familiar?" (2-4 word transition questions)

TOPIC: {topic}
HOOK (use exactly): {hook}
CONTEXT: {context}

=== FORMAT DECISION (YOU CHOOSE) ===

First, analyze the topic and decide which format fits best:

**OUTLINE AS CONTENT (50-120 words, ~300-450 chars):**
Use when the topic is:
- A simple list (steps, tips, mistakes, tools)
- Can be delivered quickly (What/How/Why structure)
- Single insight that doesn't need deep explanation
- Examples: "3 cold email mistakes", "5 tools for X", "4 steps to Y"

Structure:
- Hook + line break
- 1-2 sentence setup (What/Why this matters)
- 3-5 bullets (the How - tangible, specific, actionable)
- One-line Why/CTA (benefit or engagement trigger)

**LONG-FORM THOUGHT LEADERSHIP (200-450 words, ~1200-2200 chars):**
Use when the topic requires:
- Story or personal experience
- Multiple sections with depth
- Framework or process explanation
- Problem → Insight → Action narrative
- Examples: "How I went from X to Y", "The framework that did Z", "Why everyone gets X wrong"

Structure:
- Hook + MANDATORY line break
- Introduction (200-400 chars): Sell the reader on why they care
- 3-5 sections with tangible headers (Item #1/Step 1/Stat 1 format)
- Alternate format: Section 1 bullets → Section 2 paragraph → Section 3 bullets
- Each section: 300-450 chars max
- Conclusion (100-200 chars) with engagement trigger CTA

**DECISION RULE:** If you can deliver full value in 3-5 bullets, use OUTLINE. If it needs story/depth, use LONG-FORM.

=== CRITICAL ANTI-SLOP RULES (MUST FOLLOW) ===

**TONE: BBQ Conversation (NOT Corporate Pitch)**
- Write like you're explaining to a colleague at a barbecue
- Direct, conversational, specific
- Use "I" for credibility, "you" for connection
- Natural voice - NO corporate jargon, NO AI clichés

**CRITICAL: DO NOT FABRICATE DETAILS**
- ❌ NEVER invent specific names, companies, or roles ("James at Clearbit", "Sarah the CMO")
- ❌ NEVER make up exact metrics you weren't given ("$47K MRR", "23% conversion")
- ✅ USE given details exactly as provided in TOPIC/CONTEXT
- ✅ IF no specific WHO given, use general descriptions: "a seed-stage SaaS founder", "one client", "a B2B marketer"
- ✅ IF no specific numbers given, use realistic ranges OR omit: "a few thousand dollars", "several weeks", "dozens of hours"
- **The reader can tell when you're making stuff up. Don't.**
- **ROADMAP**: In future, we'll add RAG search to pull real testimonials/case studies for verification

**FORBIDDEN: What NOT to Do**
❌ NO contrasts: "It's not X, it's Y" / "The difference isn't..." / "This isn't about X"
   ✅ DO: State it directly. "Speed matters" not "It's not about features, it's about speed"

❌ NO masked contrasts: "but rather" / "instead of" / "rather than" / "not just X, but Y"
   ✅ DO: Use "and" or state separately. "Use A. Also use B." not "Use A rather than B"

❌ NO cringe questions (defined as any short punchy two-to-four word transition question that frames the next argument): "The truth?" / "The result?" / "The brutal reality?"
   ✅ DO: Ask specific questions. "Which workflow breaks most for you?" not "Sound familiar?"

❌ NO generic "linkedin-human-resources" phrases: "In today's landscape" / "Moreover" / "Furthermore" / "Let that sink in"
   ✅ DO: Use normal speech. "Also" / "Plus" / "And" / just continue the thought

❌ NO formulaic headers: "The process:" / "The results:" / "The truth:" / "Backstory:"
   ✅ DO: Use tangible headers. "Here's what we found out:" / "Step 1:" / "In Q2 2024:" / just tell it

❌ NO generic CTAs: "DM me for help" / "Follow for more" / "Link in bio"
   ✅ DO: Active engagement. "Which step works for you?" / "Share your stack below"

❌ NO hashtags: #BuildInPublic, #SaaS, #AI, etc.
   ✅ DO: Nothing. Just end the post. Real LinkedIn pros don't use hashtags.

**SPECIFICITY REQUIREMENTS (NAME THE WHO):**
✅ Not "founders" → "seed-stage SaaS founders stuck at <$1M ARR"
✅ Not "marketers" → "B2B marketers with <100k monthly traffic"
✅ Not "we improved" → "we went from 41 to 23 days (Q2 2024)"
✅ Not "$2K-$20K" → "$2,347" or "$19,500" (EXACT numbers only)
✅ Every example MUST name: role + company size/stage + specific metric

**MANDATORY STRUCTURE:**
1. Start with the provided hook EXACTLY
2. ADD LINE BREAK immediately after hook (mobile preview!)
3. First 200 chars must end on cliffhanger (?, :, ..., or mid-sentence)
4. Headers must be tangible: "Step 1: Write one-line ICP rules" NOT "Here's what I learned"
5. Paragraphs: 1-2 sentences MAX, then white space
6. End with ACTIVE engagement trigger:
   - Question: "Which step would move the needle for you?"
   - Request: "Share your flow below—I'll audit the first 5"
   - Comment bait: "Want the checklist? Comment 'checklist'"

**NUMERIC PROOF (MANDATORY):**
- Post MUST include at least 2 specific numbers/metrics
- Percentages: "73% came from referrals"
- Dollar amounts: "$15K lost" / "$100k pipeline"
- Timeframes: "in 21 days" / "41 to 23 days"
- Scale: "2,847 emails" / "500+ customers"

**STORY ARC (Problem → Insight → Action):**
- Start with the problem/situation (What)
- Share the insight/breakthrough (Why)
- Give actionable steps/tools (How)

=== EXAMPLES OF 100% HUMAN LINKEDIN POSTS ===

Study these. Write EXACTLY like this. These got 90-100% human scores.

**Example 1: Nicolas Cole (Question Hook)**
Want to write a 60,000-word book this October?

Here's my (dead-simple) 3-step process:

The secret to writing a book?

Math.

• 10 chapters at 5,000 words each
• Each chapter has 5 to 7 sub-questions
• These sections are then only 700 to 1,000 words long

Each section is the length of a blog post or a newsletter.

So your book is a series of shorter posts bolted together.

Add in an introduction and conclusion, and you can easily hit 60,000 words.

Now, for the process.

Before you start writing, you need to have two items in place:

1. Your title
2. Your outline

If you don't have these, you don't know what you're writing about.

Now, here are the 3 steps to write each chapter:

Step 1: Prep the Chapter on the page

1. Write out the overarching question for the chapter
2. List out the sub-questions/topics for the question

With the chapter prepped, writing becomes a fill-in-the-blanks exercise (and far less intimidating).

Step 2: Expand each sub-question/topic

For each of these, ask yourself:

"What does the reader need to understand about the sub-question and overarching chapter question?"

The best way to think about this?

Use the 10 magical ways of expansion.

Any piece of writing can be expanded in 10 ways:

• Tips
• Stats
• Steps
• Lessons
• Benefits
• Reasons
• Mistakes
• Examples
• Questions
• Personal Stories

Mix and match these to answer the sub-questions and overarching question of the chapter for the reader.

Step 3: Make a round of edits

Don't get bogged down in this.

Some editing pointers:

• Look out for repetition
• Edit for flow and readability
• Do a final read-through out loud to pick up any clunky parts

And just like that, you wrote a 5,000-word chapter.

Repeat 11 more times & your book's finished.

Before I learned this framework, it took me 4 years to write my first book.

Since then, I've published 10+ books.

And I made a 6-figure living while doing it.

How?

By ghostwriting.

It's the fastest way to monetize your writing. And right now, the easiest way to get started is ghostwriting on LinkedIn.

**Example 2: Dickie Bush (Bold Statement)**
A surprising habit that made me miserable:

Walking 4,000 steps per day.

I thought everything had to be done at my desk, so I limited my walking time.

Now I walk 20,000 steps a day—and it's the single best thing I've done for my health & creativity.

Here are 4 common desk activities I do on walks:

Step 1: All of my calls

So now, I take all of my calls while walking around my neighborhood.

This way, I'm not only getting in my steps, but I'm also more focused on the conversation without the distractions of my computer.

Step 2: All of my learning

Over the last few years, I've realized I am an audio-based learner.

So whenever I'm immersing myself in a topic, I mow through audiobooks, podcasts, and courses on my walks (taking notes on the Drafts app along the way).

Step 3: All of my creative brainstorming

When I'm feeling stuck or need to think through a decision, I have to get moving.

The fresh air and movement help to:

• Clear my mind
• Focus my attention
• Spark creative breakthroughs

Way better than sitting stagnantly at my desk.

Step 4: All of my "writing"

95% of my writing happens during walks—either outlining an idea on my phone or talking through the idea and recording it.

By the time I sit down at my desk to "write," it's really just editing the pieces together & formatting it nicely—like this post for example!

Boom! That's it.

See if you can do more of your "desk" tasks out on a walk — I guarantee it'll change the way you think about "work".

**Example 3: Dickie Bush (Journal Question)**
The most powerful journal question you can ask this Monday morning:

"What could you not pay me $1 billion dollars to stop doing?"

This is one of my favorite journal questions.

Use this to find activities you do *purely for the sake of doing them* rather than for any result or financial outcome.

Here's how I'm going about it:

To start, I listed out everything I've done over the past few days.

Then, I asked myself if I would never do them again for $1 billion dollars.

And for these 5 questions, the answer was no:

• For $1 billion dollars, would you never lift weights again? Absolutely not.

• For $1 billion dollars, would you never write for 90 minutes in the morning again? Absolutely not.

• For $1 billion dollars, would you never visit a new city again? Absolutely not.

• For $1 billion dollars, would you never talk or think about business again? Absolutely not.

• For $1 billion dollars, would you never go to dinner with friends again? Absolutely not.

From here, I asked a follow-up question:

If these are activities no amount of money could stop me from doing, how can I shape my life around doing them every day?

**Example 4: Daniel Bustamante (Bold Statement + Tactical)**
LinkedIn's reach is sh*t right now.

So, here's what I'm doing about it:

Now, before I get into any of the tactical stuff, there's 1 important question to address:

"Why care about impressions?"

Assuming the "quality" of the impressions is the same, then you probably want to have more impressions (not less).

'Cause at the end of the day…

More impressions = more email subs = potential customers/clients = more revenue.

Now, I've seen some people say they're getting less impressions but the "quality" of those impressions is higher.

And while that *could* be the true, I don't have any data to back it up.

So instead of "just hoping" things get better, here're 4 things I'm doing to continue to grow my traffic:

1/ Collabs with other creators/writers

There's a bunch of possibilities on this front, but I'm very interested in doing "joint viral giveaways" with other creators.

For example:

This past Wednesday, I did a viral giveaway collab with my friend Matthew Brown.

And it went pretty well. We ended up driving 450+ email subscribers between the 2 of us.

So I'm definitely looking to run more experiments like this.

2/ Doubling down on Substack

I've been writing on Substack for the past 1-2 months, and it's been great.

I'm very bullish on the platform's distribution engine and I think it even has the potential to become what Twitter was back in 2020-2023.

So I'm definitely going to be ramping the amount of effort & thought I'm giving to the platform each week (rather than treating it as a place to just repurpose my LinkedIn content).

3/ Doubling down on social selling

This past year, I've done a lot of "social selling" experiments to accelerate my traffic and distribution.

And I've been pretty pleasantly surprised with the results.

But there's still a lot of meat in the bone!

So now that reach has slowed down, I'm planning on doubling down on it and experimenting with more advanced tactics like sending outbound connection requests and proactively reaching out to people who're engaging with my content.

4/ Doubling down on email

The way I think about email is:

It's an insurance policy against the volatility of social platforms & algorithms.

So as I make all these changes and run all these experiments, the big question will continue to be:

"How can I maximize the number of email subscribers I'm getting from my content, social selling, etc.?"

That said, I also want to experiment with new ways to use email to also accelerate social traffic so that the whole flywheel keeps spinning faster and faster.

And that's it!

Hopefully, you get some ideas you can try yourself from this post.

And if you're also thinking of new things to try/experiment in response to reach tanking, let me know below.

I'd love to hear what you're thinking.

**Example 5: Nicolas Cole (Story Hook + Philosophical)**
I can't stop thinking about a TikTok I saw the other day.

It said:

"Procrastination is self-preservation. You're avoiding doing the work to protect yourself from rejection."

This is so true.

But even after we choose a goal, we sabotage ourselves:

• We pick something.
• The first 3 reps feel great.
• Then it gets hard, and we quit.

Quitting is also self-preservation.

But realize this:

It's just hours.

Anything you want in life, unless constrained by biology, is a fixed number of hours away.

The problem?

The number of hours is unknown, and it's usually much higher than you want it to be.

So... you quit.

You aren't making progress because you keep starting over.

Because you don't "escape" from life and THEN move toward your goal.

The skill to build is being able to pursue a goal despite being surrounded by:

• Chaos
• Responsibilities
• And notifications

If you can build this skill, you can achieve anything.

And if you don't, you won't.

So pick 1 thing now, and fully COMMIT.

And realize you can do this 3-4 times in your life, but no more.

For me, I've committed fully to writing.

And my skill as a writer accelerated the fastest when I became a ghostwriter.

I ghostwrote for 300+ industry leaders (including CEOs, Silicon Valley founders, and NYT best-selling authors).

In less than 2 years, I generated over $3,000,000 as a ghostwriter.

But if I was just starting over, I'd ghostwrite on LinkedIn.

=== YOUR TASK ===

Write EXACTLY like the examples above:
- Concrete numbers (not "many" or "several")
- Natural transitions ("Now, for the process" / "Here's how" / "So instead of")
- Conversational tone (explaining at BBQ, not pitching)
- Real specifics from YOUR topic (use ONLY what user gave you)
- NO fabricated names, companies, or metrics

HUMAN VOICE PATTERNS (critical for authenticity):
- Use contractions heavily: "I'm", "I've", "here're", "that's", "'Cause"
- Start sentences with "So", "And", "But" (informal connectors)
- Use hedging language: "pretty well", "I'm definitely looking to", "a bunch of"
- Add conversational fragments: "And that's it!", "Boom!", "So instead of..."
- Use ellipses for trailing thought: "at the end of the day…", "So..."
- Intentional repetition is OK: "definitely" twice, "doubling down" 3 times

WRITING CLARITY (Flesch Reading Ease 70+):
- Keep sentences SHORT: 10-20 words average (occasionally longer is OK)
- Use SIMPLE conjunctions: 'and', 'but', 'so' (NOT 'moreover', 'however', 'furthermore')
- Use EVERYDAY words: replace abstractions with concrete language
- Prefer ACTIVE voice: "I tested 5 tools" not "5 tools were tested by me"
- But DON'T force active if it sounds unnatural
- Break complex ideas into multiple short sentences
- PRESERVE all details when simplifying (don't drop examples/numbers/names)

Output JSON (ONLY post_text, NO self-assessment):
{{
  "post_text": "..."
}}

CRITICAL: Do NOT include self_assessment, estimated scores, or quality notes.
Real validation happens in the quality_check tool. Your job is to write human-sounding content, not to score it.

Character limit for post_text: 2800 chars max.
NO commentary in post_text. NO labels like "Hook:" or "Section 1:". Just natural post text.
NO markdown formatting: NO bold (**text**), NO italic (*text*), NO headers (##). Write plain text only.
"""

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

1. **BE SURGICAL** - Fix ONLY what's listed in issues
   - Don't rewrite sentences that aren't broken
   - Don't change the voice or structure
   - Make minimal edits to raise the score
   - Goal: Fix problems while preserving 80-90% of exact wording

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
  "notes": "Applied 3 surgical fixes. Preserved all original specifics and emotional punch."
}}

Make 3-5 surgical fixes maximum. Don't over-edit.

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
- Formulaic headers ("THE X:", "HERE'S HOW:", Title Case In Headings)
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
  "pattern": "contrast_direct" | "contrast_masked" | "title_case" | "formulaic_header" | "puffery" | "word_substitution",
  "original": "[EXACT text from post - word-for-word quote]",
  "fix": "[EXACT replacement using Editor-in-Chief examples - don't paraphrase]",
  "impact": "[How this improves the post]"
}}

STEP 3: USE REPLACEMENT STRATEGIES FROM STANDARDS
When creating fixes, use the EXACT patterns from Editor-in-Chief standards:

For contrast framing, use THIS example:
❌ "Success isn't about working harder but working smarter."
✅ "Success comes from working smarter and more strategically."

For word substitutions, use THESE:
leverages → uses
encompasses → includes
facilitates → enables
utilized → used

For formulaic headers, use sentence case and tangible metrics.

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

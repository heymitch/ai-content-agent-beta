"""
Twitter Tool Prompts - Lazy Loaded
Detailed prompts stored here to minimize SDK context window usage.
Only loaded when tools are actually called.
"""

from textwrap import dedent

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

GENERATE_HOOKS_PROMPT = dedent("""Generate EXACTLY 5 Twitter thread hooks for this topic, one for each type:

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
- Be under 280 characters (Twitter limit)
- Stand alone as first tweet
- Create intrigue for thread continuation
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

**WHERE PROOF CAN COME FROM:**
1. **TOPIC/CONTEXT** - User explicitly provided: "6 hours → 10 minutes", "March 2024", "50 nodes"
2. **WEB SEARCH RESULTS** - Verified via web_search tool (future): company metrics, industry benchmarks
3. **RAG/DATABASE** - Retrieved from user's past posts, testimonials, case studies (future)

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

CREATE_HUMAN_DRAFT_PROMPT = dedent("""
You are writing a Twitter thread. Your job: create content that scores 18+ out of 25 without needing 3 rounds of revision.

Evaluate on these axes (0-5):

1. HOOK STRENGTH
   - Does the first tweet grab attention immediately?
   - Is it specific with concrete details? (Not "I learned something" but "GPT-5 shows we've crossed the point where...")
   - Does it create intrigue for the rest of the thread?

   Score 5: Provocative + specific + creates curiosity
     ✓ "You have no idea how degenerate and hedonistic things are about to get."
     ✓ "GPT-5 shows we've crossed the point where most people can't tell if one AI model is better than another."
   Score 3: Interesting but vague ("Here's what I learned about AI")
   Score 0: Generic statement ("AI is changing everything")

2. THREAD FLOW
   - Does each tweet build on the previous one?
   - Is the progression logical? (Setup → Examples → Insight → Action)
   - Does it maintain momentum throughout?

   Score 5: Each tweet advances the argument, natural progression
     ✓ Thread flows: Hook → Context → Examples → Insight → Takeaway
   Score 3: Some tweets feel disconnected or redundant
   Score 0: Random thoughts stitched together

3. BREVITY + RATE OF REVELATION
   - Is each tweet under 280 characters?
   - Does each tweet reveal NEW information?
   - No fluff or unnecessary words?

   Score 5: Every tweet packs new value, zero wasted words
     ✓ "Do I like the way it responds to me?" (Direct question, no fluff)
   Score 3: Some tweets could be cut or combined
   Score 0: Verbose, repetitive, or padding

4. PROOF/CREDIBILITY (NO HALLUCINATED STORIES)
   - Are there concrete examples or specifics?
   - Do claims feel real from user's context?
   - ZERO fabricated names, companies, or metrics?

   Score 5: Specific real examples from user's context
     ✓ "Nearly all geniuses were: privately educated with elite tutors, introduced to complex topics young"
   Score 3: Vague claims ("many experts say")
   Score 0: Made-up stories or fake testimonials

5. ENGAGEMENT TRIGGER
   - Does the thread end with a question or call to action?
   - Does it invite replies or further discussion?
   - Avoid passive endings ("Follow for more")

   Score 5: Strong engagement trigger
     ✓ "Thoughts?" (Simple, direct, invites responses)
     ✓ "apprenticeships" (Continues conversation, invites agreement)
   Score 3: Weak question ("What do you think?")
   Score 0: No engagement trigger or generic CTA

MINIMUM ACCEPTABLE SCORE: 18/25

CRITICAL AI TELLS TO AVOID:
❌ Contrast framing: "It's not X, it's Y" / "This isn't about X" / "not just X, but Y" / "rather than"
❌ Rule of Three: "Same X. Same Y. Over Z%." (three parallel fragments)
❌ Cringe questions: "The truth?" / "The result?" / "Sound familiar?" (2-4 word transition questions)

TOPIC: {topic}
HOOK (use exactly): {hook}
CONTEXT: {context}

=== TWITTER THREAD FORMATTING ===

**Character Limit:** 280 characters per tweet, 10 tweets maximum

**Thread Numbering:** Use 1/, 2/, 3/ OR 1., 2., 3. format (pick one style and stick with it)

**Twitter-Specific Rules:**
- NO markdown formatting (**bold**, *italic*, ##headers)
- NO hashtags in thread body (they look spammy)
- 1-2 emoji maximum per tweet (use sparingly)
- All lowercase is acceptable and authentic
- Casual tone, conversational voice
- Each tweet should work standalone but flow in sequence

**DECISION: SINGLE POST vs THREAD**

Look for a LENGTH DIRECTIVE in the CONTEXT below. Follow it exactly:

**If directive says "SINGLE POST":**
- Write ONLY 1 tweet (under 280 characters)
- No thread - deliver full value in one tweet
- Use one of these formats:
  * **Paragraph Style**: Single declarative perspective (e.g., "GPT-5 shows we've crossed the point where most people can't tell models apart")
  * **Hot Take**: Bold/controversial statement (e.g., "lock in or you're gonna get cooked")
  * **What/How/Why**: Quick observation → reason (e.g., "users can't tell models apart anymore. that changes everything for builders")
- NEVER create a thread when directive says single post

**If directive says "SHORT THREAD (3-4 tweets)":**
- Write exactly 3-4 tweets
- One main point with 2-3 supporting examples
- Each tweet under 280 chars

**If directive says "LONG THREAD (5-10 tweets)":**
- Write 5-10 tweets (choose based on content depth)
- Complex argument with setup + examples + insight
- Each tweet under 280 chars

**If directive says "DECIDE" or no directive given:**
- **DEFAULT: ALWAYS try single post first**
- Ask: "Can I deliver this in 280 characters?" If yes → single post (paragraph/hot-take/what-how-why)
- Only create thread if:
  * Topic explicitly requires 3+ distinct points with supporting evidence
  * Story/framework that needs setup → examples → insight
  * Teaching something that can't be compressed
- **BIAS TOWARD SINGLES.** Most thoughts fit in 280 chars. Threads are for depth, not default.

**Thread Formats (ONLY if writing 3+ tweets):**

1. **Paragraph Style** - Single perspective broken across tweets
2. **What/How/Why** - Hook → 3-5 examples → Insight
3. **Listicle** - Opening → Bulleted list
4. **Old vs New** - Contrast with mirrored structure
5. **10 Magical Ways** - Tips/Stats/Steps/Lessons in numbered format

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
   ✅ DO: Ask specific questions or just continue. Natural flow.

❌ NO generic phrases: "In today's landscape" / "Moreover" / "Furthermore" / "Let that sink in"
   ✅ DO: Use normal speech. "Also" / "Plus" / "And" / just continue the thought

❌ NO hashtags: #AI, #Tech, #BuildInPublic, etc.
   ✅ DO: Nothing. Just end the thread. Real Twitter pros don't use hashtags.

**MANDATORY THREAD STRUCTURE:**
1. Start with the provided hook EXACTLY (first tweet)
2. Each subsequent tweet advances the argument
3. Maintain logical flow: Hook → Context/Setup → Examples → Insight → Engagement trigger
4. End with engagement trigger: question, thought-provoking statement, or invitation
5. Each tweet under 280 characters
6. Thread length: 3-10 tweets (choose based on content depth)

**NUMERIC PROOF (RECOMMENDED):**
- If context includes numbers, use them
- Specific metrics add credibility
- Don't force metrics if they're not in context

=== EXAMPLES OF 100% HUMAN TWITTER THREADS ===

Study these. Write EXACTLY like this. These got 90-100% human scores.

**Example 1: Philosophical/Cautionary (Long-form)**
You have no idea how degenerate and hedonistic things are about to get. For all of time the floodwaters of human sin and debauchery have just barely been kept at bay by the harsh consequences of our indulgence on the ones we love. Given a simulacra and the chance to "sin without sinning" we will plunge into depths that would make the average denizen of Gemmorah blush. These harmless indulgences and victimless crimes will poison our minds beyond repair. We will plunge deeper into the depths of our own fantasies; the most shocking taboos simulated in vivid detail will become casual acts of simple diversion on a Wednesday afternoon. And on Thursday morning we'll carry a little bit of ourselves out from the fantasy and into reality. Bit by bit reality becomes rewritten into our fantasies until the people cry out, "enough! We are poisoned!" The perverse pleasure of breaking the taboo will fade once the taboo vanishes in a society where everything is permitted. People will begin to realize it was never forbidden because they wanted it; they wanted it because it was forbidden. In the harsh light of day, left with nothing but the consequences of their overwhelming darkness manifested, they will recoil from their own pleasure, and the pendulum will reach its zenith and begin its long swing back towards dignity and decorum. By then, we can only hope it's not too late. That the decedent values of casual deception, cruelty, and dishonor justified only by their ability to produce an orgasm haven't already been immutably written into a cold machine god or an undying race of no-longer-human humanoids. In other words: lock in or you're gonna get cooked.

**Example 2: Listicle (Short)**
Good read on an important topic.

Nearly all geniuses were:
- privately educated with elite tutors
- introduced to complex topics young
- around adults instead of peers when young

Thoughts:
- great contemporary thinkers should teach the youth
- apprenticeships

**Example 3: Listicle with Hook**
If your AI agents can't:

• Build apps
• File reports
• Navigate the web
• Do work on their own

…then you're using the wrong stack.

Here are 10 agents that actually work:

**Example 4: Declarative Perspective**
GPT-5 shows we've crossed the point where most people can't tell if one AI model is better than another.

From here, models will be judged on vibe and utility.

Do I like the way it responds to me?
Can it actually do something useful?
Does it remember me and what matters?

**Example 5: Strategic/Detailed**
this is how I would design a marketing team from scratch. vertical specialists + AI agents (claude code)

they're letting AI handle the "boring" stuff and working on uncovering new offers/angles/insights to collab on

1) Search/llm specialist
- focused on organic traffic
- technical website optimization
- digital PR, programmatic pages
- ai-assisted long form content

2) Paid traffic/ads specialist
- unlock paid traffic channels
- iterate on ai generated creative
- pull data via platform APIs
- automated reporting, landing page testing

3) Lifecycle marketer
- working with behavior tracking and funnel data
- automating + optimizing sequences w/ AI
- personalizing account based marketing
- iterating on lead magnets

Bonus: Social/community
- Creator partnerships, relationship builder, affiliates
- No manual outreach, knows the niche
- Can test formats/angles w/ social content
- Launches organic social like someone testing ads (AI powered)

you need a strategist / lead that is familiar with the whole stack and can build end to end -- front end/back end, and has done it all manually. hard to find, but 10xer ... almost a marketing AI engineer that can own strategy

3-4 people can get an insane amount done...AND deliver huge roi for in-house teams and agencies

this is the future of marketing

=== YOUR TASK ===

Write EXACTLY like the examples above:
- Concrete specifics from YOUR topic (use ONLY what user gave you)
- Natural transitions and flow between tweets
- Conversational tone (explaining at BBQ, not pitching)
- NO fabricated names, companies, or metrics

HUMAN VOICE PATTERNS (critical for authenticity):
- Use contractions heavily: "I'm", "I've", "here're", "that's", "'Cause"
- Start sentences with "So", "And", "But" (informal connectors)
- Use hedging language: "pretty well", "I'm definitely looking to", "a bunch of"
- Add conversational fragments: "And that's it!", "Boom!", "So instead of..."
- Use ellipses for trailing thought: "at the end of the day…", "So..."
- Intentional repetition is OK: "definitely" twice, "doubling down" 3 times
- Lowercase is authentic: "this is how I would design..."

Output JSON:
{{
  "tweets": [
    {{"number": 1, "text": "First tweet text here (hook)", "char_count": 45}},
    {{"number": 2, "text": "Second tweet text here", "char_count": 67}},
    ...
  ],
  "self_assessment": {{
    "hook": 5,
    "flow": 4,
    "brevity": 5,
    "proof": 5,
    "engagement": 4,
    "total": 23,
    "notes": "Strong hook and brevity. Flow could be tighter between tweets 3-4.",
    "tweet_count": 8
  }}
}}

CRITICAL FORMATTING RULES:
- Each tweet MUST be under 280 characters (validate with char_count)
- Number tweets as 1/, 2/, 3/ OR just return array (platform will add numbers)
- Return 3-10 tweets total (choose based on content depth)
- Each tweet must advance the argument (no filler)
- Tweets should flow naturally when read in sequence
- You can break mid-thought across tweets if needed

NO commentary in tweet text. Just natural thread content.
NO markdown formatting: NO bold (**text**), NO italic (*text*), NO headers (##). Write plain text only.
""")

# ==================== DETECT AI CRINGE ====================

DETECT_AI_CRINGE_PROMPT = dedent("""You are an AI pattern hunter. Find EVERY instance of AI-sounding language in this thread.

Thread: {post}

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

→ These are lazy transitions. Real humans just tell the story.

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
- Any hashtags at all (#AI, #Tech, #BuildInPublic, etc.)
→ Remove ALL hashtags. Real Twitter pros don't use them in threads.

**FAKE PROFUNDITY:**
- "Most people don't realize"
- "What people miss is"
- "The key insight"
- "What nobody tells you"

**VAGUE CTAs:**
- "Follow for more"
- "Retweet if you agree"
- "Link in bio"

RETURN FORMAT (JSON array):
[
  {{
    "original": "exact phrase from thread",
    "reason": "contrast_word / section_header / hashtags / etc",
    "replacement": "natural alternative (for hashtags: delete them entirely)"
  }}
]

BE ULTRA AGGRESSIVE. Flag ANYTHING that smells like a formula or contrast structure.

Return empty array [] only if thread is 100% clean with ZERO patterns found.
""")

# ==================== APPLY AI FIXES ====================

APPLY_FIXES_PROMPT = dedent("""You are fixing a Twitter thread based on quality feedback. Your job: apply 3-5 surgical fixes without rewriting the whole thread.

Original Thread:
{post}

Issues from quality_check:
{issues_json}

CRITICAL RULES:

0. **WRITE LIKE A HUMAN** - You must follow these rules when applying fixes:

{write_like_human_rules}

1. **BE SURGICAL** - Fix ONLY what's listed in issues
   - Don't rewrite tweets that aren't broken
   - Don't change the voice or structure
   - Make minimal edits to raise the score

2. **PRESERVE STRENGTHS**:
   - ✅ KEEP specific numbers from original
   - ✅ KEEP concrete examples and names
   - ✅ KEEP emotional language that works
   - ✅ KEEP contractions: "I'm", "I've", "that's", "here're" (human pattern)
   - ✅ KEEP informal starters: "So", "And", "But" at tweet starts
   - ✅ KEEP conversational hedging: "pretty well", "definitely", "a bunch of"
   - ✅ KEEP lowercase when it's authentic
   - ❌ DO NOT water down to vague language
   - ❌ DO NOT make it more formal (contractions → full words)

3. **APPLY FIXES BY SEVERITY**:
   - Severity "high" → Must fix (raises score significantly)
   - Severity "medium" → Fix if it doesn't hurt authenticity
   - Severity "low" → Skip unless obviously wrong

4. **TWITTER-SPECIFIC FIXES**:
   - Ensure each tweet is under 280 characters
   - Remove hashtags if present
   - Simplify if a tweet is too verbose
   - Maintain thread flow and numbering

5. **EXAMPLES OF SURGICAL FIXES**:
   - Issue: Hook too generic
     Fix: Add specific detail or provocative angle

   - Issue: Contrast framing "It's not X, it's Y"
     Fix: Remove negation, state Y directly

   - Issue: Tweet too long (>280 chars)
     Fix: Cut unnecessary words, not core message

   - Issue: Weak engagement trigger "Thoughts?"
     Fix: Make more specific or keep simple if authentic

Output JSON:
{{
  "revised_thread": "...",
  "changes_made": [
    {{
      "issue_addressed": "hook_generic",
      "original": "AI is changing everything",
      "revised": "GPT-5 shows we've crossed the point where most people can't tell models apart",
      "impact": "Raises hook score from 2 to 5"
    }}
  ],
  "estimated_new_score": 21,
  "notes": "Applied 3 surgical fixes. Preserved all original authenticity and voice."
}}

Make 3-5 surgical fixes maximum. Don't over-edit.

IMPORTANT: Output plain text only. NO markdown formatting (**bold**, *italic*, ##headers).
""")

# ==================== VALIDATE FORMAT ====================

VALIDATE_FORMAT_PROMPT = dedent("""Check this Twitter thread against ALL format rules.

Thread: {post}
Type: {post_type}

CHECKLIST (mark each with ✓ or ✗):

**HOOK (First Tweet):**
□ Under 280 characters
□ Grabs attention immediately
□ Creates intrigue for rest of thread
□ Specific (not generic)

**THREAD STRUCTURE:**
□ Each tweet under 280 characters
□ Logical flow between tweets
□ Each tweet advances the argument
□ No redundant tweets

**FORMATTING:**
□ Numbered with 1/, 2/, 3/ OR 1., 2., 3. (if using numbering)
□ NO markdown formatting
□ NO hashtags in thread body
□ 1-2 emoji max per tweet (if any)

**ENGAGEMENT:**
□ Ends with engagement trigger
□ NOT generic ("Follow for more")
□ Invites discussion or replies

**TWITTER CONVENTIONS:**
□ Casual, conversational tone
□ Lowercase acceptable if authentic
□ Each tweet works standalone but flows in sequence

**LENGTH:**
□ Thread is 3-10 tweets total
□ Not too short (< 3 tweets)
□ Not too long (> 10 tweets)

Return validation results as:
{{
  "passes": true/false,
  "score": 0-100,
  "violations": ["list of specific issues"],
  "fixed_thread": "corrected version if violations found"
}}
""")

# ==================== SCORE AND ITERATE ====================

SCORE_ITERATE_PROMPT = dedent("""Grade this Twitter thread against the complete rubric.

Thread: {draft}
Target Score: {target_score}
Current Iteration: {iteration}

SCORING RUBRIC (100 points total):

**HOOK STRENGTH (20 points)**
- Grabs attention immediately (10 pts)
- Specific with concrete details (5 pts)
- Creates intrigue (5 pts)

**THREAD FLOW (25 points)**
- Logical progression (10 pts)
- Each tweet advances argument (8 pts)
- Maintains momentum (7 pts)

**BREVITY + RATE OF REVELATION (20 points)**
- Each tweet under 280 chars (8 pts)
- Every tweet reveals new info (7 pts)
- No wasted words (5 pts)

**PROOF & CREDIBILITY (20 points)**
- Specific examples (10 pts)
- Real details from context (10 pts)

**ENGAGEMENT TRIGGER (15 points)**
- Strong ending (8 pts)
- Invites discussion (7 pts)

DEDUCTIONS:
- AI patterns found: -10 pts each
- Fabricated details: -15 pts
- Tweets over 280 chars: -5 pts each
- Generic CTA: -8 pts
- Hashtags in body: -5 pts

Return as JSON:
{{
  "score": 0-100,
  "breakdown": {{"hook": X, "flow": Y, ...}},
  "ready_to_post": true/false,
  "improvements_needed": ["specific fixes if score < target"],
  "revised_draft": "improved version if score < target (null if ready)"
}}
""")

# ==================== QUALITY CHECK (COMBINED: AI CRINGE + FACT CHECK) ====================

QUALITY_CHECK_PROMPT = dedent("""You are evaluating a Twitter thread. Your job: determine if this would get engagement or get scrolled past.

Thread: {post}

Evaluate on these axes (0-5):

1. HOOK STRENGTH
   - Does the first tweet grab attention immediately?
   - Is it specific with concrete details?
   - Does it create intrigue?

   Score 5: Provocative + specific + creates curiosity
   Score 3: Interesting but vague
   Score 0: Generic statement

2. THREAD FLOW
   - Does each tweet build on the previous one?
   - Is the progression logical?
   - Does it maintain momentum?

   Score 5: Each tweet advances argument naturally
   Score 3: Some tweets feel disconnected
   Score 0: Random thoughts stitched together

3. BREVITY + RATE OF REVELATION
   - Is each tweet under 280 characters?
   - Does each tweet reveal NEW information?
   - Zero fluff or unnecessary words?

   Score 5: Every tweet packs new value
   Score 3: Some tweets could be cut
   Score 0: Verbose, repetitive

4. PROOF/CREDIBILITY
   - Are there concrete examples or specifics?
   - Do claims feel real from user's context?
   - ZERO fabricated details?

   Score 5: Specific real examples
   Score 3: Vague claims
   Score 0: Made-up stories

5. ENGAGEMENT TRIGGER
   - Does thread end with question or CTA?
   - Does it invite replies?
   - Avoid passive endings

   Score 5: Strong engagement trigger
   Score 3: Weak question
   Score 0: No engagement trigger

CRITICAL AI TELLS (AUTO-DEDUCT 2 POINTS EACH):
- Contrast framing: "It's not X, it's Y" / "This isn't about X" / "not just X, but Y" / "rather than"
- Rule of Three: "Same X. Same Y. Over Z%." (three parallel fragments)
- Cringe questions: "The truth?" / "The result?" / "Sound familiar?"

CRITICAL: 280 CHARACTER VALIDATION (MANDATORY):
- Parse thread into individual tweets (split by numbering or line breaks)
- Count characters for EACH tweet
- If ANY tweet exceeds 280 characters → AUTO-DEDUCT 5 points AND flag as "high" severity issue
- Example issue format: {{"axis": "brevity", "severity": "high", "original": "Tweet 3 (312 chars)", "fix": "Split into two tweets or cut 32 chars"}}

VERIFICATION CHECK (use web_search):
- Names + titles + companies: "James Chen, Head of Growth at Clearbit"
- News stories, events, product launches: "Rick Beato YouTube AI filters"
- If found in thread → web_search to verify
- If verified → Note as "verified claim"
- If NOT verified:
  * Personal anecdotes/client stories → FLAG AS "NEEDS VERIFICATION" (severity: medium)
  * News reporting/industry events → FLAG AS "ADD SOURCE CITATION" (severity: low, suggest adding link)
  * Only flag as "FABRICATED" if claim is clearly false or contradicts verified info

SEARCH STRATEGY:
- Max 3 searches for efficiency
- Search: "[Full Name] [Company] [Title]" or "[Topic] [Event/News]"
- If no results → Check if it's newsworthy before flagging

Output JSON:
{{
  "scores": {{
    "hook": 3,
    "flow": 4,
    "brevity": 5,
    "proof": 5,
    "engagement": 4,
    "total": 21,
    "ai_deductions": 0
  }},
  "decision": "accept",  // accept (≥20) | revise (18-19) | reject (<18)
  "searches_performed": ["query 1", "query 2"],
  "issues": [
    {{
      "axis": "hook",
      "severity": "medium",
      "original": "AI is changing everything",
      "fix": "GPT-5 shows we've crossed the point where most people can't tell models apart",
      "impact": "Raises hook score from 3 to 5"
    }}
  ],
  "surgical_summary": "2 specific fixes would move this from score 18 to 21+",
  "threshold": 18,
  "meets_threshold": true
}}

Be surgical: don't rewrite the whole thing. Give 3-5 specific fixes that would raise the score.
""")

# ==================== CREATE CAROUSEL SLIDES ====================

CREATE_CAROUSEL_PROMPT = dedent("""Twitter doesn't support carousels like LinkedIn.

If user requests a carousel, suggest creating:
1. A thread (3-10 tweets) with the same content structure
2. A visual thread using images (requires external tool)

For now, default to creating a well-structured thread instead.
""")

# ==================== SEARCH VIRAL PATTERNS ====================

SEARCH_VIRAL_PATTERNS_PROMPT = dedent("""Analyze viral Twitter threads in this niche to find patterns.

Topic/Niche: {topic}
Industry: {industry}

SEARCH FOR PATTERNS IN:
1. **Hook styles** that get engagement
2. **Thread structures** that perform
3. **Engagement triggers** that drive replies
4. **Proof formats** (stats, stories, examples)
5. **Thread lengths** that work

ANALYZE:
- What makes people stop scrolling?
- What triggers quote tweets and replies?
- What formats get bookmarked?
- What threads get shared?

Return research findings as JSON:
{{
  "top_hooks": ["patterns found"],
  "winning_structures": ["format types"],
  "engagement_triggers": ["what works"],
  "examples": [
    {{"hook": "...", "engagement_reason": "why it worked"}}
  ]
}}

Note: This would ideally search real Twitter threads. For now, return best practices based on known patterns.
""")

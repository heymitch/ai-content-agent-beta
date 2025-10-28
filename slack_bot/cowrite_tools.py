"""
Co-Write Tools Module
Lazy-loaded tools for interactive content co-writing mode.
Only loaded when user explicitly requests "co-write" or "collaborate".
"""

import os
from claude_agent_sdk import tool

# ================== CO-WRITE GENERATION TOOLS ==================
# These tools allow the CMO to generate initial drafts using WRITE_LIKE_HUMAN_RULES

@tool(
    "generate_post_linkedin",
    "Generate LinkedIn post using WRITE_LIKE_HUMAN_RULES. Returns clean draft without quality analysis.",
    {"topic": str, "context": str}
)
async def generate_post_linkedin(args):
    """Generate LinkedIn post draft"""
    print(f"📝 generate_post_linkedin CALLED - Topic: {args.get('topic', 'N/A')[:50]}")
    import json
    from anthropic import Anthropic
    from prompts.linkedin_tools import WRITE_LIKE_HUMAN_RULES

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    topic = args.get('topic', '')
    context = args.get('context', '')

    prompt = f"""{WRITE_LIKE_HUMAN_RULES}

TASK: Write a LinkedIn post

Topic: {topic}
Context: {context}

LINKEDIN POST STRUCTURE:
- Hook (first 2-3 lines): Question, bold claim, or specific stat
- Body (150-300 words): One main idea with specific examples/numbers
- Call-to-action: Specific question or engagement trigger

CRITICAL RULES:
✗ NO contrast framing ("It's not X, it's Y")
✗ NO rule of three ("Same X. Same Y. Over Z%.")
✗ NO cringe questions ("The truth?" / "Sound familiar?")
✗ NO AI buzzwords (leverage, seamless, robust, game-changer)

Return ONLY the post text. No markdown formatting (**bold** or *italic*). No metadata or explanations."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    print(f"✅ generate_post_linkedin COMPLETED - Generated {len(response.content[0].text)} chars")
    return {"content": [{"type": "text", "text": response.content[0].text}]}


@tool(
    "generate_post_twitter",
    "Generate Twitter thread using WRITE_LIKE_HUMAN_RULES. Returns clean draft without quality analysis.",
    {"topic": str, "context": str}
)
async def generate_post_twitter(args):
    """Generate Twitter thread draft"""
    import json
    from anthropic import Anthropic
    from prompts.linkedin_tools import WRITE_LIKE_HUMAN_RULES

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    topic = args.get('topic', '')
    context = args.get('context', '')

    prompt = f"""{WRITE_LIKE_HUMAN_RULES}

TASK: Write a Twitter thread

Topic: {topic}
Context: {context}

TWITTER THREAD STRUCTURE:
- Tweet 1 (Hook): Bold claim, specific stat, or question (under 280 chars)
- Tweets 2-5: One idea per tweet, build on each other
- Final tweet: Recap + CTA

TWITTER-SPECIFIC RULES:
- Each tweet under 280 characters
- First tweet must hook (people decide in 2 seconds)
- Use line breaks for readability
- Numbers tweets (1/, 2/, 3/ etc.)

CRITICAL RULES:
✗ NO contrast framing ("It's not X, it's Y")
✗ NO rule of three
✗ NO cringe questions
✗ NO AI buzzwords

Return thread as numbered tweets. Format: "1/ [tweet]\\n\\n2/ [tweet]" etc."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return {"content": [{"type": "text", "text": response.content[0].text}]}


@tool(
    "generate_post_email",
    "Generate email newsletter using WRITE_LIKE_HUMAN_RULES. Returns clean draft without quality analysis.",
    {"topic": str, "context": str}
)
async def generate_post_email(args):
    """Generate email newsletter draft"""
    import json
    from anthropic import Anthropic
    from prompts.linkedin_tools import WRITE_LIKE_HUMAN_RULES

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    topic = args.get('topic', '')
    context = args.get('context', '')

    prompt = f"""{WRITE_LIKE_HUMAN_RULES}

TASK: Write an email newsletter

Topic: {topic}
Context: {context}

EMAIL NEWSLETTER STRUCTURE:
- Subject line: Specific, benefit-focused (under 60 chars)
- Opening: Personal, direct (2-3 sentences)
- Body: One main insight with examples (200-400 words)
- CTA: Clear next step (reply, click, try)

EMAIL-SPECIFIC RULES:
- Conversational tone (like talking to a friend)
- Short paragraphs (2-3 sentences max)
- Specific examples over theory
- One clear action at the end

CRITICAL RULES:
✗ NO contrast framing
✗ NO rule of three
✗ NO cringe questions
✗ NO AI buzzwords

Return format:
Subject: [subject line]

[email body]

CTA: [call to action]"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2500,
        messages=[{"role": "user", "content": prompt}]
    )

    return {"content": [{"type": "text", "text": response.content[0].text}]}


@tool(
    "generate_post_youtube",
    "Generate YouTube script using WRITE_LIKE_HUMAN_RULES. Returns clean draft without quality analysis.",
    {"topic": str, "context": str}
)
async def generate_post_youtube(args):
    """Generate YouTube script draft"""
    import json
    from anthropic import Anthropic
    from prompts.linkedin_tools import WRITE_LIKE_HUMAN_RULES

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    topic = args.get('topic', '')
    context = args.get('context', '')

    prompt = f"""{WRITE_LIKE_HUMAN_RULES}

TASK: Write a YouTube video script

Topic: {topic}
Context: {context}

YOUTUBE SCRIPT STRUCTURE:
- Title: Specific, searchable, benefit-focused
- Hook (first 15 seconds): Bold statement or question
- Intro (15-30 seconds): What viewers will learn
- Main content: 3-5 clear points with examples
- Outro: Recap + CTA (like, subscribe, comment)

YOUTUBE-SPECIFIC RULES:
- Write for speaking (contractions, natural rhythm)
- Include [B-ROLL] markers for visual suggestions
- Time estimates in parentheses
- Conversational, energetic tone

CRITICAL RULES:
✗ NO contrast framing
✗ NO rule of three
✗ NO cringe questions
✗ NO AI buzzwords

Return format:
Title: [video title]

HOOK (0:00-0:15):
[opening hook]

INTRO (0:15-0:45):
[introduction]

[Continue with timestamped sections]"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    return {"content": [{"type": "text", "text": response.content[0].text}]}


@tool(
    "generate_post_instagram",
    "Generate Instagram caption using WRITE_LIKE_HUMAN_RULES. Returns clean draft without quality analysis.",
    {"topic": str, "context": str}
)
async def generate_post_instagram(args):
    """Generate Instagram caption draft"""
    import json
    from anthropic import Anthropic
    from prompts.linkedin_tools import WRITE_LIKE_HUMAN_RULES

    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    topic = args.get('topic', '')
    context = args.get('context', '')

    prompt = f"""{WRITE_LIKE_HUMAN_RULES}

TASK: Write an Instagram caption

Topic: {topic}
Context: {context}

INSTAGRAM CAPTION STRUCTURE:
- Hook (first 125 chars): Must work in preview before "...more"
- Body (under 2,200 chars total): Short paragraphs, line breaks every 2-3 sentences
- Visual pairing: Add context the image/Reel can't show
- CTA: Specific engagement trigger
- Hashtags: 3-5 relevant tags at end

INSTAGRAM-SPECIFIC RULES:
- 2,200 character HARD LIMIT (includes hashtags)
- First 125 chars appear before "...more" (must create curiosity)
- Line breaks for mobile readability
- 1-2 strategic emojis (not spam)
- Reference visual naturally ("swipe", "above")

CRITICAL RULES:
✗ NO contrast framing ("It's not X, it's Y")
✗ NO rule of three ("Same X. Same Y. Over Z%.")
✗ NO cringe questions ("The truth?" / "Sound familiar?")
✗ NO AI buzzwords (game-changer, unlock, revolutionary)

Return ONLY the caption text with hashtags. No markdown formatting. No metadata."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return {"content": [{"type": "text", "text": response.content[0].text}]}


# ================== PLATFORM-SPECIFIC QUALITY CHECK TOOLS ==================
# These tools allow the CMO to directly check quality and apply fixes during co-writing

@tool(
    "quality_check_linkedin",
    "Evaluate LinkedIn post with 5-axis rubric, detect AI tells, verify facts with web search.",
    {"post": str}
)
async def quality_check_linkedin(args):
    """Quality check tool for LinkedIn posts"""
    from agents.linkedin_sdk_agent import quality_check as linkedin_quality_check
    return await linkedin_quality_check(args)


@tool(
    "quality_check_twitter",
    "Evaluate Twitter thread with 5-axis rubric, detect AI tells, verify facts with web search.",
    {"post": str}
)
async def quality_check_twitter(args):
    """Quality check tool for Twitter threads"""
    from agents.twitter_sdk_agent import quality_check as twitter_quality_check
    return await twitter_quality_check(args)


@tool(
    "quality_check_email",
    "Evaluate email newsletter with 5-axis rubric, detect AI tells, verify facts with web search.",
    {"post": str}
)
async def quality_check_email(args):
    """Quality check tool for email newsletters"""
    from agents.email_sdk_agent import quality_check as email_quality_check
    return await email_quality_check(args)


@tool(
    "quality_check_youtube",
    "Evaluate YouTube script with 5-axis rubric, detect AI tells, verify facts with web search.",
    {"post": str}
)
async def quality_check_youtube(args):
    """Quality check tool for YouTube scripts"""
    from agents.youtube_sdk_agent import quality_check as youtube_quality_check
    return await youtube_quality_check(args)


@tool(
    "quality_check_instagram",
    "Evaluate Instagram caption with 5-axis rubric (hook/visual/readability/proof/cta), detect AI tells, verify facts.",
    {"post": str}
)
async def quality_check_instagram(args):
    """Quality check tool for Instagram captions"""
    from agents.instagram_sdk_agent import quality_check as instagram_quality_check
    return await instagram_quality_check(args)


# ================== PLATFORM-SPECIFIC APPLY FIXES TOOLS ==================

@tool(
    "apply_fixes_linkedin",
    "Apply surgical fixes to LinkedIn post based on quality_check feedback and user requests.",
    {"post": str, "issues_json": str}
)
async def apply_fixes_linkedin(args):
    """Apply fixes tool for LinkedIn posts"""
    print(f"🔧 apply_fixes_linkedin CALLED with args: {list(args.keys())}")
    from agents.linkedin_sdk_agent import apply_fixes as linkedin_apply_fixes
    result = await linkedin_apply_fixes(args)
    print(f"✅ apply_fixes_linkedin COMPLETED")
    return result


@tool(
    "apply_fixes_twitter",
    "Apply surgical fixes to Twitter thread based on quality_check feedback and user requests.",
    {"post": str, "issues_json": str}
)
async def apply_fixes_twitter(args):
    """Apply fixes tool for Twitter threads"""
    from agents.twitter_sdk_agent import apply_fixes as twitter_apply_fixes
    return await twitter_apply_fixes(args)


@tool(
    "apply_fixes_email",
    "Apply surgical fixes to email newsletter based on quality_check feedback and user requests.",
    {"post": str, "issues_json": str}
)
async def apply_fixes_email(args):
    """Apply fixes tool for email newsletters"""
    from agents.email_sdk_agent import apply_fixes as email_apply_fixes
    return await email_apply_fixes(args)


@tool(
    "apply_fixes_youtube",
    "Apply surgical fixes to YouTube script based on quality_check feedback and user requests.",
    {"post": str, "issues_json": str}
)
async def apply_fixes_youtube(args):
    """Apply fixes tool for YouTube scripts"""
    from agents.youtube_sdk_agent import apply_fixes as youtube_apply_fixes
    return await youtube_apply_fixes(args)


@tool(
    "apply_fixes_instagram",
    "Apply surgical fixes to Instagram caption based on quality_check feedback and user requests.",
    {"post": str, "issues_json": str}
)
async def apply_fixes_instagram(args):
    """Apply fixes tool for Instagram captions"""
    from agents.instagram_sdk_agent import apply_fixes as instagram_apply_fixes
    return await instagram_apply_fixes(args)


def get_cowrite_tools():
    """
    Return all co-write tools for lazy loading.
    Only called when user explicitly requests co-write mode.
    """
    return [
        # Generation tools
        generate_post_linkedin,
        generate_post_twitter,
        generate_post_email,
        generate_post_youtube,
        generate_post_instagram,
        # Quality check tools
        quality_check_linkedin,
        quality_check_twitter,
        quality_check_email,
        quality_check_youtube,
        quality_check_instagram,
        # Apply fixes tools
        apply_fixes_linkedin,
        apply_fixes_twitter,
        apply_fixes_email,
        apply_fixes_youtube,
        apply_fixes_instagram,
    ]
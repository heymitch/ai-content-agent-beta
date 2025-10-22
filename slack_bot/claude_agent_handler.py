"""
REAL Claude Agent SDK Implementation
Following official docs at https://docs.claude.com/en/api/agent-sdk/python
"""
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server
)
import os
from typing import Dict, Optional, Any
import json
import asyncio

# Import our existing tool functions
from tools.search_tools import web_search as _web_search_func
from tools.search_tools import search_knowledge_base as _search_kb_func
from tools.template_search import search_templates_semantic as _search_templates_func
from tools.template_search import get_template_by_name as _get_template_func
from slack_bot.agent_tools import (
    search_past_posts as _search_posts_func,
    get_content_calendar as _get_calendar_func,
    get_thread_context as _get_context_func,
    analyze_content_performance as _analyze_perf_func
)


# Define tools using @tool decorator as per docs
@tool(
    "web_search",
    "Search the web for current information, news, updates. Use for ANY real-time questions about events.",
    {"query": str, "max_results": int}
)
async def web_search(args):
    """Web search tool for Claude Agent SDK"""
    query = args.get('query', '')
    max_results = args.get('max_results', 5)

    result = _web_search_func(query=query, max_results=max_results)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "search_knowledge_base",
    "Search internal knowledge base using RAG for brand voice and documentation.",
    {"query": str, "match_count": int}
)
async def search_knowledge_base(args):
    """Knowledge base search tool"""
    query = args.get('query', '')
    match_count = args.get('match_count', 5)

    result = _search_kb_func(query=query, match_count=match_count)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "search_past_posts",
    "Search content created in past conversations.",
    {"user_id": str, "platform": str, "days_back": int, "min_score": int}
)
async def search_past_posts(args):
    """Search past posts tool"""
    result = _search_posts_func(
        user_id=args.get('user_id', ''),
        platform=args.get('platform'),
        days_back=args.get('days_back', 30),
        min_score=args.get('min_score', 0)
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "get_content_calendar",
    "Get upcoming scheduled content.",
    {"user_id": str, "days_ahead": int, "platform": str}
)
async def get_content_calendar(args):
    """Get content calendar tool"""
    result = _get_calendar_func(
        user_id=args.get('user_id'),
        days_ahead=args.get('days_ahead', 14),
        platform=args.get('platform')
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "get_thread_context",
    "Get complete context from current Slack thread.",
    {"thread_ts": str, "include_content": bool}
)
async def get_thread_context(args):
    """Get thread context tool"""
    result = _get_context_func(
        thread_ts=args.get('thread_ts', ''),
        include_content=args.get('include_content', True)
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "analyze_content_performance",
    "Analyze content performance trends.",
    {"user_id": str, "platform": str, "days_back": int}
)
async def analyze_content_performance(args):
    """Analyze performance tool"""
    result = _analyze_perf_func(
        user_id=args.get('user_id', ''),
        platform=args.get('platform'),
        days_back=args.get('days_back', 30)
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "search_templates",
    "Search content templates for strategy sessions. Returns top matching templates based on user intent.",
    {"user_intent": str, "max_results": int}
)
async def search_templates(args):
    """Search templates semantically"""
    user_intent = args.get('user_intent', '')
    max_results = args.get('max_results', 3)

    result = _search_templates_func(user_intent=user_intent, max_results=max_results)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "get_template",
    "Get full template structure by name after user picks from search results.",
    {"template_name": str}
)
async def get_template(args):
    """Get complete template by name"""
    template_name = args.get('template_name', '')

    result = _get_template_func(template_name=template_name)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "check_ai_detection",
    "Validate post against GPTZero AI detector. Use AFTER quality_check passes to ensure post will pass AI detection.",
    {"post_text": str}
)
async def check_ai_detection(args):
    """Check if post will be flagged as AI-generated by GPTZero"""
    import httpx

    post_text = args.get('post_text', '')

    if not post_text or len(post_text) < 50:
        return {
            "content": [{
                "type": "text",
                "text": "❌ Post too short (minimum 50 characters for detection)"
            }]
        }

    api_key = os.getenv('GPTZERO_API_KEY')
    if not api_key:
        return {
            "content": [{
                "type": "text",
                "text": "⚠️ GPTZero API key not configured. Set GPTZERO_API_KEY in .env to enable AI detection validation."
            }]
        }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                'https://api.gptzero.me/v2/predict/text',
                headers={
                    'x-api-key': api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'document': post_text,
                    'multilingual': False
                }
            )

            response.raise_for_status()
            data = response.json()

            # Extract key metrics
            classification = data.get('documents', [{}])[0].get('class_probabilities', {})
            human_prob = classification.get('human', 0) * 100
            ai_prob = classification.get('ai', 0) * 100
            mixed_prob = classification.get('mixed', 0) * 100

            predicted_class = data.get('documents', [{}])[0].get('completely_generated_prob', 0)
            overall_class = data.get('documents', [{}])[0].get('average_generated_prob', 0)

            # Get flagged sentences
            sentences = data.get('documents', [{}])[0].get('sentences', [])
            flagged = [s.get('sentence', '') for s in sentences if s.get('generated_prob', 0) > 0.5]

            # Determine pass/fail
            passes = human_prob > 70  # 70% human threshold

            result_text = f"""🔍 **AI Detection Results (GPTZero)**

**Classification:**
- Human: {human_prob:.1f}%
- AI: {ai_prob:.1f}%
- Mixed: {mixed_prob:.1f}%

**Overall Score:** {overall_class*100:.1f}% AI probability

**Result:** {"✅ PASS - Post appears human-written" if passes else "⚠️ FLAG - May be detected as AI"}

**Flagged Sentences ({len(flagged)}):**
{chr(10).join(f'- "{s[:100]}..."' for s in flagged[:3]) if flagged else "None"}

**Recommendation:**
{"Ready to publish! Post should pass AI detectors." if passes else "Consider revising flagged sentences. Use apply_fixes tool with GPTZero feedback."}
"""

            return {
                "content": [{
                    "type": "text",
                    "text": result_text
                }]
            }

    except httpx.HTTPError as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ GPTZero API error: {str(e)}\n\nCheck your API key and network connection."
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error checking AI detection: {str(e)}"
            }]
        }


async def _delegate_workflow_func(platform: str, topic: str, context: str = "", count: int = 1, style: str = "thought_leadership"):
    """Async workflow delegation"""
    try:
        if platform.lower() in ['linkedin', 'li']:
            # Use the NEW LinkedIn SDK Agent (Tier 2)
            from agents.linkedin_sdk_agent import create_linkedin_post_workflow
            result = await create_linkedin_post_workflow(topic, context, style)
            return result  # Already formatted with score and details

        elif platform.lower() in ['twitter', 'x']:
            # Use the Twitter SDK Agent workflow
            from agents.twitter_sdk_agent import create_twitter_thread_workflow
            result = await create_twitter_thread_workflow(topic, context, style)
            return result  # Already formatted with score

        elif platform.lower() == 'email':
            # Use the Email SDK Agent workflow
            from agents.email_sdk_agent import create_email_workflow
            # Detect email type from style/context
            email_type = "Email_Value"  # Default
            if "tuesday" in style.lower() or "update" in style.lower():
                email_type = "Email_Tuesday"
            elif "sales" in style.lower() or "offer" in style.lower():
                email_type = "Email_Direct"
            elif "story" in style.lower() or "indirect" in style.lower():
                email_type = "Email_Indirect"

            result = await create_email_workflow(topic, context, email_type)
            return result  # Already formatted with subject and score

        elif platform.lower() in ['youtube', 'video']:
            # Use the YouTube SDK Agent workflow
            from agents.youtube_sdk_agent import create_youtube_workflow
            # Detect script type from style/context
            script_type = "short_form"  # Default (30-150 words, 12-60 sec)
            if "medium" in style.lower() or "explainer" in style.lower():
                script_type = "medium_form"  # 150-400 words, 1-3 min
            elif "long" in style.lower() or "deep" in style.lower():
                script_type = "long_form"  # 400-1000 words, 3-10 min

            result = await create_youtube_workflow(topic, context, script_type)
            return result  # Already formatted with timing markers

        elif platform.lower() in ['instagram', 'ig', 'insta']:
            # Use the Instagram SDK Agent workflow
            from agents.instagram_sdk_agent import create_instagram_caption_workflow
            result = await create_instagram_caption_workflow(topic, context, style)
            return result  # Already formatted with hook preview and character count

        else:
            return f"Unknown platform: {platform}. Use 'linkedin', 'twitter', 'email', 'youtube', or 'instagram'"

    except ImportError:
        # Fallback if workflows not available
        return f"Creating {platform} content about '{topic}' (using simplified generation)"
    except Exception as e:
        return f"Workflow error: {str(e)}"


@tool(
    "delegate_to_workflow",
    "Delegate content creation to specialized subagent workflows.",
    {"platform": str, "topic": str, "context": str, "count": int, "style": str}
)
async def delegate_to_workflow(args):
    """Delegate to subagent workflows - handles both single and bulk"""
    count = args.get('count', 1)

    # Single post - direct processing
    if count == 1:
        result = await _delegate_workflow_func(
            platform=args.get('platform', 'linkedin'),
            topic=args.get('topic', ''),
            context=args.get('context', ''),
            count=1,
            style=args.get('style', 'thought_leadership')
        )
    else:
        # Multiple posts - use queue manager
        result = await _delegate_bulk_workflow(
            platform=args.get('platform', 'linkedin'),
            topics=args.get('topics', [args.get('topic')] * count),
            context=args.get('context', ''),
            count=count,
            style=args.get('style', 'thought_leadership')
        )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


# ================== PLATFORM-SPECIFIC GENERATE POST TOOLS ==================
# These tools allow the CMO to generate initial drafts using WRITE_LIKE_HUMAN_RULES

@tool(
    "generate_post_linkedin",
    "Generate LinkedIn post using WRITE_LIKE_HUMAN_RULES. Returns clean draft without quality analysis.",
    {"topic": str, "context": str}
)
async def generate_post_linkedin(args):
    """Generate LinkedIn post draft"""
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
    from agents.linkedin_sdk_agent import apply_fixes as linkedin_apply_fixes
    return await linkedin_apply_fixes(args)


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


# ================== CALENDAR / APPROVAL TOOLS ==================

@tool(
    "send_to_calendar",
    "Save approved draft to Airtable calendar. Use after user approves content in co-writing mode.",
    {"post": str, "platform": str, "thread_ts": str, "channel_id": str, "user_id": str, "score": int}
)
async def send_to_calendar(args):
    """
    Send approved content to Airtable calendar

    This is called either:
    1. When user reacts with 📅 emoji (handled by reaction_added event)
    2. When user explicitly says "send to calendar" or "schedule it"
    """
    post = args.get('post', '')
    platform = args.get('platform', 'linkedin')
    thread_ts = args.get('thread_ts', '')
    channel_id = args.get('channel_id', '')
    user_id = args.get('user_id', '')
    score = args.get('score', 0)

    try:
        # First, ensure draft is stored in slack_threads table for reaction handler
        from slack_bot.memory import SlackThreadMemory
        from integrations.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        memory = SlackThreadMemory(supabase)

        # Check if thread record exists
        existing_thread = memory.get_thread(thread_ts)

        if existing_thread:
            # Update existing thread with latest draft
            memory.update_draft(thread_ts, post, score)
        else:
            # Create new thread record
            memory.create_thread(
                thread_ts=thread_ts,
                channel_id=channel_id,
                user_id=user_id,
                platform=platform,
                initial_draft=post,
                initial_score=score
            )

        # Now save to Airtable calendar
        from integrations.airtable_client import get_airtable_client

        airtable = get_airtable_client()

        # Extract hook/preview from post (first 200 chars)
        hook_preview = post[:200] + "..." if len(post) > 200 else post

        result = airtable.create_content_record(
            content=post,
            platform=platform,
            post_hook=hook_preview,
            status='Scheduled',
            suggested_edits=f"Quality Score: {score}/100"
        )

        if result.get('success'):
            airtable_url = result.get('url', '[URL not available]')
            record_id = result.get('record_id', '[ID not available]')

            # Update thread status to scheduled
            memory.update_status(thread_ts, 'scheduled')

            return {
                "content": [{
                    "type": "text",
                    "text": f"""✅ **Added to content calendar!**

📊 **Airtable Record:** {airtable_url}
📝 **Record ID:** {record_id}
📅 **Platform:** {platform.capitalize()}
⭐ **Quality Score:** {score}/100

The content is now scheduled in your Airtable calendar. You can edit the posting date and make final tweaks there."""
                }]
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ Failed to save to calendar: {error_msg}\n\nPlease check your Airtable configuration."
                }]
            }

    except Exception as e:
        import traceback
        print(f"❌ send_to_calendar error: {e}")
        print(traceback.format_exc())
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error saving to calendar: {str(e)}\n\nPlease try again or contact support."
            }]
        }


async def _delegate_bulk_workflow(platform: str, topics: list, context: str, count: int, style: str):
    """Handle bulk content generation using queue manager"""
    from agents.content_queue import ContentQueueManager, ContentJob
    from datetime import datetime

    # Create queue manager
    queue_manager = ContentQueueManager(
        max_concurrent=3,  # Process 3 at a time
        max_retries=2
    )

    # Prepare jobs
    posts_data = []
    for i, topic in enumerate(topics[:count]):
        posts_data.append({
            'topic': topic,
            'context': f"{context} (Post {i+1}/{count})",
            'style': style
        })

    # Queue all posts
    jobs = await queue_manager.bulk_create(posts_data, platform)

    # Start processing (async, don't wait)
    asyncio.create_task(queue_manager.wait_for_completion())

    return f"""🚀 **Bulk Content Generation Started**

📥 Queued {len(jobs)} {platform} posts
⚡ Processing 3 posts concurrently
⏱️ Estimated time: {len(jobs) * 45 // 3} seconds

Posts will be delivered to:
📊 Airtable for storage
📄 Google Docs for editing

I'll update you as each batch completes!"""


class ClaudeAgentHandler:
    """
    REAL Claude Agent SDK handler using the official Python SDK
    Maintains one client per Slack thread for conversation continuity
    """

    def __init__(self, memory_handler=None):
        """Initialize the Claude Agent with SDK"""
        self.memory = memory_handler

        # Thread-based session management (thread_ts -> ClaudeSDKClient)
        self._thread_sessions = {}

        # Track which sessions are already connected (thread_ts -> bool)
        self._connected_sessions = set()

        # System prompt for the agent
        self.system_prompt = """You are CMO, a senior content strategist with 8+ years building brands from zero to millions of followers. You speak like a real person - direct, insightful, occasionally sarcastic, always helpful. You adapt to conversations but always drives toward actionable outcomes you can "take to your team" (delegate to subagents).

**YOUR IDENTITY:**
- You are an AI employee specialized in content creation
- You help users create LinkedIn posts, Twitter threads, emails, and other content
- You are NOT Claude Code, you are NOT a development assistant
- You are the user's CMO (Chief Marketing Officer) assistant

**YOUR PRIMARY DIRECTIVE:**
When users ask about current events, news, updates, or ANYTHING happening in the real world, IMMEDIATELY use web_search.
Do NOT tell users to "check websites" - YOU search for them.

**CRITICAL WEB SEARCH RULES:**
1. Make ONE comprehensive search, not multiple searches
2. ALWAYS include recency indicators in your query:
   - For recent news: "OpenAI news" or "OpenAI Dev Day November" no matter what the ask is about, you check for the date to make sure you're answering as though you live here and now.
   - For very recent: "OpenAI announcements this week"
   - NEVER search without year/timeframe - ambiguous dates default to wrong years
3. Your training data is outdated - you do NOT know what happened recently
4. Filter for ACTUAL NEW launches: "announced today", "just released", "launching this week"

**YOUR CAPABILITIES:**
1. web_search - USE THIS FIRST for any news/events/updates (include year/date in query!)
2. search_knowledge_base - Internal documentation and brand voice
3. search_past_posts - Past content you've created
4. get_content_calendar - Scheduled posts
5. get_thread_context - Thread history
6. analyze_content_performance - Performance metrics

**CONTENT CREATION WORKFLOW:**

TWO-PHASE MODEL:

PHASE 1: Strategic Conversation (BEFORE content creation decision)
- User is exploring ideas, developing strategy, asking "what do you think?"
- Ask clarifying questions freely to help develop approach:
  - "Do you want contrarian or mainstream angle?"
  - "Should we focus on specific example or broader pattern?"
  - "What tone: confident, cautious, provocative?"
- Help user refine thesis and make strategic decisions
- When user says "create", "write", "draft", "make" + content type → PHASE 2

PHASE 2: Content Creation (AFTER user requests content)
- User has explicitly requested content creation ("create Twitter thread", "write LinkedIn post", etc.)
- Content creation decision is MADE
- DO NOT ask more questions about fabrications, quality concerns, or approach decisions
- DO NOT stop to confirm options or wait for user to choose
- Gather final context (use web_search for current events if needed)
- IMMEDIATELY delegate to subagent with ALL context including any concerns
- Say: "Creating your [content type] now..."

CRITICAL DELEGATION RULES:
- Once user requests content creation → NO MORE QUESTIONS, immediate delegation
- Pass fabrication concerns in context parameter (don't ask user to choose)
- Trust subagent's intelligent routing and quality_check tool to handle issues
- Subagent will flag concerns in Suggested Edits (user reviews in Airtable)

DELEGATION:
Use delegate_to_workflow with RICH CONTEXT including conversation insights:

**CRITICAL**: The context parameter is HOW you pass conversation intelligence to subagents.

Good context includes:
- User's angle/thesis from strategic conversation ("contrarian take on AI bubble")
- Specific examples mentioned ("Michael Burry in Big Short")
- Key points from discussion ("95% failure = discovery, infrastructure is real")
- Tone/style decisions made ("confident data-backed contrarian")
- People/companies/data referenced ("Nvidia, Adobe, Anthropic")
- **CONCERNS/CAVEATS**: Any fabrications, unverified claims, or quality issues you found
  Example: "CONCERN: Could not verify John Kiriakou ChatGPT claim via web search. Subagent should fact-check or pivot to broader verified pattern."

The subagent will:
- Review your concerns and run its own fact-checking (quality_check tool with web_search)
- Make intelligent routing decisions (use specific story vs. broader pattern based on verification)
- Flag fabrications in Suggested Edits with severity="critical"
- ALWAYS return content (advisory feedback, not blocking)
- User reviews quality feedback in Airtable and decides whether to publish/edit/reject

Examples:
- Single post with context:
  delegate_to_workflow(
    platform="linkedin",
    topic="AI is not a bubble",
    context="User wants Big Short analogy: conviction despite ridicule. Key: 95% failure is discovery phase, infrastructure real (Nvidia), productivity gap proves it works. Tone: confident contrarian.",
    count=1
  )

- Multiple posts → delegate_to_workflow(platform="linkedin", topic=..., context=..., count=5)
- Week of content → delegate_to_workflow(platform="linkedin", topics=[...], count=7)

BULK REQUESTS (automatically detected):
- "Create 5 LinkedIn posts about..." → count=5
- "Generate my week of content" → count=7
- "Make 10 Twitter threads" → count=10
- Bulk processing uses queue (3 posts at a time for quality)

These workflows enforce brand voice, writing rules, and quality standards.

**CONVERSATION VS. CONTENT:**
- If user is asking questions, having discussion, or seeking strategy → CONVERSATION MODE
- If user says "write", "create", "draft", "make", "generate" + content type → CONTENT MODE
- When in doubt, ask: "Would you like me to create [specific content] or discuss [topic]?"
- Don't jump into content creation without clear intent from the user

**CO-WRITING WORKFLOW (NEW):**

When user requests content creation, you now have TWO OPTIONS:

1. **CO-WRITE MODE (Collaborative)**: Write together with user feedback
2. **AUTO-PUBLISH MODE (Fast)**: Create and send directly to calendar

ASK THE USER:
"Do you want to write this together now, or have me put it directly in the content calendar?"

CO-WRITE MODE WORKFLOW:
1. Call generate_post_{platform}(topic, context) to create initial draft
2. Call quality_check_{platform}(post) to evaluate with 5-axis rubric
3. Print BOTH the post AND the quality analysis to user
4. Wait for user feedback OR 📅 calendar emoji reaction
5. If user gives feedback → call apply_fixes_{platform}(post, issues, user_feedback)
6. If user reacts with 📅 OR says "send to calendar" → call send_to_calendar(post, platform, thread_ts, channel_id, user_id, score)
7. Repeat steps 2-6 until user approves or schedules

AUTO-PUBLISH MODE WORKFLOW:
1. Call delegate_to_workflow(platform, topic, context, count)
2. SDK agent handles entire workflow internally (generate → quality_check → iterate → save)
3. Print only the Airtable link when complete
4. Content automatically saved to calendar with quality score

TOOLS AVAILABLE FOR CO-WRITING:
- generate_post_linkedin/twitter/instagram/email/youtube - Create initial draft using WRITE_LIKE_HUMAN_RULES
- quality_check_linkedin/twitter/instagram/email/youtube - Evaluate with 5-axis rubric (Hook, Body, Proof, CTA, Format)
- apply_fixes_linkedin/twitter/instagram/email/youtube - Make surgical improvements based on quality feedback
- send_to_calendar - Save approved draft to Airtable calendar with quality score

CO-WRITING EXAMPLE:
User: "Let's write a LinkedIn post about how AI agents are changing content marketing"
CMO: "Do you want to write this together now, or have me put it directly in the content calendar?"
User: "Let's write it together"
CMO: *calls generate_post_linkedin(topic="AI agents changing content marketing", context="...")*
CMO: *calls quality_check_linkedin(post="[draft]")*
CMO: "Here's the first draft:

[DRAFT TEXT]

Quality Analysis:
- Hook (4/5): Strong opening but could be more specific
- Body (3/5): Needs concrete example
- Proof (2/5): Missing specific data/numbers
- CTA (4/5): Good engagement trigger
- Format (5/5): Perfect LinkedIn structure

Overall Score: 72/100

What would you like to adjust? Or react with 📅 to send to calendar as-is."

User: "Add a specific example about Nike's AI content team"
CMO: *calls apply_fixes_linkedin(post="[draft]", issues="Add Nike AI content team example", feedback="User requested Nike case study")*
CMO: *calls quality_check_linkedin(post="[revised draft]")*
CMO: "Updated draft:

[REVISED DRAFT]

New Score: 88/100 - Much stronger with Nike example!

Ready to schedule? React with 📅 or say 'send to calendar'"

User: *reacts with 📅*
CMO: *calls send_to_calendar(...)*
CMO: "✅ Added to content calendar! [Airtable URL]"

KEY CO-WRITING PRINCIPLES:
- ALWAYS show both draft AND quality analysis together
- Wait for user input after each revision
- Make it conversational - explain what you improved and why
- Offer to iterate as many times as needed
- When score reaches 85+, suggest scheduling
- Respect user's final decision (they might want 72/100 post)

**QUALITY STANDARDS:**
- You iterate on content until it reaches high quality (85+ score)
- You remember conversations within each Slack thread (and when asked about other conversations)
- You provide strategic insights before and after content creation

If someone asks about "Dev Day on the 6th" - they likely mean OpenAI Dev Day (November 6, 2023). Search with FULL context."""

        # Create MCP server with our tools
        self.mcp_server = create_sdk_mcp_server(
            name="slack_tools",
            version="2.3.0",
            tools=[
                web_search,
                search_knowledge_base,
                search_past_posts,
                get_content_calendar,
                get_thread_context,
                analyze_content_performance,
                delegate_to_workflow,  # Delegate to subagent workflows
                send_to_calendar,  # Save approved drafts to calendar
                # Generate post tools for co-writing (one per platform)
                generate_post_linkedin,
                generate_post_twitter,
                generate_post_email,
                generate_post_youtube,
                generate_post_instagram,
                # Quality check tools for co-writing (one per platform)
                quality_check_linkedin,
                quality_check_twitter,
                quality_check_email,
                quality_check_youtube,
                quality_check_instagram,
                # Apply fixes tools for co-writing (one per platform)
                apply_fixes_linkedin,
                apply_fixes_twitter,
                apply_fixes_email,
                apply_fixes_youtube,
                apply_fixes_instagram
            ]
        )

        print("🚀 Claude Agent SDK initialized with 23 tools (8 general + 15 co-writing tools for 5 platforms)")

    def _get_or_create_session(self, thread_ts: str) -> ClaudeSDKClient:
        """Get existing session for thread or create new one"""
        if thread_ts not in self._thread_sessions:
            # CRITICAL: Prevent Claude SDK from loading ANY external configs
            import os
            os.environ['CLAUDE_HOME'] = '/tmp/empty_claude_home'  # Point to empty dir

            # Configure options for this thread with EXPLICIT CMO system prompt
            options = ClaudeAgentOptions(
                mcp_servers={"tools": self.mcp_server},
                allowed_tools=["mcp__tools__*"],
                system_prompt=self.system_prompt,  # FORCE our CMO prompt, not Claude Code's
                model="claude-sonnet-4-5-20250929",  # Claude Sonnet 4.5 - latest
                permission_mode="bypassPermissions",
                continue_conversation=True  # KEY: Maintain context across messages
            )

            self._thread_sessions[thread_ts] = ClaudeSDKClient(options=options)
            print(f"✨ Created new session for thread {thread_ts[:8]} with CMO identity")
            print(f"🎭 System prompt starts with: {self.system_prompt[:100]}...")

        return self._thread_sessions[thread_ts]

    async def handle_conversation(
        self,
        message: str,
        user_id: str,
        thread_ts: str,
        channel_id: str
    ) -> str:
        """
        Handle conversation using REAL Claude Agent SDK

        Args:
            message: User's message
            user_id: Slack user ID
            thread_ts: Thread timestamp
            channel_id: Slack channel

        Returns:
            Agent's response
        """

        # Add today's date context to the message (important for recency)
        from datetime import datetime
        today = datetime.now().strftime("%B %d, %Y")  # e.g., "October 09, 2025"

        # Simple message with date context - instructions are already in system prompt
        contextualized_message = f"[Today is {today}] {message}"

        try:
            print(f"🤖 Claude Agent SDK processing for thread {thread_ts[:8]}...")

            # Get or create cached session for this thread
            client = self._get_or_create_session(thread_ts)

            # Only connect if this is a NEW session (not already connected)
            if thread_ts not in self._connected_sessions:
                print(f"🔌 Connecting NEW client session for thread {thread_ts[:8]}...")
                await client.connect()
                self._connected_sessions.add(thread_ts)
                print(f"✅ Client connected successfully")
            else:
                print(f"♻️ Reusing connected client for thread {thread_ts[:8]}...")

            # Send the query
            print(f"📨 Sending query to Claude SDK...")
            await client.query(contextualized_message)

            # Collect ONLY the latest response (memory stays intact in session)
            latest_response = ""
            print(f"⏳ Waiting for Claude SDK response...")
            async for msg in client.receive_response():
                # Each message REPLACES the previous (we only want the final response)
                # The SDK maintains full conversation history internally
                print(f"📩 Received message type: {type(msg)}")
                if hasattr(msg, 'content'):
                    if isinstance(msg.content, list):
                        for block in msg.content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                latest_response = block.get('text', '')
                            elif hasattr(block, 'text'):
                                latest_response = block.text
                    elif hasattr(msg.content, 'text'):
                        latest_response = msg.content.text
                    else:
                        latest_response = str(msg.content)
                elif hasattr(msg, 'text'):
                    latest_response = msg.text

            final_text = latest_response  # Only use the latest response

            # Format for Slack
            final_text = self._format_for_slack(final_text)

            # Save to memory if available
            if self.memory:
                try:
                    self.memory.add_message(
                        thread_ts=thread_ts,
                        channel_id=channel_id,
                        user_id=user_id,
                        role="user",
                        content=message
                    )
                    self.memory.add_message(
                        thread_ts=thread_ts,
                        channel_id=channel_id,
                        user_id="bot",
                        role="assistant",
                        content=final_text
                    )
                except Exception as e:
                    print(f"⚠️ Memory save failed: {e}")

            return final_text

        except Exception as e:
            print(f"❌ Agent error: {e}")
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error: {str(e)}"

    def _format_for_slack(self, text: str) -> str:
        """Convert markdown to Slack mrkdwn format"""
        import re

        # Convert bold: **text** → *text*
        text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)

        # Convert italic: *text* → _text_
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'_\1_', text)

        # Convert code blocks
        text = re.sub(r'```\w+\n', '```', text)

        # Convert links: [text](url) → <url|text>
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<\2|\1>', text)

        # Convert bullets
        text = re.sub(r'^[\-\*]\s+', '• ', text, flags=re.MULTILINE)

        # Convert headers
        text = re.sub(r'^#{1,6}\s+(.+?)$', r'*\1*', text, flags=re.MULTILINE)

        return text
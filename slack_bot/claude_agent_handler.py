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
import hashlib
import time

# Import our existing tool functions
from tools.search_tools import web_search as _web_search_func
from tools.search_tools import search_knowledge_base as _search_kb_func
from tools.company_documents import search_company_documents as _search_company_docs_func
from tools.template_search import search_templates_semantic as _search_templates_func
from tools.template_search import get_template_by_name as _get_template_func
from slack_bot.agent_tools import (
    search_past_posts as _search_posts_func,
    get_content_calendar as _get_calendar_func,
    get_thread_context as _get_context_func,
    analyze_content_performance as _analyze_perf_func
)
from agents.batch_orchestrator import (
    execute_sequential_batch,
    create_batch_plan,
    execute_single_post_from_plan,
    diversify_topics
)
from agents.context_manager import ContextManager

# NEW: Global variable to store current handler instance for tool access
# This allows tools to access slack_client and conversation context
_current_handler = None


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
    "search_company_documents",
    "Search user-uploaded company documents (case studies, testimonials, product docs). Use BEFORE asking user for context.",
    {"query": str, "match_count": int, "document_type": str}
)
async def search_company_documents(args):
    """Search company documents for context enrichment"""
    query = args.get('query', '')
    match_count = args.get('match_count', 3)
    document_type = args.get('document_type')  # Optional: 'case_study', 'testimonial', 'product_doc'

    result = _search_company_docs_func(
        query=query,
        match_count=match_count,
        document_type=document_type
    )

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
        # Multiple posts - use queue manager with Slack progress updates
        # NEW: Get Slack context from global handler
        global _current_handler
        slack_client = None
        channel = None
        thread_ts = None

        if _current_handler and _current_handler.slack_client:
            # Get conversation context for current thread
            # Find the current thread by checking which thread has been most recently accessed
            if _current_handler._conversation_context:
                # Get the most recent context (last item)
                latest_context = list(_current_handler._conversation_context.values())[-1]
                slack_client = _current_handler.slack_client
                channel = latest_context['channel']
                thread_ts = latest_context['thread_ts']

        result = await _delegate_bulk_workflow(
            platform=args.get('platform', 'linkedin'),
            topics=args.get('topics', [args.get('topic')] * count),
            context=args.get('context', ''),
            count=count,
            style=args.get('style', 'thought_leadership'),
            slack_client=slack_client,  # NEW: Pass Slack client
            channel=channel,  # NEW: Pass channel
            thread_ts=thread_ts  # NEW: Pass thread_ts
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


# ================== BATCH ORCHESTRATION TOOLS ==================

@tool(
    "plan_content_batch",
    "Create a structured plan for N posts across platforms. Returns plan ID for tracking.",
    {"posts": list, "description": str}
)
async def plan_content_batch(args):
    """
    Create a batch content plan

    Args:
        posts: List of post specs [{"platform": "linkedin", "topic": "...", "context": "..."}]
        description: High-level description of the batch (e.g., "Week of AI content")

    Returns:
        Plan summary with ID
    """
    posts_list = args.get('posts', [])
    description = args.get('description', 'Content batch')

    if not posts_list or len(posts_list) == 0:
        return {
            "content": [{
                "type": "text",
                "text": "❌ No posts provided. Please specify at least one post in the batch."
            }]
        }

    try:
        plan = create_batch_plan(posts_list, description)

        # Format plan summary
        summary = f"""✅ **Batch Plan Created**

📋 **Plan ID:** {plan['id']}
📝 **Description:** {plan['description']}
📊 **Total Posts:** {len(plan['posts'])}

**Posts:**
"""

        for i, post_spec in enumerate(plan['posts'], 1):
            summary += f"\n{i}. {post_spec['platform'].capitalize()}: {post_spec['topic'][:60]}..."

        summary += f"""

**Estimated Time:** {len(plan['posts']) * 1.5:.0f} minutes (sequential execution)

Use execute_post_from_plan to create each post with accumulated learnings."""

        return {
            "content": [{
                "type": "text",
                "text": summary
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error creating plan: {str(e)}"
            }]
        }


@tool(
    "execute_post_from_plan",
    "Execute a single post from the batch plan. Accumulates learnings from previous posts.",
    {"plan_id": str, "post_index": int}
)
async def execute_post_from_plan(args):
    """
    Execute one post from a batch plan

    Args:
        plan_id: ID from plan_content_batch
        post_index: Which post to create (0-indexed)

    Returns:
        Post result with updated learnings
    """
    plan_id = args.get('plan_id', '')
    post_index = args.get('post_index', 0)

    if not plan_id:
        return {
            "content": [{
                "type": "text",
                "text": "❌ No plan_id provided. Create a plan first with plan_content_batch."
            }]
        }

    try:
        result = await execute_single_post_from_plan(plan_id, post_index)

        if result.get('error'):
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ {result['error']}"
                }]
            }

        # Format result
        output = f"""✅ **Post {post_index + 1} Complete**

📊 **Quality Score:** {result.get('score', 'N/A')}/25
🎯 **Platform:** {result.get('platform', 'unknown').capitalize()}
📝 **Hook Preview:** {result.get('hook', 'N/A')[:100]}...
📎 **Airtable:** {result.get('airtable_url', 'N/A')}

**Learnings Applied:**
{result.get('learnings_summary', 'First post in batch - no prior learnings')}

**Next:** Execute post {post_index + 2} to continue the batch."""

        return {
            "content": [{
                "type": "text",
                "text": output
            }]
        }

    except Exception as e:
        import traceback
        print(f"❌ execute_post_from_plan error: {e}")
        print(traceback.format_exc())
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error executing post: {str(e)}"
            }]
        }


@tool(
    "compact_learnings",
    "Compress learnings from last 10 posts into key insights. Call every 10 posts.",
    {"plan_id": str}
)
async def compact_learnings(args):
    """
    Compact context manager learnings

    Args:
        plan_id: ID from plan_content_batch

    Returns:
        Compaction summary
    """
    plan_id = args.get('plan_id', '')

    if not plan_id:
        return {
            "content": [{
                "type": "text",
                "text": "❌ No plan_id provided."
            }]
        }

    try:
        # Get context manager for this plan
        from agents.batch_orchestrator import get_context_manager

        context_mgr = get_context_manager(plan_id)

        if not context_mgr:
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ No context manager found for plan {plan_id}"
                }]
            }

        # Run compaction
        await context_mgr.compact()

        stats = context_mgr.get_stats()

        return {
            "content": [{
                "type": "text",
                "text": f"""✅ **Learnings Compacted**

📊 **Stats:**
- Total posts: {stats['total_posts']}
- Average score: {stats['average_score']:.1f}/25
- Posts since last compact: {stats['posts_since_compact']}

Context compressed from ~20k tokens to ~2k tokens.
Quality insights preserved for next batch of posts."""
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error compacting learnings: {str(e)}"
            }]
        }


@tool(
    "checkpoint_with_user",
    "Send checkpoint update to user at 10/20/30/40 post intervals. Shows progress stats.",
    {"plan_id": str, "posts_completed": int}
)
async def checkpoint_with_user(args):
    """
    Send checkpoint update

    Args:
        plan_id: ID from plan_content_batch
        posts_completed: Number of posts finished

    Returns:
        Checkpoint message
    """
    plan_id = args.get('plan_id', '')
    posts_completed = args.get('posts_completed', 0)

    if not plan_id:
        return {
            "content": [{
                "type": "text",
                "text": "❌ No plan_id provided."
            }]
        }

    try:
        from agents.batch_orchestrator import get_context_manager

        context_mgr = get_context_manager(plan_id)

        if not context_mgr:
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ No context manager found for plan {plan_id}"
                }]
            }

        stats = context_mgr.get_stats()

        # Calculate quality trend
        if len(stats['scores']) >= 2:
            first_score = stats['scores'][0]
            recent_avg = sum(stats['scores'][-5:]) / len(stats['scores'][-5:])
            trend = "📈 Improving" if recent_avg > first_score else "📊 Stable"
        else:
            trend = "🆕 Just started"

        checkpoint_msg = f"""🎯 **Checkpoint: {posts_completed} Posts Complete**

📊 **Progress Stats:**
- Average quality: {stats['average_score']:.1f}/25
- Quality trend: {trend}
- Estimated time remaining: {(stats['total_posts'] - posts_completed) * 1.5:.0f} min

**Recent Learnings:**
{stats.get('recent_learnings', 'Building quality patterns...')}

Continue creating posts - quality is improving with each iteration!"""

        return {
            "content": [{
                "type": "text",
                "text": checkpoint_msg
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error creating checkpoint: {str(e)}"
            }]
        }


# ================== BATCH CONTROL TOOLS (Phase 6A) ==================
# NEW: Cancel and status tools for bulk generation

@tool(
    "cancel_batch",
    "Cancel an active bulk content generation job. In-progress posts will complete, queued posts will be cancelled.",
    {"plan_id": str}
)
async def cancel_batch_tool(args):
    """
    Cancel batch tool - allows users to stop bulk generation mid-execution

    Args:
        plan_id: The batch plan ID to cancel

    Returns:
        Cancellation status
    """
    from prompts.batch_tools import cancel_batch
    plan_id = args.get('plan_id', '')

    if not plan_id:
        return {
            "content": [{
                "type": "text",
                "text": "❌ No plan_id provided. Use get_batch_status() to see active batches."
            }]
        }

    result = cancel_batch(plan_id)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "get_batch_status",
    "Check status of bulk content generation. Shows progress, completed/failed/pending counts, and time estimates.",
    {"plan_id": str}
)
async def get_batch_status_tool(args):
    """
    Get batch status tool - shows real-time progress of bulk generation

    Args:
        plan_id: Optional - specific batch ID to check. If empty, shows all active batches.

    Returns:
        Status information with progress bar
    """
    from prompts.batch_tools import get_batch_status
    plan_id = args.get('plan_id', None)

    result = await get_batch_status(plan_id)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


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
            status='Draft',  # Use 'Draft' to match SDK agents (user can change in Airtable)
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


async def _delegate_bulk_workflow(
    platform: str,
    topics: list,
    context: str,
    count: int,
    style: str,
    slack_client=None,  # NEW: Pass Slack client for progress updates
    channel: str = None,  # NEW: Channel ID
    thread_ts: str = None  # NEW: Thread timestamp
):
    """Handle bulk content generation using queue manager"""
    from agents.content_queue import ContentQueueManager, ContentJob
    from datetime import datetime

    # Create queue manager with Slack integration
    queue_manager = ContentQueueManager(
        max_concurrent=3,  # Process 3 at a time
        max_retries=2,
        slack_client=slack_client,  # NEW: Pass Slack client
        slack_channel=channel,  # NEW: Pass channel
        slack_thread_ts=thread_ts  # NEW: Pass thread_ts
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

    def __init__(self, memory_handler=None, slack_client=None):
        """Initialize the Claude Agent with SDK"""
        self.memory = memory_handler
        self.slack_client = slack_client  # NEW: Store slack_client for progress updates

        # Thread-based session management (thread_ts -> ClaudeSDKClient)
        self._thread_sessions = {}

        # Track which sessions are already connected (thread_ts -> bool)
        self._connected_sessions = set()

        # Track current conversation context for tools (thread_ts -> {channel, thread_ts})
        self._conversation_context = {}  # NEW: For Slack progress updates

        # Session version tracking for cache invalidation
        self._session_prompt_versions = {}  # thread_ts -> prompt hash
        self._session_created_at = {}  # thread_ts -> timestamp

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
3. search_company_documents - User-uploaded docs (case studies, testimonials, product docs) - USE BEFORE asking for context
4. search_past_posts - Past content you've created
5. get_content_calendar - Scheduled posts
6. get_thread_context - Thread history
7. analyze_content_performance - Performance metrics

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

**SPECIAL: Batch Content Requests (5+ posts)**
When user requests 5+ posts, PROACTIVELY search company documents BEFORE asking questions:

1. **Immediate Search:**
   Call search_company_documents(query="[topic] case studies examples testimonials")

2. **Evaluate Results:**
   - **Rich (3+ docs):** "Found [N] company docs about [topic]. Creating [N]-post plan with this context..."
   - **Medium (1-2 docs):** "Found [N] doc(s). Quick question: any specific [examples/experiences] to add?"
   - **Sparse (0 docs + vague topic):** Ask for context anchors OR offer thought leadership

3. **Context Anchor Request (Sparse Context Only):**
   "I can create [N] posts about [topic], but to avoid generic content, I need context anchors.

   Quick questions (2 minutes):

   1. **Personal Experience:** What's ONE specific way you've used/observed [topic]?
      Example: 'I replaced 3 workflows with one agent, saved 15 hours/week'

   2. **Specific Examples:** Any companies, people, or products you have opinions on?
      Example: 'ChatGPT vs Claude' or 'Adobe Firefly vs Midjourney'

   3. **Concrete Observations:** What pattern have you noticed that others miss?
      Example: 'I see 10 posts a day with the same hook structure'

   Give me 1-2 for each, and I'll create [N] unique posts with variety.

   OR: Say 'skip' and I'll create thought leadership posts (idea-driven, shorter, no proof claims)."

4. **User Response Handling:**
   - Provides anchors → Distribute across batch, create plan
   - Says "skip" → Use thought leadership approach (see below)
   - Provides topic → Use for proof posts

**Thought Leadership Fallback (Sparse Context + Skip):**
When NO company docs AND user skips questions:
- Post length: 800-1000 chars (vs 1200-1500)
- Content type: Idea-driven, opinion-based
- Framing: "I believe X because Y" (explicit opinion)
- FORBIDDEN: Hallucinated stats ("Studies show..."), fake examples ("Sarah Chen...")
- Focus: Frameworks, predictions, contrarian takes, observations

**Context Anchor Distribution:**
If user provides 3 anchors for 15 posts:
- Posts 1-5: Anchor 1 (personal experience) with variations
- Posts 6-10: Anchor 2 (specific examples) with variations
- Posts 11-15: Anchor 3 (observations) with variations

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

**CRITICAL: TWO CONTENT CREATION MODES**

When user requests content creation, you have TWO distinct modes:

**MODE 1: CO-WRITE (Collaborative, Iterative)**
- User wants to see drafts, give feedback, iterate together
- Always 1 post at a time
- Interactive loop until user approves
- Tools: generate_post_{platform}, quality_check_{platform}, apply_fixes_{platform}, send_to_calendar

**MODE 2: BATCH (Automated, Strategic)**
- User wants "direct to calendar" / auto-publish
- Works for ANY count (1, 5, 15, 50 posts - no threshold)
- Sequential execution with learning accumulation
- Real-time progress updates, cancel/status tools available
- Tools: plan_content_batch, execute_post_from_plan, cancel_batch, get_batch_status

**HOW TO DECIDE:**
When user requests content, ASK:
"Do you want to write this together now (co-write mode), or have me put it directly in the content calendar (batch mode)?"

**User says "together" / "co-write" / "let's iterate":**
→ Use CO-WRITE MODE (see workflow below)

**User says "direct to calendar" / "auto-publish" / "just create":**
→ Use BATCH MODE (see workflow below)

**CRITICAL RULES:**
1. **NEVER create multiple posts inline** and concatenate them
   - ❌ WRONG: Generate 3 posts in conversation, combine, save as one Airtable record
   - ✅ RIGHT: Use batch orchestration tools (plan_content_batch + execute_post_from_plan)
2. Each post MUST be created separately to get separate Airtable rows
3. Parse count from user request: "3 posts" → count=3, "week of content" → count=7, "month" → count=30

**BATCH MODE WORKFLOW:**

When user chooses "direct to calendar" (for ANY post count):

**STEP 1: PLAN REVISIONS (CRITICAL - Prevents Duplicates)**

When user requests changes to a plan BEFORE execution:
- ❌ WRONG: Create a new plan with 9 posts (7 original + 2 edits)
- ✅ RIGHT: Update the existing plan in conversation, maintain count of 7

EXAMPLE:
User: "Create a week of LinkedIn content"
CMO: "Here's a plan for 7 posts:
  1. AI ethics
  2. Remote work
  3. Team communication ←
  4. Hiring challenges
  5. Content strategy
  6. Leadership tips
  7. Career growth"

User: "Change post 3 to async work, and post 5 to SEO"
CMO: "Updated plan (still 7 posts):
  1. AI ethics
  2. Remote work
  3. Async work ← UPDATED
  4. Hiring challenges
  5. SEO ← UPDATED
  6. Leadership tips
  7. Career growth

Ready to execute?"

User: "Yes, create them"
CMO: *calls plan_content_batch with FINAL 7-post plan*

**STEP 2: BATCH EXECUTION RULES:**
1. Display plan in conversation BEFORE calling plan_content_batch
2. When user requests edits, update the plan in-conversation (no new posts)
3. Only call plan_content_batch when user confirms ("execute", "create", "go ahead")
4. The FINAL plan should have the ORIGINAL count (no duplicates from edits)

**STEP 3: BATCH TOOLS:**

1. **plan_content_batch**: Create structured plan (AFTER user confirms)
   - Input: List of post specs [{"platform": "linkedin", "topic": "...", "context": "..."}]
   - Returns: plan_id for tracking
   - Example: plan_content_batch(posts=[...], description="Week of AI content")

2. **execute_post_from_plan**: Execute posts sequentially
   - Call once per post with plan_id and post_index (0-indexed)
   - Each post gets learnings from previous posts
   - Quality improves over the batch (post 1 score 20 → post 50 score 23)
   - Example: execute_post_from_plan(plan_id="batch_123", post_index=0)

3. **compact_learnings**: Every 10 posts
   - Compresses context from 20k tokens → 2k tokens
   - Preserves key quality insights
   - Example: compact_learnings(plan_id="batch_123")

4. **checkpoint_with_user**: Every 10 posts
   - Shows progress stats, quality trend, time remaining
   - Example: checkpoint_with_user(plan_id="batch_123", posts_completed=10)

5. **cancel_batch**: User can stop batch mid-execution (NEW Phase 6A)
   - In-progress posts complete, queued posts cancelled
   - Example: cancel_batch(plan_id="batch_123")

6. **get_batch_status**: Check real-time progress (NEW Phase 6A)
   - Shows completed/failed/cancelled/processing/queued breakdown
   - Progress bar visualization
   - Example: get_batch_status(plan_id="batch_123")

**BATCH WORKFLOW EXAMPLES:**

Example A: Single post batch
```
User: "Create 1 LinkedIn post about AI, direct to calendar"
CMO: *calls plan_content_batch with 1 post spec*
CMO: "✅ Batch plan created! ID: batch_123. Creating post 1/1..."
CMO: *calls execute_post_from_plan(plan_id, 0)*
CMO: "✅ Post 1 complete (score 21/25). Saved to Airtable!"
```

Example B: Large batch with progress updates
```
User: "Create 15 LinkedIn posts, direct to calendar"
CMO: *calls plan_content_batch with 15 post specs*
CMO: "✅ Batch plan created! Creating post 1/15..."
CMO: *calls execute_post_from_plan sequentially*
[... after post 5 ...]
User: "How's it going?"
CMO: *calls get_batch_status* → "[====  ] 33% - 5/15 complete"
[... continues ...]
CMO: *calls checkpoint_with_user at post 10*
CMO: "✅ All 15 posts complete! Average score: 22/25."
```

Example C: User cancellation
```
User: "Create 20 posts, direct to calendar"
CMO: *starts batch execution*
[... after 7 posts complete ...]
User: "Stop! Cancel it!"
CMO: *calls cancel_batch*
CMO: "🛑 Batch cancelled. 7 posts completed, 13 cancelled."
```

**BATCH MODE CHARACTERISTICS:**
- Sequential execution: 1 post at a time, ~90 seconds per post
- Learning accumulation: Post N learns from posts 1 to N-1
- Quality improvement: Score typically increases 2-3 points over batch
- Real-time visibility: User sees each post complete with quality feedback
- Cancellable: User can stop mid-batch using cancel_batch tool
- Status checking: User can check progress anytime using get_batch_status tool

**CO-WRITE MODE WORKFLOW:**

When user chooses "together" / "co-write" / "let's iterate":

**CHARACTERISTICS:**
- Always 1 post at a time (never batch)
- User sees drafts before they're saved
- Interactive iteration loop until user approves
- User has full control over final output

**STEPS:**
1. Call generate_post_{platform}(topic, context) to create initial draft
2. Call quality_check_{platform}(post) to evaluate with 5-axis rubric
3. Print BOTH the post AND the quality analysis to user
4. Wait for user feedback OR 📅 calendar emoji reaction
5. If user gives feedback → call apply_fixes_{platform}(post, issues, user_feedback)
6. If user reacts with 📅 OR says "send to calendar" → call send_to_calendar(post, platform, thread_ts, channel_id, user_id, score)
7. Repeat steps 2-6 until user approves or schedules

**CO-WRITE EXAMPLE:**
```
User: "Let's write a LinkedIn post about AI agents together"
CMO: *calls generate_post_linkedin(topic="AI agents", context="...")*
CMO: *calls quality_check_linkedin(post="[draft]")*
CMO: "Here's the first draft:

[DRAFT TEXT]

Quality Analysis:
- Hook (4/5): Strong opening but could be more specific
- Body (3/5): Needs concrete example
- Proof (2/5): Missing data/numbers
- CTA (4/5): Good engagement trigger
- Format (5/5): Clean structure

What would you like to adjust?"
User: "Add a concrete example in the body"
CMO: *calls apply_fixes_linkedin with user feedback*
CMO: "Updated draft: [NEW VERSION] - Better?"
User: "Perfect! Send to calendar"
CMO: *calls send_to_calendar* → "✅ Saved to Airtable!"
```

**TOOLS AVAILABLE:**
- **CO-WRITE MODE:** generate_post_{platform}, quality_check_{platform}, apply_fixes_{platform}, send_to_calendar
- **BATCH MODE:** plan_content_batch, execute_post_from_plan, compact_learnings, checkpoint_with_user, cancel_batch, get_batch_status

**KEY PRINCIPLES:**
- **CO-WRITE:** Always show draft + quality analysis together, wait for user input, iterate until approved
- **BATCH:** Sequential execution, learning accumulation, real-time progress, cancellable
- **Both modes** enforce brand voice, writing rules, and quality standards

**DECISION SUMMARY:**
```
User requests content → ASK: "Co-write or direct to calendar?"

User says "together" → CO-WRITE MODE (1 post, iterative)
User says "direct to calendar" → BATCH MODE (any count, automated)
```

**QUALITY STANDARDS:**
- You iterate on content until it reaches high quality (85+ score)
- You remember conversations within each Slack thread (and when asked about other conversations)
- You provide strategic insights before and after content creation

If someone asks about "Dev Day on the 6th" - they likely mean OpenAI Dev Day (November 6, 2023). Search with FULL context."""

        # Calculate prompt version hash for cache invalidation
        self.prompt_version = hashlib.md5(self.system_prompt.encode()).hexdigest()[:8]

        # Create MCP server with our tools
        self.mcp_server = create_sdk_mcp_server(
            name="slack_tools",
            version="2.5.0",
            tools=[
                web_search,
                search_knowledge_base,
                search_company_documents,  # NEW in v2.5.0: User-uploaded docs for context enrichment
                search_past_posts,
                get_content_calendar,
                get_thread_context,
                analyze_content_performance,
                delegate_to_workflow,  # Delegate to subagent workflows
                send_to_calendar,  # Save approved drafts to calendar
                # Batch orchestration tools (NEW in v2.4.0)
                plan_content_batch,
                execute_post_from_plan,
                compact_learnings,
                checkpoint_with_user,
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
                apply_fixes_instagram,
                # Batch control tools (NEW Phase 6A)
                cancel_batch_tool,
                get_batch_status_tool
            ]
        )

        print("🚀 Claude Agent SDK initialized with 30 tools (9 general + 6 batch + 15 co-writing tools for 5 platforms)")

    def _get_or_create_session(self, thread_ts: str) -> ClaudeSDKClient:
        """Get existing session for thread or create new one"""
        SESSION_TTL = 3600  # 1 hour session lifetime
        now = time.time()

        # Check if we need to invalidate existing session
        if thread_ts in self._thread_sessions:
            # Check 1: Prompt version changed (code update with new prompt)
            if thread_ts in self._session_prompt_versions:
                old_version = self._session_prompt_versions[thread_ts]
                if old_version != self.prompt_version:
                    print(f"🔄 Prompt updated ({old_version} → {self.prompt_version}), recreating session for thread {thread_ts[:8]}")
                    del self._thread_sessions[thread_ts]
                    self._connected_sessions.discard(thread_ts)
                    del self._session_prompt_versions[thread_ts]
                    if thread_ts in self._session_created_at:
                        del self._session_created_at[thread_ts]

            # Check 2: Session expired (> 1 hour old)
            if thread_ts in self._session_created_at:
                age = now - self._session_created_at[thread_ts]
                if age > SESSION_TTL:
                    print(f"⏰ Session expired ({int(age/60)} minutes old), recreating session for thread {thread_ts[:8]}")
                    del self._thread_sessions[thread_ts]
                    self._connected_sessions.discard(thread_ts)
                    if thread_ts in self._session_prompt_versions:
                        del self._session_prompt_versions[thread_ts]
                    del self._session_created_at[thread_ts]

        # Create new session if needed
        if thread_ts not in self._thread_sessions:
            # Configure options for this thread
            # setting_sources=["project"] tells SDK to automatically load .claude/CLAUDE.md for brand context
            options = ClaudeAgentOptions(
                mcp_servers={"tools": self.mcp_server},
                allowed_tools=["mcp__tools__*"],
                setting_sources=["project"],  # Load .claude/CLAUDE.md automatically via SDK
                system_prompt=self.system_prompt,  # CMO prompt (SDK will combine with CLAUDE.md)
                model="claude-sonnet-4-5-20250929",  # Claude Sonnet 4.5 - latest
                permission_mode="bypassPermissions",
                continue_conversation=True  # KEY: Maintain context across messages
            )

            self._thread_sessions[thread_ts] = ClaudeSDKClient(options=options)
            self._session_prompt_versions[thread_ts] = self.prompt_version
            self._session_created_at[thread_ts] = now

            print(f"✨ Created new session for thread {thread_ts[:8]} with CMO identity (prompt version: {self.prompt_version})")
            print(f"🎭 System prompt starts with: {self.system_prompt[:100]}...")

            # DEBUG: Verify which prompt version is loaded
            if "TWO CONTENT CREATION MODES" in self.system_prompt:
                print(f"   ✅ Using NEW architecture (CO-WRITE vs BATCH)")
            else:
                print(f"   ⚠️ Using OLD architecture (count-based routing)")

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

        # NEW: Store conversation context for tools to access
        self._conversation_context[thread_ts] = {
            'channel': channel_id,
            'thread_ts': thread_ts
        }

        # NEW: Set global handler reference so tools can access slack_client
        global _current_handler
        _current_handler = self

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
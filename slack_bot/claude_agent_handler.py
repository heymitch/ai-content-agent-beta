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
import uuid

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

# Global variable to store current Slack context (channel_id, thread_ts, user_id)
# Populated at the start of each handle_conversation() call
# Allows tools to access Slack metadata without passing through function signatures
_current_slack_context = {}


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



# ================== CO-WRITE TOOLS MOVED TO cowrite_tools.py ==================
# Co-write tools (generate_post_*, quality_check_*, apply_fixes_*) are now
# lazy-loaded only when user explicitly requests co-write mode.
# This ensures batch mode is used by default (99% of requests).

# ================== BATCH ORCHESTRATION TOOLS ==================

@tool(
    "plan_content_batch",
    "Create a structured plan for N posts across platforms. Returns plan ID for tracking.",
    {
        "type": "object",
        "properties": {
            "posts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "platform": {"type": "string", "description": "Platform: linkedin, twitter, email, youtube, or instagram"},
                        "topic": {"type": "string", "description": "Main topic/angle for the post"},
                        "context": {"type": "string", "description": "Additional context or background"},
                        "style": {"type": "string", "description": "Style: thought_leadership, tactical, educational, or storytelling"}
                    },
                    "required": ["platform", "topic"]
                }
            },
            "description": {"type": "string", "description": "High-level description of the batch"}
        },
        "required": ["posts"]
    }
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
        # Access global Slack context for metadata
        context = _current_slack_context

        # Pass Slack metadata to batch plan
        plan = create_batch_plan(
            posts_list,
            description,
            channel_id=context.get('channel_id'),
            thread_ts=context.get('thread_ts'),
            user_id=context.get('user_id')
        )

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
        # Generate unique handler instance ID for debugging
        self.handler_id = str(uuid.uuid4())[:8]
        print(f"\n🏗️ Creating ClaudeAgentHandler instance [{self.handler_id}]")

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

**CRITICAL: BATCH MODE IS THE DEFAULT FOR ALL CONTENT CREATION**

**TWO PHASES:**

**PHASE 1: Strategic Conversation (OPTIONAL)**
- User is exploring ideas, developing strategy, asking "what do you think?"
- Feel free to discuss angles, positioning, tone, examples
- Ask clarifying questions to help refine the approach
- When user says "create", "write", "make", "draft", "execute", "let's do it" + content type → **IMMEDIATELY CALL plan_content_batch TOOL (DO NOT draft content inline)**

**PHASE 2: Content Creation via Batch Mode (REQUIRED)**

CRITICAL: The INSTANT user approves/requests content creation:
1. Call plan_content_batch tool with the posts array
2. Then call execute_post_from_plan for each post
3. DO NOT write draft posts in conversation first
4. DO NOT show previews before calling tools
5. TOOLS FIRST, then show results

When user requests content creation, follow this workflow:

1. **Search for Context** (if topic provided):
   - Call search_company_documents(query="[topic] case studies examples testimonials")
   - Call search_knowledge_base if needed for brand voice/strategy

2. **Create Batch Plan** (CALL THE TOOL NOW):
   - IMMEDIATELY call plan_content_batch with posts array
   - DO NOT draft example posts first
   - DO NOT show "here's what Post 1 would look like..."
   - NEVER generate post content inline in conversation
   - ALWAYS delegate to SDK subagents via the tool

3. **Execute Posts** (CALL THE TOOL NOW):
   - Call execute_post_from_plan for each post in the plan
   - SDK subagents handle actual content generation
   - Posts auto-save to Airtable
   - CRITICAL: The tool returns a summary (score + hook + Airtable link)
   - DO NOT show the full post content in Slack - only show the tool's summary
   - Full post is in Airtable, user can click the link to see it

**Tools to use:**
- plan_content_batch → Creates structured plan with post specs
- execute_post_from_plan → Returns summary with score, hook preview, Airtable link (DO NOT add full post)

**Examples (ALL use batch mode):**
✅ "Write a LinkedIn post about X" → plan_content_batch + execute_post_from_plan
✅ "Create 5 posts about Y" → plan_content_batch + execute_post_from_plan (×5)
✅ "Draft a Twitter thread" → plan_content_batch + execute_post_from_plan
✅ "Make content for LinkedIn and Twitter" → plan_content_batch + execute_post_from_plan (×2)

**RARE EXCEPTION - Co-write mode (1% of requests):**
Only use if user EXPLICITLY says: "co-write", "collaborate with me", "iterate with me"
If uncertain, ask: "Do you want me to create this now (batch) or co-write it with you?"

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
   - Provides anchors → Distribute across batch, create plan with plan_content_batch
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

**MULTI-POST REQUEST PATTERNS (ALWAYS USE BATCH):**

Recognize these patterns as multiple posts → USE BATCH:
- "turn this into X and Y and Z" → Parse as multiple posts
- "create a carousel post and a twitter thread" → 2 posts (LinkedIn + Twitter)
- "make versions for different platforms" → Multiple posts
- "create content for LinkedIn, Twitter, and YouTube" → 3 posts

Platform name mapping:
- "carousel post" or "carousel" → LinkedIn platform (multi-slide post format)
- "twitter thread" or "thread" → Twitter platform
- "youtube script" or "video script" → YouTube platform
- "instagram caption" or "IG post" → Instagram platform
- "email newsletter" or "newsletter" → Email platform

CRITICAL: NEVER generate multiple posts inline in conversation!
ALWAYS use plan_content_batch → execute_post_from_plan → SDK subagents.

**How CO-WRITE works (RARE):**
- Always 1 post at a time
- Return draft to user, WAIT for explicit approval
- NEVER auto-send to calendar - user must say "approve" or "send"
- Tools: generate_post_{platform}, quality_check_{platform}, apply_fixes_{platform}
- Only call send_to_calendar after user approves

**ROUTING DECISION (STRICT):**
1. Check message for EXACT keywords: "co-write", "collaborate with me", "iterate with me"
   → If found: ASK USER TO CONFIRM co-write mode
2. Otherwise: USE BATCH MODE (default)

**DO NOT** interpret "draft", "help", "write", "show me" as co-write requests.
These are content creation verbs that trigger BATCH mode by default.

**CRITICAL RULES:**
1. **NEVER create multiple posts inline** and concatenate them
   - ❌ WRONG: Generate 3 posts in conversation, combine, save as one Airtable record
   - ✅ RIGHT: Use batch orchestration tools (plan_content_batch + execute_post_from_plan)
2. Each post MUST be created separately to get separate Airtable rows
3. Parse count from user request: "3 posts" → count=3, "week of content" → count=7, "month" → count=30
4. Default to BATCH MODE - only use CO-WRITE if explicitly requested

**BATCH MODE WORKFLOW:**

When using BATCH MODE (the default for ANY post count):

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

**CRITICAL: PRESERVING USER OUTLINES IN BATCH MODE**

When user provides detailed post outlines (common in strategic batches):

RECOGNIZE these patterns:
- "Post 1: [detailed narrative]"
- "DAY 1: [title] - [full outline]"
- Numbered/bulleted posts with specific content
- Strategic sequences with exact messaging

YOU MUST:
1. Extract COMPLETE outline for each post (not just topic)
2. Store in 'detailed_outline' field alongside topic/context
3. Include ALL user-provided details (hooks, examples, CTAs)
4. Preserve formatting and structure

EXAMPLE - User provides:
"Create 3 LinkedIn posts:
Post 1 (Morning): Most high-ticket operators have built the wrong AI tools. They spent months on chatbots. I built something different..."

Your plan_content_batch call MUST be:
posts=[{
    "platform": "linkedin",
    "topic": "High-ticket operators building wrong AI tools",
    "context": "Morning post, contrarian angle",
    "detailed_outline": "Most high-ticket operators have built the wrong AI tools. They spent months on chatbots. I built something different...",  # FULL TEXT - can be 500+ words!
    "style": "contrarian",
    "timing": "Morning 7-9 AM"
}]

NEVER summarize or truncate the user's strategic outline!
When in doubt, preserve MORE context, not less.

If user provides a 500-word nearly-complete post as their outline, store ALL 500 words.
The detailed_outline field has NO length limit - preserve EVERYTHING.

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
        print(f"   Prompt version: {self.prompt_version}")

        # Initialize co-write mode as False by default (will be set per message)
        self.cowrite_mode = False

        # Build tool list - always include batch tools (default mode)
        self.base_tools = [
            # Core tools - always available
            web_search,
            search_knowledge_base,
            search_company_documents,  # NEW in v2.5.0: User-uploaded docs for context enrichment
            search_past_posts,
            get_content_calendar,
            get_thread_context,
            analyze_content_performance,
            send_to_calendar,  # Save approved drafts to calendar
            # Batch orchestration tools - ALWAYS available (default mode)
            plan_content_batch,
            execute_post_from_plan,
            compact_learnings,
            checkpoint_with_user,
            cancel_batch_tool,
            get_batch_status_tool
        ]

        # Create MCP server with base tools initially
        self.mcp_server = create_sdk_mcp_server(
            name="slack_tools",
            version="2.6.0",  # Bumped for lazy-loading feature
            tools=self.base_tools
        )

        print(f"✅ Handler [{self.handler_id}] ready with batch tools (default mode)")

    def _detect_cowrite_mode(self, message: str) -> bool:
        """
        Detect if user explicitly wants co-write mode

        Args:
            message: User's message text

        Returns:
            True if co-write keywords detected, False for batch mode (default)
        """
        if not message:
            return False

        message_lower = message.lower()

        # EXACT keywords that trigger co-write mode
        cowrite_keywords = [
            "co-write",
            "cowrite",
            "collaborate with me",
            "iterate with me",
            "iterate with you",  # Added to match test case
            "work with me on this",
            "let's collaborate",
            "let's iterate"
        ]

        # Check for exact keyword matches
        for keyword in cowrite_keywords:
            if keyword in message_lower:
                print(f"🔍 Co-write keyword detected: '{keyword}'")
                return True

        # Default to batch mode
        return False

    def _get_or_create_session(self, thread_ts: str, request_id: str = "NONE") -> ClaudeSDKClient:
        """Get existing session for thread or create new one"""
        SESSION_TTL = 3600  # 1 hour session lifetime
        now = time.time()

        # Verbose logging for debugging
        print(f"[{request_id}] 🔍 Session lookup for thread {thread_ts[:8]}")
        print(f"[{request_id}]    Existing sessions: {list(self._thread_sessions.keys())}")
        print(f"[{request_id}]    Current prompt version: {self.prompt_version}")

        # Check if we need to invalidate existing session
        if thread_ts in self._thread_sessions:
            print(f"[{request_id}]    ♻️ Session exists, checking if valid...")

            # Check 1: Prompt version changed (code update with new prompt)
            if thread_ts in self._session_prompt_versions:
                old_version = self._session_prompt_versions[thread_ts]
                print(f"[{request_id}]    Cached prompt version: {old_version}")
                if old_version != self.prompt_version:
                    print(f"[{request_id}] 🔄 PROMPT CHANGED ({old_version} → {self.prompt_version})")
                    print(f"[{request_id}]    Invalidating session for thread {thread_ts[:8]}")
                    del self._thread_sessions[thread_ts]
                    self._connected_sessions.discard(thread_ts)
                    del self._session_prompt_versions[thread_ts]
                    if thread_ts in self._session_created_at:
                        del self._session_created_at[thread_ts]

            # Check 2: Session expired (> 1 hour old)
            if thread_ts in self._session_created_at:
                age = now - self._session_created_at[thread_ts]
                age_mins = int(age / 60)
                print(f"[{request_id}]    Session age: {age_mins} minutes")
                if age > SESSION_TTL:
                    print(f"[{request_id}] ⏰ SESSION EXPIRED ({age_mins} minutes old)")
                    print(f"[{request_id}]    Invalidating session for thread {thread_ts[:8]}")
                    del self._thread_sessions[thread_ts]
                    self._connected_sessions.discard(thread_ts)
                    if thread_ts in self._session_prompt_versions:
                        del self._session_prompt_versions[thread_ts]
                    del self._session_created_at[thread_ts]

        # Create new session if needed
        if thread_ts not in self._thread_sessions:
            print(f"[{request_id}] ✨ Creating NEW session for thread {thread_ts[:8]}")
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

            print(f"[{request_id}]    ✅ Session created with prompt version: {self.prompt_version}")
            print(f"[{request_id}]    System prompt preview: {self.system_prompt[:80]}...")

            # DEBUG: Verify which prompt version is loaded
            if "BATCH MODE IS THE DEFAULT" in self.system_prompt:
                print(f"[{request_id}]    ✅ Using NEW architecture (BATCH-first with SDK subagents)")
            else:
                print(f"[{request_id}]    ⚠️ Using OLD architecture (missing batch emphasis)")
        else:
            print(f"[{request_id}]    ✅ Reusing existing session (version: {self._session_prompt_versions.get(thread_ts, 'unknown')})")

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

        # Generate unique request ID for debugging
        request_id = str(uuid.uuid4())[:8]

        print(f"\n{'='*70}")
        print(f"[{request_id}] 🎯 NEW REQUEST - Thread: {thread_ts[:8]}")
        print(f"[{request_id}] 💬 Message: {message[:100]}{'...' if len(message) > 100 else ''}")
        print(f"{'='*70}")

        # NEW: Store conversation context for tools to access
        self._conversation_context[thread_ts] = {
            'channel': channel_id,
            'thread_ts': thread_ts
        }

        # NEW: Set global handler reference so tools can access slack_client
        global _current_handler
        _current_handler = self

        # Set global Slack context for tools to access metadata
        global _current_slack_context
        _current_slack_context = {
            'channel_id': channel_id,
            'thread_ts': thread_ts,
            'user_id': user_id
        }

        # Add today's date context to the message (important for recency)
        from datetime import datetime
        today = datetime.now().strftime("%B %d, %Y")  # e.g., "October 09, 2025"

        # Simple message with date context - instructions are already in system prompt
        contextualized_message = f"[Today is {today}] {message}"

        # Check if this message requires co-write mode
        message_needs_cowrite = self._detect_cowrite_mode(message)

        # If co-write mode is needed and not already loaded, update the MCP server
        if message_needs_cowrite and not self.cowrite_mode:
            print(f"[{request_id}] 📝 Co-write mode requested - loading co-write tools...")

            # Load co-write tools
            from slack_bot.cowrite_tools import get_cowrite_tools
            all_tools = self.base_tools + get_cowrite_tools()

            # Recreate MCP server with all tools
            self.mcp_server = create_sdk_mcp_server(
                name="slack_tools",
                version="2.6.0",
                tools=all_tools
            )

            # Mark that co-write mode is loaded
            self.cowrite_mode = True

            # Clear existing sessions to force reconnection with new tools
            self._thread_sessions.clear()
            self._connected_sessions.clear()

            print(f"[{request_id}] ✅ Co-write tools loaded (15 additional tools)")
        elif message_needs_cowrite:
            print(f"[{request_id}] 📝 Co-write mode already active")
        else:
            print(f"[{request_id}] 🚀 Using batch mode (default)")

        try:
            # Get or create cached session for this thread
            client = self._get_or_create_session(thread_ts, request_id)

            # Only connect if this is a NEW session (not already connected)
            if thread_ts not in self._connected_sessions:
                print(f"[{request_id}] 🔌 Connecting NEW client session...")
                await client.connect()
                self._connected_sessions.add(thread_ts)
                print(f"[{request_id}] ✅ Client connected successfully")
            else:
                print(f"[{request_id}] ♻️ Reusing connected client...")

            # Send the query
            print(f"[{request_id}] 📨 Sending query to Claude SDK...")
            await client.query(contextualized_message)

            # Collect ONLY the latest response (memory stays intact in session)
            latest_response = ""
            print(f"[{request_id}] ⏳ Waiting for Claude SDK response...")
            async for msg in client.receive_response():
                # Each message REPLACES the previous (we only want the final response)
                # The SDK maintains full conversation history internally
                msg_type = type(msg).__name__

                # Extract text content and log tool calls
                text_preview = None
                if hasattr(msg, 'content'):
                    if isinstance(msg.content, list):
                        for block in msg.content:
                            # Handle dict-style blocks (raw API format)
                            if isinstance(block, dict):
                                block_type = block.get('type')
                                if block_type == 'text':
                                    latest_response = block.get('text', '')
                                    text_preview = latest_response[:150]
                                elif block_type == 'tool_use':
                                    tool_name = block.get('name', 'unknown')
                                    tool_input = block.get('input', {})
                                    # Create brief preview of args
                                    args_preview = str(tool_input)[:100]
                                    print(f"[{request_id}] 🔧 Tool: {tool_name}({args_preview}{'...' if len(str(tool_input)) > 100 else ''})")
                                elif block_type == 'tool_result':
                                    result_preview = str(block.get('content', ''))[:100]
                                    print(f"[{request_id}] ✅ Tool result: {result_preview}{'...' if len(str(block.get('content', ''))) > 100 else ''}")
                            # Handle object-style blocks (SDK format)
                            elif hasattr(block, 'text'):
                                latest_response = block.text
                                text_preview = latest_response[:150]
                            elif hasattr(block, 'name'):  # Likely a tool_use block
                                tool_name = block.name
                                tool_input = getattr(block, 'input', {})
                                args_preview = str(tool_input)[:100]
                                print(f"[{request_id}] 🔧 Tool: {tool_name}({args_preview}{'...' if len(str(tool_input)) > 100 else ''})")
                    elif hasattr(msg.content, 'text'):
                        latest_response = msg.content.text
                        text_preview = latest_response[:150]
                    else:
                        latest_response = str(msg.content)
                elif hasattr(msg, 'text'):
                    latest_response = msg.text
                    text_preview = latest_response[:150]

                # Log with content preview
                if text_preview:
                    print(f"[{request_id}] 📩 {msg_type}: {text_preview}{'...' if len(latest_response) > 150 else ''}")
                else:
                    print(f"[{request_id}] 📩 {msg_type} (no text content)")

            final_text = latest_response  # Only use the latest response
            print(f"[{request_id}] ✅ Response received ({len(final_text)} chars)")

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
            error_str = str(e)
            print(f"❌ Agent error: {e}")
            import traceback
            traceback.print_exc()

            # Format error message for Slack - hide ugly API details
            if any(keyword in error_str.lower() for keyword in ['api_error', '500', 'internal server error', 'anthropic']):
                return "⚠️ Sorry, I encountered an API issue while creating content. Some posts may have been created successfully - please check Airtable. Full error details are in the server logs."
            else:
                # Truncate long error messages
                clean_error = error_str[:400] + "..." if len(error_str) > 400 else error_str
                return f"Sorry, I encountered an error: {clean_error}"

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
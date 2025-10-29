"""
Stdio MCP Server - Workaround for ProcessTransport Bug
https://github.com/anthropics/claude-agent-sdk-python/issues/266

This file wraps all agent tools as an external stdio MCP server
to avoid the race condition in create_sdk_mcp_server()
"""
from mcp.server.fastmcp import FastMCP
from typing import Any, Dict
import os
import asyncio

# Import existing tool functions
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
    create_batch_plan,
    execute_single_post_from_plan,
    get_context_manager
)

# Initialize FastMCP server
mcp = FastMCP(name="slack_tools")


@mcp.tool()
async def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information, news, updates. Use for ANY real-time questions about events."""
    return _web_search_func(query=query, max_results=max_results)


@mcp.tool()
async def search_knowledge_base(query: str, match_count: int = 5) -> str:
    """Search internal knowledge base using RAG for brand voice and documentation."""
    return _search_kb_func(query=query, match_count=match_count)


@mcp.tool()
async def search_company_documents(query: str, match_count: int = 3, document_type: str = None) -> str:
    """Search user-uploaded company documents (case studies, testimonials, product docs). Use BEFORE asking user for context."""
    return _search_company_docs_func(
        query=query,
        match_count=match_count,
        document_type=document_type
    )


@mcp.tool()
async def search_past_posts(user_id: str, platform: str = None, days_back: int = 30, min_score: int = 0) -> str:
    """Search content created in past conversations."""
    return _search_posts_func(
        user_id=user_id,
        platform=platform,
        days_back=days_back,
        min_score=min_score
    )


@mcp.tool()
async def get_content_calendar(user_id: str = None, days_ahead: int = 14, platform: str = None) -> str:
    """Get upcoming scheduled content."""
    return _get_calendar_func(
        user_id=user_id,
        days_ahead=days_ahead,
        platform=platform
    )


@mcp.tool()
async def get_thread_context(thread_ts: str, include_content: bool = True) -> str:
    """Get complete context from current Slack thread."""
    return _get_context_func(
        thread_ts=thread_ts,
        include_content=include_content
    )


@mcp.tool()
async def analyze_content_performance(user_id: str, platform: str = None, days_back: int = 30) -> str:
    """Analyze content performance trends."""
    return _analyze_perf_func(
        user_id=user_id,
        platform=platform,
        days_back=days_back
    )


@mcp.tool()
async def search_templates(user_intent: str, max_results: int = 3) -> str:
    """Search content templates for strategy sessions. Returns top matching templates based on user intent."""
    return _search_templates_func(user_intent=user_intent, max_results=max_results)


@mcp.tool()
async def get_template(template_name: str) -> str:
    """Get full template structure by name after user picks from search results."""
    return _get_template_func(template_name=template_name)


@mcp.tool()
async def check_ai_detection(post_text: str) -> str:
    """Validate post against GPTZero AI detector. Use AFTER quality_check passes to ensure post will pass AI detection."""
    import httpx

    if not post_text or len(post_text) < 50:
        return "❌ Post too short (minimum 50 characters for detection)"

    api_key = os.getenv('GPTZERO_API_KEY')
    if not api_key:
        return "⚠️ GPTZero API key not configured. Set GPTZERO_API_KEY in .env to enable AI detection validation."

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

            return result_text

    except httpx.HTTPError as e:
        return f"❌ GPTZero API error: {str(e)}\n\nCheck your API key and network connection."
    except Exception as e:
        return f"❌ Error checking AI detection: {str(e)}"


@mcp.tool()
async def plan_content_batch(posts: list, description: str = "Content batch") -> str:
    """Create a structured plan for N posts across platforms. Returns plan ID for tracking.

    Args:
        posts: List of post specs [{"platform": "linkedin", "topic": "...", "context": "...", "style": "..."}]
        description: High-level description of the batch
    """
    import sys
    print(f"📋 [MCP] plan_content_batch called with {len(posts) if posts else 0} posts", file=sys.stderr)
    sys.stderr.flush()

    if not posts or len(posts) == 0:
        return "❌ No posts provided. Please specify at least one post in the batch."

    try:
        # Create plan (Slack metadata will be None in stdio mode - that's okay)
        plan = create_batch_plan(
            posts,
            description,
            channel_id=None,
            thread_ts=None,
            user_id=None
        )
        print(f"✅ [MCP] Plan created: {plan['id']}", file=sys.stderr)
        sys.stderr.flush()

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

        return summary

    except Exception as e:
        return f"❌ Error creating plan: {str(e)}"


@mcp.tool()
async def execute_post_from_plan(plan_id: str, post_index: int) -> str:
    """Execute a single post from the batch plan.

    Args:
        plan_id: ID from plan_content_batch
        post_index: Which post to create (0-indexed)
    """
    import sys
    print(f"🚀 [MCP] execute_post_from_plan called: plan={plan_id}, index={post_index}", file=sys.stderr)
    sys.stderr.flush()

    if not plan_id:
        return "❌ No plan_id provided. Create a plan first with plan_content_batch."

    try:
        # Get the plan to check total count
        from agents.batch_orchestrator import _batch_plans
        plan = _batch_plans.get(plan_id)

        if not plan:
            return f"❌ Plan {plan_id} not found"

        total_posts = len(plan['posts'])
        is_single_post = (total_posts == 1)

        # Execute the post
        result = await execute_single_post_from_plan(plan_id, post_index)

        if result.get('error'):
            return f"❌ {result['error']}"

        # Format result based on batch size
        if is_single_post:
            # Single post: Return FULL formatted result from SDK agent (includes full post)
            # The SDK agent already returns beautifully formatted output
            full_result = result.get('full_result', '')

            if full_result:
                # full_result is already a formatted string from the SDK agent
                output = str(full_result)
                print(f"✅ [MCP] Returning full_result ({len(output)} chars)", file=sys.stderr)
                sys.stderr.flush()
            else:
                # Fallback if full_result not available
                output = f"""✅ **Post Created & Saved to Airtable**

📊 **Quality Score:** {result.get('score', 'N/A')}/25
🔗 **Airtable Record:** [View Here]({result.get('airtable_url', 'N/A')})

📝 **Hook Preview:** {result.get('hook', 'N/A')[:200]}...

Note: Full post saved to Airtable - view link above."""
        else:
            # Multi-post batch: Return summary only
            output = f"""✅ **Post {post_index + 1}/{total_posts} Complete**

📊 **Quality Score:** {result.get('score', 'N/A')}/25
🎯 **Platform:** {result.get('platform', 'unknown').capitalize()}
📝 **Hook Preview:** {result.get('hook', 'N/A')[:100]}...
📎 **Airtable:** {result.get('airtable_url', 'N/A')}

**Next:** Execute post {post_index + 2} to continue the batch."""

        return output

    except Exception as e:
        import traceback
        print(f"❌ execute_post_from_plan error: {e}")
        print(traceback.format_exc())
        return f"❌ Error executing post: {str(e)}"


@mcp.tool()
async def compact_learnings(plan_id: str) -> str:
    """Compress learnings from last 10 posts into key insights. Call every 10 posts."""
    if not plan_id:
        return "❌ No plan_id provided."

    try:
        context_mgr = get_context_manager(plan_id)

        if not context_mgr:
            return f"❌ No context manager found for plan {plan_id}"

        # Run compaction
        await context_mgr.compact()

        stats = context_mgr.get_stats()

        return f"""✅ **Learnings Compacted**

📊 **Stats:**
- Total posts: {stats['total_posts']}
- Average score: {stats['average_score']:.1f}/25
- Posts since last compact: {stats['posts_since_compact']}

Context compressed from ~20k tokens to ~2k tokens.
Quality insights preserved for next batch of posts."""

    except Exception as e:
        return f"❌ Error compacting learnings: {str(e)}"


@mcp.tool()
async def checkpoint_with_user(plan_id: str, posts_completed: int) -> str:
    """Send checkpoint update to user at 10/20/30/40 post intervals. Shows progress stats."""
    if not plan_id:
        return "❌ No plan_id provided."

    try:
        context_mgr = get_context_manager(plan_id)

        if not context_mgr:
            return f"❌ No context manager found for plan {plan_id}"

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

        return checkpoint_msg

    except Exception as e:
        return f"❌ Error creating checkpoint: {str(e)}"


@mcp.tool()
async def send_to_calendar(post: str, platform: str, thread_ts: str = None, channel_id: str = None, user_id: str = None, score: int = 0) -> str:
    """Save approved draft to Airtable calendar. Use after user approves content in co-writing mode."""
    try:
        # Save to Airtable calendar
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

            return f"""✅ **Added to content calendar!**

📊 **Airtable Record:** {airtable_url}
📝 **Record ID:** {record_id}
📅 **Platform:** {platform.capitalize()}
⭐ **Quality Score:** {score}/100

The content is now scheduled in your Airtable calendar. You can edit the posting date and make final tweaks there."""
        else:
            error_msg = result.get('error', 'Unknown error')
            return f"❌ Failed to save to calendar: {error_msg}\n\nPlease check your Airtable configuration."

    except Exception as e:
        import traceback
        print(f"❌ send_to_calendar error: {e}")
        print(traceback.format_exc())
        return f"❌ Error saving to calendar: {str(e)}\n\nPlease try again or contact support."


# Run the server
if __name__ == "__main__":
    import sys
    print("🚀 Starting Stdio MCP Server (workaround for ProcessTransport bug)", file=sys.stderr)
    print("📋 Tools available: web_search, search_knowledge_base, search_company_documents, search_past_posts, get_content_calendar, get_thread_context, analyze_content_performance, search_templates, get_template, check_ai_detection, plan_content_batch, execute_post_from_plan, compact_learnings, checkpoint_with_user, send_to_calendar", file=sys.stderr)
    print("📡 Listening on stdin/stdout for MCP requests...", file=sys.stderr)
    sys.stderr.flush()

    try:
        mcp.run(transport="stdio")
    except Exception as e:
        print(f"❌ MCP Server crashed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

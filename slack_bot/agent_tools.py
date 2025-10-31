"""
Intelligent agent tools for Slack content operations
Tools that enable the bot to search, analyze, and manage content
"""
from typing import Dict, List, Any
import os
from datetime import datetime, timedelta


def search_past_posts(
    user_id: str,
    platform: str = None,
    days_back: int = 30,
    min_score: int = 0
) -> str:
    """
    Search for content created in past conversations

    Args:
        user_id: Slack user ID
        platform: Filter by platform (linkedin, twitter, email)
        days_back: How many days to look back
        min_score: Minimum quality score filter

    Returns:
        Formatted list of past posts with scores and metadata
    """
    from supabase import create_client

    try:
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        all_posts = []

        # 1. Query generated_posts (unpublished/queue)
        try:
            gen_query = client.table('generated_posts')\
                .select('*')\
                .gte('quality_score', min_score)\
                .gte('created_at', cutoff_date)\
                .order('created_at', desc=True)\
                .limit(10)

            if platform:
                gen_query = gen_query.eq('platform', platform.lower())

            gen_result = gen_query.execute()

            for post in gen_result.data or []:
                all_posts.append({
                    'source': 'QUEUE',
                    'platform': post.get('platform', 'unknown'),
                    'score': post.get('quality_score', 0),
                    'content': post.get('body_content') or post.get('content', ''),
                    'hook': post.get('post_hook', ''),
                    'created': post.get('created_at', ''),
                    'iterations': post.get('iterations', 1),
                    'status': post.get('status', 'draft')
                })
        except Exception as e:
            print(f"Warning: Could not query generated_posts: {e}")

        # 2. Query content_performance (published)
        try:
            perf_query = client.table('content_performance')\
                .select('*')\
                .eq('user_id', user_id)\
                .gte('quality_score', min_score)\
                .gte('created_at', cutoff_date)\
                .order('created_at', desc=True)\
                .limit(10)

            if platform:
                perf_query = perf_query.eq('platform', platform)

            perf_result = perf_query.execute()

            for post in perf_result.data or []:
                all_posts.append({
                    'source': 'PUBLISHED',
                    'platform': post.get('platform', 'unknown'),
                    'score': post.get('quality_score', 0),
                    'content': post.get('content', ''),
                    'hook': post.get('post_hook', ''),
                    'created': post.get('created_at', ''),
                    'iterations': post.get('iterations', 1),
                    'status': 'published'
                })
        except Exception as e:
            print(f"Warning: Could not query content_performance: {e}")

        if not all_posts:
            return f"No posts found in the last {days_back} days"

        # Sort by created date (most recent first)
        all_posts.sort(key=lambda x: x['created'], reverse=True)

        # Format results
        posts_summary = ["PAST CONTENT:\n"]
        for i, post in enumerate(all_posts[:10], 1):
            score = post['score']
            # Ensure content is properly handled as UTF-8 string
            content = str(post['content']) if post['content'] else ''
            content_preview = content[:150] if content else '[No content]'
            created = str(post['created'])[:10]
            platform_name = str(post['platform'])
            iterations = post['iterations']
            source = str(post['source'])
            # Ensure hook is properly handled as UTF-8 string
            hook = str(post['hook'])[:80] if post['hook'] else content_preview[:80]
            status_marker = "[QUEUE]" if source == "QUEUE" else "[PUBLISHED]"

            posts_summary.append(
                f"{i}. {status_marker} [{platform_name.upper()}] {source} | Score: {score}/100 ({iterations} iterations)\n"
                f"   Created: {created}\n"
                f"   Hook: {hook}...\n"
            )

        # Ensure final string is properly encoded as UTF-8
        result = "\n".join(posts_summary)
        return result

    except Exception as e:
        return f"Error searching posts: {str(e)}"


def get_content_calendar(
    user_id: str = None,
    days_ahead: int = 14,
    platform: str = None
) -> str:
    """
    Get upcoming scheduled content from calendar

    Args:
        user_id: Filter by user (optional)
        days_ahead: How many days to look ahead
        platform: Filter by platform

    Returns:
        Formatted calendar of scheduled posts
    """
    from supabase import create_client

    try:
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Query content_calendar table
        query = client.table('content_calendar')\
            .select('*')\
            .gte('scheduled_date', datetime.now().date().isoformat())\
            .lte('scheduled_date', (datetime.now() + timedelta(days=days_ahead)).date().isoformat())\
            .order('scheduled_date', desc=False)\
            .limit(20)

        if user_id:
            query = query.eq('user_id', user_id)
        if platform:
            query = query.eq('platform', platform)

        result = query.execute()

        if not result.data:
            return f"No content scheduled in the next {days_ahead} days"

        # Format results
        calendar_items = []
        for item in result.data:
            date = item.get('scheduled_date', '')
            platform_name = item.get('platform', 'unknown')
            content_preview = item.get('content', '')[:100]
            status = item.get('status', 'pending')

            calendar_items.append(
                f"📅 {date} - {platform_name.upper()} ({status})\n"
                f"   {content_preview}...\n"
            )

        return "\n".join(calendar_items)

    except Exception as e:
        return f"Error fetching calendar: {str(e)}"


def get_thread_context(
    thread_ts: str,
    include_content: bool = True
) -> str:
    """
    Get full context from a Slack thread including all content created

    Args:
        thread_ts: Slack thread timestamp
        include_content: Whether to include full content or just summaries

    Returns:
        Complete thread context with conversation and content
    """
    from supabase import create_client

    try:
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Get conversation history
        conv_result = client.table('conversation_history')\
            .select('*')\
            .eq('thread_ts', thread_ts)\
            .order('created_at', desc=False)\
            .execute()

        # Get content performance from this thread
        content_result = client.table('content_performance')\
            .select('*')\
            .eq('thread_ts', thread_ts)\
            .order('created_at', desc=False)\
            .execute()

        context_parts = []

        # Add conversation summary
        if conv_result.data:
            context_parts.append(f"CONVERSATION ({len(conv_result.data)} messages):")

            # Smart truncation: If thread is very long, return first 5 + last 20 messages
            # This ensures we get the initial context (like batch plans) AND recent messages
            messages = conv_result.data
            if len(messages) > 30:
                # Include first 5 messages (often contains plans/instructions)
                for msg in messages[:5]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    # Don't truncate first 5 messages - they might contain important plans
                    context_parts.append(f"{role}: {content}")

                context_parts.append(f"\n... [{len(messages) - 25} messages omitted] ...\n")

                # Include last 20 messages (recent conversation)
                for msg in messages[-20:]:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')[:500]  # Increased from 200 chars
                    context_parts.append(f"{role}: {content}")
            else:
                # For shorter threads, return everything with minimal truncation
                for msg in messages:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')[:1000]  # Allow up to 1000 chars per message
                    context_parts.append(f"{role}: {content}")

        # Add content created
        if content_result.data:
            context_parts.append(f"\nCONTENT CREATED ({len(content_result.data)} posts):")
            for post in content_result.data:
                platform = post.get('platform', 'unknown')
                score = post.get('quality_score', 0)

                if include_content:
                    content = post.get('content', '')
                    context_parts.append(f"\n{platform.upper()} (Score: {score}/100):\n{content}\n")
                else:
                    preview = post.get('content', '')[:150]
                    context_parts.append(f"{platform.upper()} (Score: {score}/100): {preview}...")

        return "\n".join(context_parts) if context_parts else "No context found for this thread"

    except Exception as e:
        return f"Error fetching thread context: {str(e)}"


def analyze_content_performance(
    user_id: str,
    platform: str = None,
    days_back: int = 30
) -> str:
    """
    Analyze content performance trends and provide insights

    NEW: Phase 1 Analytics - Uses Ayrshare MCP + Claude Sonnet 4.5 for strategic insights

    This function now:
    1. Attempts to fetch live analytics from Ayrshare MCP server (if available)
    2. Falls back to internal Supabase data if Ayrshare unavailable
    3. Uses Claude Sonnet 4.5 via analyze_performance() for strategic insights
    4. Returns actionable recommendations (hook styles, timing, platform fit)

    Args:
        user_id: Slack user ID
        platform: Filter by platform
        days_back: Analysis period in days

    Returns:
        Performance analysis with trends and recommendations
    """
    from supabase import create_client
    import statistics
    import asyncio

    # Try Ayrshare MCP first (Phase 1: Live analytics)
    try:
        from slack_bot.analytics_handler import analyze_performance

        # TODO: Add Ayrshare MCP fetch here when MCP server is configured
        # For now, fall through to Supabase-only analysis
        # Example future implementation:
        # ayrshare_data = await mcp_fetch_analytics(days_back=days_back, platform=platform)
        # if ayrshare_data:
        #     analysis = await analyze_performance(ayrshare_data['posts'], ayrshare_data['date_range'])
        #     return format_analysis_for_slack(analysis)

    except Exception as e:
        print(f"Analytics handler not available, using legacy analysis: {e}")

    # Fallback: Legacy Supabase-only analysis
    try:
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Query content performance
        query = client.table('content_performance')\
            .select('*')\
            .eq('user_id', user_id)\
            .gte('created_at', (datetime.now() - timedelta(days=days_back)).isoformat())

        if platform:
            query = query.eq('platform', platform)

        result = query.execute()

        if not result.data or len(result.data) < 3:
            return "Not enough data for analysis (need at least 3 posts)"

        # Calculate metrics
        scores = [p.get('quality_score', 0) for p in result.data]
        iterations = [p.get('iterations', 1) for p in result.data]
        platforms = {}

        for post in result.data:
            plat = post.get('platform', 'unknown')
            platforms[plat] = platforms.get(plat, []) + [post.get('quality_score', 0)]

        # Generate insights
        analysis = [
            f"PERFORMANCE ANALYSIS ({len(result.data)} posts, {days_back} days)",
            f"",
            f"Quality Scores:",
            f"  Average: {statistics.mean(scores):.1f}/100",
            f"  Best: {max(scores)}/100",
            f"  Worst: {min(scores)}/100",
            f"",
            f"Iterations:",
            f"  Average: {statistics.mean(iterations):.1f} revisions per post",
            f"",
            f"By Platform:"
        ]

        for plat, plat_scores in platforms.items():
            avg_score = statistics.mean(plat_scores)
            analysis.append(f"  {plat.upper()}: {len(plat_scores)} posts, avg {avg_score:.1f}/100")

        # Recommendations
        analysis.append("\nRecommendations:")
        if statistics.mean(scores) < 75:
            analysis.append("  • Focus on improving quality - average score is below target")
        if statistics.mean(iterations) > 2:
            analysis.append("  • High iteration count - consider clearer initial briefs")

        analysis.append("\n💡 NOTE: This analysis uses internal quality scores only.")
        analysis.append("For live engagement data (impressions, likes, shares), ask: 'How did our posts perform on LinkedIn last week?'")
        analysis.append("This will trigger Ayrshare analytics with strategic insights from Claude.")

        return "\n".join(analysis)

    except Exception as e:
        return f"Error analyzing performance: {str(e)}"


# Tool definitions for Claude Agent SDK
CONTENT_TOOLS = [
    {
        "name": "search_past_posts",
        "description": "Search for content created in past conversations. Use this when users ask about 'recent posts', 'what we created', or 'past content'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Slack user ID"},
                "platform": {"type": "string", "description": "Filter by platform (linkedin, twitter, email)", "enum": ["linkedin", "twitter", "email"]},
                "days_back": {"type": "integer", "description": "How many days to look back", "default": 30},
                "min_score": {"type": "integer", "description": "Minimum quality score filter", "default": 0}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_content_calendar",
        "description": "Get upcoming scheduled content. Use when users ask about 'what's scheduled', 'upcoming posts', or 'content calendar'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Filter by user"},
                "days_ahead": {"type": "integer", "description": "How many days to look ahead", "default": 14},
                "platform": {"type": "string", "description": "Filter by platform"}
            },
            "required": []
        }
    },
    {
        "name": "get_thread_context",
        "description": "Get complete context from a Slack thread. Use to understand what's been discussed and created in the current conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "thread_ts": {"type": "string", "description": "Slack thread timestamp"},
                "include_content": {"type": "boolean", "description": "Include full content or just summaries", "default": True}
            },
            "required": ["thread_ts"]
        }
    },
    {
        "name": "analyze_content_performance",
        "description": "Analyze content performance trends. Use when users ask for insights, trends, or performance analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "Slack user ID"},
                "platform": {"type": "string", "description": "Filter by platform"},
                "days_back": {"type": "integer", "description": "Analysis period in days", "default": 30}
            },
            "required": ["user_id"]
        }
    }
]

# Map tool names to functions
TOOL_FUNCTIONS = {
    "search_past_posts": search_past_posts,
    "get_content_calendar": get_content_calendar,
    "get_thread_context": get_thread_context,
    "analyze_content_performance": analyze_content_performance
}

"""
Analytics tools for agent

Provides natural language interface to post performance analytics.
Tools query Supabase for published posts with metrics and use Claude for analysis.

Before using: Ensure syncs have run (Airtable content + Ayrshare metrics)
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from supabase import create_client

logger = logging.getLogger(__name__)


def get_post_analytics(
    days_back: int = 7,
    platform: str = None,
    min_engagement: float = 0.0
) -> str:
    """
    Analyze post performance and identify patterns.

    Uses Claude to analyze engagement metrics and provide strategic insights:
    - Top/worst performers
    - Pattern detection (hooks, timing, platforms)
    - Actionable recommendations

    Args:
        days_back: Analyze posts from last N days (default: 7)
        platform: Filter by platform (linkedin, twitter, email)
        min_engagement: Min engagement rate filter (default: 0.0)

    Returns:
        Formatted analysis with insights and recommendations
    """
    from integrations.airtable_sync import sync_airtable_to_generated_posts
    from integrations.ayrshare_sync import sync_ayrshare_metrics
    from slack_bot.analytics_handler import analyze_performance
    from anthropic import Anthropic

    try:
        # Step 1: Sync data first (ensure accuracy)
        logger.info("Syncing Airtable content before analytics...")
        asyncio.run(sync_airtable_to_generated_posts(only_recent=True))

        logger.info("Syncing Ayrshare metrics before analytics...")
        asyncio.run(sync_ayrshare_metrics(days_back=days_back))

        # Step 2: Query published posts with metrics
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        query = client.table('generated_posts')\
            .select('*')\
            .eq('status', 'published')\
            .not_.is_('embedding', 'null')\
            .gte('published_at', cutoff_date)\
            .order('published_at', desc=True)

        if platform:
            query = query.eq('platform', platform.lower())

        if min_engagement > 0:
            query = query.gte('engagement_rate', min_engagement)

        result = query.execute()
        posts = result.data

        if not posts:
            return f"No published posts found in the last {days_back} days{' for ' + platform if platform else ''}."

        # Step 3: Format posts for Claude analysis
        posts_for_analysis = []
        for post in posts:
            # Calculate engagements if not stored
            engagements = post.get('engagements') or (
                (post.get('likes') or 0) +
                (post.get('comments') or 0) +
                (post.get('shares') or 0)
            )

            posts_for_analysis.append({
                'hook': post.get('post_hook', '')[:200],
                'platform': post.get('platform'),
                'quality_score': post.get('quality_score', 0),
                'impressions': post.get('impressions', 0),
                'engagements': engagements,
                'engagement_rate': post.get('engagement_rate', 0.0),
                'published_at': post.get('published_at', '')[:10],
                'content_type': post.get('content_type', 'unknown')
            })

        # Step 4: Call Claude for analysis
        anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        date_range = {
            'start': cutoff_date[:10],
            'end': datetime.now().strftime('%Y-%m-%d')
        }

        import asyncio
        analysis = asyncio.run(analyze_performance(
            posts=posts_for_analysis,
            date_range=date_range,
            client=anthropic_client
        ))

        # Step 5: Format results
        result_parts = []

        result_parts.append(f"📊 *ANALYTICS REPORT* ({days_back} days)")
        result_parts.append(f"Total posts analyzed: {len(posts)}")
        if platform:
            result_parts.append(f"Platform: {platform}")
        result_parts.append("")

        # Summary
        if analysis.get('summary'):
            result_parts.append(f"*Summary:* {analysis['summary']}")
            result_parts.append("")

        # Top performers
        if analysis.get('top_performers'):
            result_parts.append("📈 *TOP PERFORMERS:*")
            for i, post in enumerate(analysis['top_performers'][:3], 1):
                hook = post.get('hook', '')[:100]
                rate = post.get('engagement_rate', 0)
                why = post.get('why_it_worked', 'N/A')
                result_parts.append(f"{i}. {hook}...")
                result_parts.append(f"   Engagement: {rate:.1f}% | Why: {why}")
                result_parts.append("")

        # Worst performers
        if analysis.get('worst_performers'):
            result_parts.append("📉 *NEEDS IMPROVEMENT:*")
            for i, post in enumerate(analysis['worst_performers'][:3], 1):
                hook = post.get('hook', '')[:100]
                rate = post.get('engagement_rate', 0)
                why = post.get('why_it_failed', 'N/A')
                result_parts.append(f"{i}. {hook}...")
                result_parts.append(f"   Engagement: {rate:.1f}% | Issue: {why}")
                result_parts.append("")

        # Patterns
        if analysis.get('patterns'):
            patterns = analysis['patterns']
            result_parts.append("🔍 *PATTERNS DETECTED:*")
            if patterns.get('best_hook_style'):
                result_parts.append(f"• Best hook style: {patterns['best_hook_style']}")
            if patterns.get('best_platform'):
                result_parts.append(f"• Best platform: {patterns['best_platform']}")
            if patterns.get('best_time'):
                result_parts.append(f"• Best posting time: {patterns['best_time']}")
            if patterns.get('avg_engagement_rate'):
                result_parts.append(f"• Avg engagement rate: {patterns['avg_engagement_rate']:.1f}%")
            result_parts.append("")

        # Recommendations
        if analysis.get('recommendations'):
            result_parts.append("💡 *RECOMMENDATIONS:*")
            for i, rec in enumerate(analysis['recommendations'][:5], 1):
                result_parts.append(f"{i}. {rec}")
            result_parts.append("")

        return "\n".join(result_parts)

    except Exception as e:
        logger.error(f"Error in get_post_analytics: {e}")
        return f"Error analyzing posts: {str(e)}\n\nTip: Ensure Ayrshare metrics are synced and posts have performance data."


def show_top_performers(
    count: int = 5,
    platform: str = None,
    days_back: int = 30
) -> str:
    """
    Show top performing posts by engagement rate.

    Returns formatted list of best posts with metrics and why they worked.

    Args:
        count: Number of top posts to show (default: 5)
        platform: Filter by platform (linkedin, twitter, email)
        days_back: Look back N days (default: 30)

    Returns:
        Formatted list of top performers with hooks, scores, metrics
    """
    try:
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        query = client.table('generated_posts')\
            .select('*')\
            .eq('status', 'published')\
            .not_.is_('engagement_rate', 'null')\
            .gte('published_at', cutoff_date)\
            .order('engagement_rate', desc=True)\
            .limit(count)

        if platform:
            query = query.eq('platform', platform.lower())

        result = query.execute()
        posts = result.data

        if not posts:
            return f"No published posts with metrics found in last {days_back} days{' for ' + platform if platform else ''}."

        # Format results
        result_parts = []
        result_parts.append(f"🏆 *TOP {count} PERFORMERS* (last {days_back} days)")
        if platform:
            result_parts.append(f"Platform: {platform}")
        result_parts.append("")

        for i, post in enumerate(posts, 1):
            hook = post.get('post_hook', '')[:120]
            platform_name = post.get('platform', 'unknown').upper()
            score = post.get('quality_score', 0)
            impressions = post.get('impressions', 0)
            engagement_rate = post.get('engagement_rate', 0.0)
            likes = post.get('likes', 0)
            comments = post.get('comments', 0)
            shares = post.get('shares', 0)
            published = post.get('published_at', '')[:10]
            published_url = post.get('published_url', '')

            result_parts.append(f"{i}. [{platform_name}] {hook}...")
            result_parts.append(f"   📊 Engagement: {engagement_rate:.1f}% | Impressions: {impressions:,}")
            result_parts.append(f"   💚 {likes} likes | 💬 {comments} comments | 🔄 {shares} shares")
            result_parts.append(f"   ⭐ Quality: {score}/25 | Published: {published}")
            if published_url:
                result_parts.append(f"   🔗 {published_url}")
            result_parts.append("")

        return "\n".join(result_parts)

    except Exception as e:
        logger.error(f"Error in show_top_performers: {e}")
        return f"Error retrieving top performers: {str(e)}"


def analyze_content_patterns(
    days_back: int = 30,
    min_engagement: float = 5.0,
    top_percent: int = 20
) -> str:
    """
    Analyze content patterns in top-performing posts using semantic analysis.

    Uses vector embeddings to cluster similar high-performers and identify:
    - Common themes (automation, frameworks, case studies)
    - Hook styles (specific numbers, contrarian, bold outcomes)
    - Content structures (numbered lists, stories, Q&A)
    - Awareness levels (problem-aware, solution-aware, product-aware)

    Args:
        days_back: Analyze posts from last N days (default: 30)
        min_engagement: Minimum engagement rate to consider (default: 5.0%)
        top_percent: Analyze top N% of posts (default: 20%)

    Returns:
        Detailed pattern analysis with themes, structures, recommendations
    """
    try:
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Get all published posts with metrics and embeddings
        result = client.table('generated_posts')\
            .select('*')\
            .eq('status', 'published')\
            .not_.is_('engagement_rate', 'null')\
            .not_.is_('embedding', 'null')\
            .gte('published_at', cutoff_date)\
            .gte('engagement_rate', min_engagement)\
            .order('engagement_rate', desc=True)\
            .execute()

        all_posts = result.data

        if not all_posts or len(all_posts) < 3:
            return f"Not enough posts with metrics (need at least 3, found {len(all_posts)}).\n\nTip: Ensure Ayrshare metrics sync has run and posts have been published recently."

        # Get top performers (top N%)
        top_count = max(3, int(len(all_posts) * (top_percent / 100)))
        top_posts = all_posts[:top_count]

        logger.info(f"Analyzing {top_count} top posts out of {len(all_posts)} total")

        # Step 1: Extract embeddings and find similar clusters
        # Use first top post as reference
        reference_post = top_posts[0]
        reference_embedding = reference_post['embedding']

        # Find semantically similar posts using vector search
        similar_posts_result = client.rpc('match_generated_posts', {
            'query_embedding': reference_embedding,
            'match_threshold': 0.7,
            'match_count': min(20, len(top_posts))
        }).execute()

        similar_posts = similar_posts_result.data if similar_posts_result.data else []

        # Step 2: Prepare data for Claude analysis
        top_posts_data = []
        for post in top_posts:
            content_preview = (post.get('body_content') or '')[:500]
            top_posts_data.append({
                'hook': post.get('post_hook', '')[:200],
                'content_preview': content_preview,
                'platform': post.get('platform'),
                'engagement_rate': post.get('engagement_rate', 0.0),
                'impressions': post.get('impressions', 0),
                'content_type': post.get('content_type', 'unknown'),
                'quality_score': post.get('quality_score', 0)
            })

        # Step 3: Use Claude to analyze patterns
        from anthropic import Anthropic

        anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        pattern_prompt = f"""Analyze these {len(top_posts_data)} top-performing posts and identify patterns.

Posts to analyze:
{json.dumps(top_posts_data, indent=2)}

Provide analysis in these categories:

1. **THEMES**: What topics/subjects appear most? (e.g., "AI automation", "case studies", "frameworks")

2. **HOOK STYLES**: What hook patterns are used? (e.g., "Specific Numbers", "Contrarian Takes", "Bold Outcomes")

3. **CONTENT STRUCTURES**: How is content organized? (e.g., "Hook + Numbered List + CTA", "Story format", "Problem → Solution")

4. **AWARENESS LEVELS**: What stage of awareness do these target?
   - Problem-aware: "You have X problem"
   - Solution-aware: "Here's how to solve X"
   - Product-aware: "Use Y tool to solve X"

5. **KEY PATTERNS**: What makes these posts work? Common elements across top performers?

6. **RECOMMENDATIONS**: Based on patterns, what should the creator do more of?

Return as JSON:
{{
  "themes": ["theme1", "theme2"],
  "hook_styles": ["style1", "style2"],
  "structures": ["structure1", "structure2"],
  "awareness_levels": {{"problem_aware": 20, "solution_aware": 60, "product_aware": 20}},
  "key_patterns": ["pattern1", "pattern2"],
  "recommendations": ["rec1", "rec2", "rec3"]
}}"""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": pattern_prompt
            }]
        )

        # Parse Claude's response
        analysis_text = response.content[0].text

        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback if no JSON found
            analysis = {
                "error": "Could not parse analysis",
                "raw_response": analysis_text
            }

        # Step 4: Format results
        result_parts = []

        result_parts.append(f"🎯 *CONTENT PATTERN ANALYSIS* (top {top_percent}% of {len(all_posts)} posts)")
        result_parts.append(f"Analyzed: {len(top_posts)} posts from last {days_back} days")
        result_parts.append(f"Avg engagement: {sum(p.get('engagement_rate', 0) for p in top_posts) / len(top_posts):.1f}%")
        result_parts.append("")

        # Themes
        if analysis.get('themes'):
            result_parts.append("📌 *COMMON THEMES:*")
            for theme in analysis['themes'][:5]:
                result_parts.append(f"• {theme}")
            result_parts.append("")

        # Hook styles
        if analysis.get('hook_styles'):
            result_parts.append("🎣 *EFFECTIVE HOOK STYLES:*")
            for style in analysis['hook_styles'][:5]:
                result_parts.append(f"• {style}")
            result_parts.append("")

        # Structures
        if analysis.get('structures'):
            result_parts.append("📐 *WINNING STRUCTURES:*")
            for structure in analysis['structures'][:5]:
                result_parts.append(f"• {structure}")
            result_parts.append("")

        # Awareness levels
        if analysis.get('awareness_levels'):
            result_parts.append("🧠 *AWARENESS LEVEL BREAKDOWN:*")
            awareness = analysis['awareness_levels']
            for level, percent in awareness.items():
                result_parts.append(f"• {level.replace('_', '-').title()}: {percent}%")
            result_parts.append("")

        # Key patterns
        if analysis.get('key_patterns'):
            result_parts.append("⭐ *KEY SUCCESS PATTERNS:*")
            for pattern in analysis['key_patterns'][:5]:
                result_parts.append(f"• {pattern}")
            result_parts.append("")

        # Recommendations
        if analysis.get('recommendations'):
            result_parts.append("💡 *RECOMMENDATIONS:*")
            for i, rec in enumerate(analysis['recommendations'][:5], 1):
                result_parts.append(f"{i}. {rec}")
            result_parts.append("")

        # Similar clusters info
        if len(similar_posts) > 1:
            result_parts.append(f"🔗 Found {len(similar_posts)} semantically similar high-performers (vector similarity > 70%)")

        return "\n".join(result_parts)

    except Exception as e:
        logger.error(f"Error in analyze_content_patterns: {e}", exc_info=True)
        return f"Error analyzing content patterns: {str(e)}"


# Import asyncio at module level
import asyncio

"""
Analytics Handler - Phase 1 of Analytics & Intelligence System

Analyzes post performance data and returns strategic insights.
Uses Claude Sonnet 4.5 to identify patterns, top/worst performers, and recommendations.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


async def analyze_performance(
    posts: List[Dict[str, Any]],
    date_range: Dict[str, str],
    client: Optional[Anthropic] = None
) -> Dict[str, Any]:
    """
    Analyze post performance data and return strategic insights.

    Uses Claude Sonnet 4.5 to:
    - Identify top/worst performers
    - Detect patterns (hook styles, timing, platforms)
    - Generate actionable recommendations

    Args:
        posts: List of posts with metrics
            Required fields: hook, platform, quality_score, impressions, engagements, engagement_rate, published_at
            Example:
            [
                {
                    "hook": "I replaced 3 workflows...",
                    "platform": "linkedin",
                    "quality_score": 24,
                    "impressions": 15000,
                    "engagements": 1230,
                    "engagement_rate": 8.2,
                    "published_at": "2025-01-20"
                }
            ]
        date_range: Start/end dates for analysis
            Example: {"start": "2025-01-20", "end": "2025-01-27"}

    Returns:
        Dict with:
        - summary: 1-2 sentence overview
        - top_performers: Top 3 posts with why_it_worked
        - worst_performers: Bottom 3 posts with why_it_failed
        - patterns: best_hook_style, best_platform, best_time, avg_engagement_rate
        - recommendations: 3-5 actionable items
    """
    from prompts.analytics_analysis_prompt import ANALYTICS_ANALYSIS_PROMPT

    logger.info(f"Analyzing {len(posts)} posts from {date_range.get('start')} to {date_range.get('end')}")

    # Validate inputs
    if not posts:
        return {
            "error": "No posts provided",
            "summary": "No data to analyze",
            "top_performers": [],
            "worst_performers": [],
            "patterns": {},
            "recommendations": []
        }

    # Format posts as JSON for Claude
    posts_json = json.dumps(posts, indent=2)

    # Construct user prompt
    user_prompt = f"""Analyze these posts from {date_range['start']} to {date_range['end']}:

{posts_json}

Return JSON with:
- summary (1-2 sentences)
- top_performers (top 3 with why_it_worked)
- worst_performers (bottom 3 with why_it_failed)
- patterns (best_hook_style, best_platform, best_time, avg_engagement_rate)
- recommendations (3-5 actionable items)"""

    # Use provided client or create new one
    if client is None:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    try:
        # Call Claude Sonnet 4.5
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            system=ANALYTICS_ANALYSIS_PROMPT,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )

        # Extract text content
        analysis_text = response.content[0].text

        # Parse JSON response
        analysis = json.loads(analysis_text)

        logger.info(f"Analysis complete: {len(analysis.get('recommendations', []))} recommendations generated")

        return analysis

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.error(f"Response text: {analysis_text[:500]}")
        return {
            "error": "Failed to parse analysis response",
            "summary": "Analysis failed due to JSON parsing error",
            "top_performers": [],
            "worst_performers": [],
            "patterns": {},
            "recommendations": []
        }

    except Exception as e:
        logger.error(f"Error analyzing performance: {e}", exc_info=True)
        return {
            "error": str(e),
            "summary": "Analysis failed due to unexpected error",
            "top_performers": [],
            "worst_performers": [],
            "patterns": {},
            "recommendations": []
        }

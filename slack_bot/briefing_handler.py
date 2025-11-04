"""
Briefing Handler - Phase 3 of Analytics & Intelligence System

Combines analytics insights + industry research into cohesive strategic briefing.
Uses Claude Sonnet 4.5 to generate Markdown formatted for Slack.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from anthropic import Anthropic

logger = logging.getLogger(__name__)


async def generate_briefing(
    analytics: Dict[str, Any],
    research: Optional[Dict[str, Any]] = None,
    user_context: Optional[Dict[str, Any]] = None,
    client: Optional[Anthropic] = None
) -> Dict[str, Any]:
    """
    Generate weekly content intelligence briefing.

    Combines:
    - Analytics insights (what's working from analyze_performance)
    - Industry research (what's trending - optional, from agent's web_search)
    - User context (goals, audience, recent topics - optional)

    Args:
        analytics: Output from /api/analyze-performance
            Required fields: summary, top_performers, worst_performers, patterns, recommendations
        research: Optional industry research data
            Can be agent's web_search results or manual input
            Fields: trending_topics (with title, url, summary, relevance, content_angle)
        user_context: Optional user context
            Fields: recent_topics, content_goals, audience

    Returns:
        Dict with:
        - briefing_markdown: Full Markdown briefing for Slack
        - suggested_topics: 5-7 specific content ideas
        - priority_actions: 3-5 immediate next steps
    """
    from prompts.briefing_generator_prompt import BRIEFING_GENERATOR_PROMPT

    logger.info("Generating weekly content intelligence briefing")

    # Validate inputs
    if not analytics:
        return {
            "error": "No analytics data provided",
            "briefing_markdown": "# Error\n\nNo analytics data to generate briefing.",
            "suggested_topics": [],
            "priority_actions": []
        }

    # Default empty structures if not provided
    if research is None:
        research = {"trending_topics": []}
    if user_context is None:
        user_context = {
            "recent_topics": [],
            "content_goals": "thought leadership",
            "audience": "professionals"
        }

    # Format inputs as JSON for Claude
    analytics_json = json.dumps(analytics, indent=2)
    research_json = json.dumps(research, indent=2)
    context_json = json.dumps(user_context, indent=2)

    # Get current date for briefing header
    current_date = datetime.now().strftime("%B %d, %Y")

    # Use provided client or create new one
    if client is None:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    try:
        logger.info("Calling Claude to generate briefing")

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            system=BRIEFING_GENERATOR_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""Generate a weekly content intelligence briefing for {current_date}.

**Analytics Insights:**
{analytics_json}

**Industry Research:**
{research_json}

**User Context:**
{context_json}

Return JSON with:
- briefing_markdown (full Markdown briefing for Slack - use emoji headers 📊, 📰, 💡, 🎯)
- suggested_topics (5-7 specific content ideas as array of strings)
- priority_actions (3-5 immediate next steps as array of strings)"""
            }]
        )

        # Extract text content
        briefing_text = response.content[0].text

        # Handle potential markdown code blocks
        if "```json" in briefing_text:
            briefing_text = briefing_text.split("```json")[1].split("```")[0].strip()
        elif "```" in briefing_text:
            briefing_text = briefing_text.split("```")[1].split("```")[0].strip()

        # Parse JSON response
        briefing = json.loads(briefing_text)

        logger.info(f"Briefing generated: {len(briefing.get('suggested_topics', []))} topics, {len(briefing.get('priority_actions', []))} actions")

        return briefing

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.error(f"Response text: {briefing_text[:500] if 'briefing_text' in locals() else 'N/A'}")
        return {
            "error": "Failed to parse briefing response",
            "briefing_markdown": "# Error\n\nFailed to generate briefing due to JSON parsing error.",
            "suggested_topics": [],
            "priority_actions": []
        }

    except Exception as e:
        logger.error(f"Error generating briefing: {e}", exc_info=True)
        return {
            "error": str(e),
            "briefing_markdown": f"# Error\n\nFailed to generate briefing: {str(e)}",
            "suggested_topics": [],
            "priority_actions": []
        }

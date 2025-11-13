"""
Test Analytics Analysis with Claude

This tests the analytics handler that analyzes performance data.
"""

import asyncio
import json
from slack_bot.analytics_handler import analyze_performance_with_claude
from integrations.ayrshare_client import AyrshareClient

async def test_analytics_analysis():
    """Test analytics analysis with real Ayrshare data."""

    print("\n" + "="*80)
    print("TESTING ANALYTICS ANALYSIS WITH CLAUDE")
    print("="*80)

    # Fetch real data from Ayrshare
    client = AyrshareClient()
    history = client.get_history(days_back=7, platforms=["twitter"], limit=5)

    if not history:
        print("\n❌ No posts found in history")
        return

    print(f"\n✅ Retrieved {len(history)} posts from Ayrshare")

    # Format for analytics handler
    analytics_data = []
    for post in history:
        analytics_data.append({
            "id": post.get("id"),
            "platform": "twitter",
            "hook": post.get("content", "")[:100],
            "published_at": post.get("scheduled_date"),
            "impressions": 0,  # Will be populated if analytics available
            "engagements": 0,
            "engagement_rate": 0.0
        })

    print("\n📊 Analyzing with Claude...")

    # Call analytics handler
    analysis = await analyze_performance_with_claude(analytics_data)

    print("\n" + "="*80)
    print("CLAUDE'S ANALYSIS:")
    print("="*80)
    print(analysis)
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(test_analytics_analysis())

"""
Quick test script for Ayrshare Analytics Integration

Tests:
1. Get post analytics for a specific post ID
2. Get post history (last 7 days)
3. Display analytics data

Usage:
    python test_ayrshare_analytics.py
"""

import os
import sys
from dotenv import load_dotenv
from integrations.ayrshare_client import AyrshareClient

load_dotenv()

def test_history():
    """Test fetching post history."""
    client = AyrshareClient()

    print("\n" + "="*80)
    print("TESTING AYRSHARE HISTORY ENDPOINT")
    print("="*80)

    try:
        history = client.get_history(
            days_back=7,
            platforms=["twitter", "linkedin"],
            limit=10
        )

        print(f"\n✅ Found {len(history)} posts in last 7 days")

        for i, post in enumerate(history, 1):
            print(f"\n📝 Post {i}:")
            print(f"   ID: {post.get('id')}")
            print(f"   Platforms: {post.get('platforms')}")
            print(f"   Content: {post.get('content', '')[:100]}...")
            print(f"   Published: {post.get('scheduled_date')}")
            print(f"   Post IDs: {post.get('post_ids')}")

        return history

    except Exception as e:
        print(f"\n❌ Error fetching history: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_analytics(post_id: str):
    """Test fetching analytics for a specific post."""
    client = AyrshareClient()

    print("\n" + "="*80)
    print(f"TESTING AYRSHARE ANALYTICS FOR POST: {post_id}")
    print("="*80)

    try:
        analytics = client.get_post_analytics(
            post_id=post_id,
            platforms=["twitter", "linkedin"]
        )

        if analytics.get("error"):
            print(f"\n⚠️  Error: {analytics.get('error')}")
            print(f"   Code: {analytics.get('code')}")
            return None

        print(f"\n✅ Analytics retrieved successfully")
        print(f"\n📊 Normalized Metrics:")
        print(f"   Impressions: {analytics.get('impressions', 0):,}")
        print(f"   Engagements: {analytics.get('engagements', 0):,}")
        print(f"   Clicks: {analytics.get('clicks', 0):,}")
        print(f"   Likes: {analytics.get('likes', 0):,}")
        print(f"   Comments: {analytics.get('comments', 0):,}")
        print(f"   Shares: {analytics.get('shares', 0):,}")
        print(f"   Saves: {analytics.get('saves', 0):,}")
        print(f"   Engagement Rate: {analytics.get('engagement_rate', 0):.2%}")

        if analytics.get('platform_data'):
            print(f"\n🔍 Platform-Specific Data:")
            for platform, data in analytics['platform_data'].items():
                print(f"\n   {platform.upper()}:")
                for key, value in data.items():
                    if isinstance(value, dict):
                        print(f"      {key}:")
                        for k, v in value.items():
                            print(f"         {k}: {v}")
                    else:
                        print(f"      {key}: {value}")

        return analytics

    except Exception as e:
        print(f"\n❌ Error fetching analytics: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main test runner."""

    # Check for API key
    api_key = os.getenv('AYRSHARE_API_KEY')
    if not api_key:
        print("\n❌ AYRSHARE_API_KEY not found in environment")
        print("   Add it to your .env file:")
        print("   AYRSHARE_API_KEY=your-key-here")
        sys.exit(1)

    print("\n🔑 Ayrshare API Key found")

    # Test 1: Get history
    history = test_history()

    # Test 2: Get analytics for first post if available
    if history and len(history) > 0:
        first_post_id = history[0].get('id')
        if first_post_id:
            test_analytics(first_post_id)
        else:
            print("\n⚠️  No post ID found in history")
    else:
        print("\n⚠️  No posts found in history")
        print("   You can manually test with a post ID:")
        print("   python test_ayrshare_analytics.py <post_id>")

    print("\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Manual post ID provided
        post_id = sys.argv[1]
        test_analytics(post_id)
    else:
        main()

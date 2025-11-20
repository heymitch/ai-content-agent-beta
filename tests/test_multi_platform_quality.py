#!/usr/bin/env python3
"""
Multi-Platform Content Quality Test
Tests YouTube, Instagram, Email (all types), and Twitter SDK agents
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Test configurations for each platform
TEST_CONFIGS = {
    "twitter": {
        "topic": "Why most AI agents fail at content creation (and the 3 things that actually work)",
        "context": "Focus on practical tips for marketers using AI tools. Include specific examples.",
        "style": "tactical"
    },
    "youtube": {
        "topic": "How to Build an AI Content Agent That Doesn't Sound Like a Robot",
        "context": "10-minute tutorial for developers and marketers. Cover both technical setup and content strategy.",
        "script_type": "educational"
    },
    "instagram": {
        "topic": "The hidden cost of AI-generated content nobody talks about",
        "context": "Thought-provoking post about authenticity vs efficiency. Target small business owners.",
        "style": "inspirational"
    },
    "email": {
        "types": [
            {
                "email_type": "Newsletter",
                "topic": "This Week in AI: 3 Game-Changing Tools You Missed",
                "context": "Weekly roundup for busy executives. Focus on practical applications, not hype."
            },
            {
                "email_type": "Sales",
                "topic": "Your content team is spending 70% of their time on the wrong things",
                "context": "Soft pitch for AI content platform. Problem-focused, not product-focused."
            },
            {
                "email_type": "Value",
                "topic": "The 5-minute content audit that reveals your AI blindspots",
                "context": "Educational email with actionable framework. Include a simple checklist."
            }
        ]
    }
}

def print_section_header(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"🎯 {title}")
    print("=" * 80)

def print_result_summary(result: Dict[str, Any], platform: str):
    """Print a summary of the test result"""
    if result.get('success'):
        # Extract score - handle different response formats
        score = result.get('score', 'N/A')

        # Get content preview
        content = result.get('post') or result.get('thread') or result.get('script') or result.get('caption') or result.get('email', '')
        preview = content[:200] + "..." if len(content) > 200 else content

        # Get hook
        hook = result.get('hook', preview[:100])

        print(f"\n✅ {platform} - SUCCESS")
        print(f"   Score: {score}/25")
        print(f"   Hook: {hook[:100]}...")

        # Check for Airtable URL
        airtable_url = result.get('airtable_url')
        if airtable_url and airtable_url != "[Airtable not configured]":
            print(f"   📊 Airtable: {airtable_url}")

        # Check for validation warnings
        if 'validation' in str(result):
            print("   ⚠️  Validation warnings present (check Suggested Edits)")

    else:
        error = result.get('error', 'Unknown error')
        print(f"\n❌ {platform} - FAILED")
        print(f"   Error: {error[:200]}...")

async def test_twitter():
    """Test Twitter SDK Agent"""
    print_section_header("Testing Twitter SDK Agent")

    from agents.twitter_sdk_agent import TwitterSDKAgent

    agent = TwitterSDKAgent(isolated_mode=True)
    config = TEST_CONFIGS["twitter"]

    print(f"📝 Creating thread about: {config['topic'][:60]}...")
    print(f"   Style: {config['style']}")

    result = await agent.create_thread(
        topic=config['topic'],
        context=config['context'],
        style=config['style'],
        content_length="short_thread",  # 3-4 tweets
        target_score=18  # Twitter has lower threshold
    )

    print_result_summary(result, "Twitter")
    return result

async def test_youtube():
    """Test YouTube SDK Agent"""
    print_section_header("Testing YouTube SDK Agent")

    from agents.youtube_sdk_agent import YouTubeSDKAgent

    agent = YouTubeSDKAgent(isolated_mode=True)
    config = TEST_CONFIGS["youtube"]

    print(f"📝 Creating script about: {config['topic'][:60]}...")
    print(f"   Type: {config['script_type']}")

    result = await agent.create_script(
        topic=config['topic'],
        context=config['context'],
        script_type=config['script_type'],
        video_length="10_min",
        target_score=20
    )

    print_result_summary(result, "YouTube")
    return result

async def test_instagram():
    """Test Instagram SDK Agent"""
    print_section_header("Testing Instagram SDK Agent")

    from agents.instagram_sdk_agent import InstagramSDKAgent

    agent = InstagramSDKAgent(isolated_mode=True)
    config = TEST_CONFIGS["instagram"]

    print(f"📝 Creating caption about: {config['topic'][:60]}...")
    print(f"   Style: {config['style']}")

    result = await agent.create_post(
        topic=config['topic'],
        context=config['context'],
        style=config['style'],
        post_type="single_image",
        target_score=20
    )

    print_result_summary(result, "Instagram")
    return result

async def test_email_type(email_config: Dict[str, str]):
    """Test a specific email type"""
    from agents.email_sdk_agent import EmailSDKAgent

    agent = EmailSDKAgent(isolated_mode=True)

    print(f"\n📧 Testing {email_config['email_type']} email...")
    print(f"   Topic: {email_config['topic'][:60]}...")

    result = await agent.create_email(
        topic=email_config['topic'],
        context=email_config['context'],
        email_type=email_config['email_type'],
        target_score=20
    )

    print_result_summary(result, f"Email ({email_config['email_type']})")
    return result

async def test_all_emails():
    """Test all email types"""
    print_section_header("Testing Email SDK Agent (All Types)")

    results = []
    for email_config in TEST_CONFIGS["email"]["types"]:
        result = await test_email_type(email_config)
        results.append(result)
        await asyncio.sleep(1)  # Small delay between calls

    return results

async def run_all_tests():
    """Run all platform tests"""
    print("\n" + "🚀 " * 20)
    print("MULTI-PLATFORM CONTENT QUALITY TEST")
    print("Testing YouTube, Instagram, Email (3 types), and Twitter")
    print("🚀 " * 20)

    results = {}

    # Test each platform
    try:
        print("\n⏳ This will take 3-5 minutes to complete all tests...\n")

        # Run tests sequentially to avoid overwhelming the API
        results['twitter'] = await test_twitter()
        await asyncio.sleep(2)

        results['youtube'] = await test_youtube()
        await asyncio.sleep(2)

        results['instagram'] = await test_instagram()
        await asyncio.sleep(2)

        results['email'] = await test_all_emails()

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()

    # Print final summary
    print_section_header("TEST SUMMARY")

    success_count = 0
    fail_count = 0

    # Count successes
    for platform, result in results.items():
        if platform == 'email':
            # Handle email array
            for email_result in (result if isinstance(result, list) else [result]):
                if email_result.get('success'):
                    success_count += 1
                else:
                    fail_count += 1
        else:
            if result and result.get('success'):
                success_count += 1
            else:
                fail_count += 1

    total = success_count + fail_count

    print(f"\n📊 Results: {success_count}/{total} tests passed")

    if success_count == total:
        print("✅ All tests passed successfully!")
    elif success_count > 0:
        print("⚠️  Some tests failed - check logs above for details")
    else:
        print("❌ All tests failed - check configuration and API keys")

    # Check for quality issues
    print("\n📋 Quality Check Summary:")
    quality_issues = []

    for platform, result in results.items():
        if platform == 'email':
            for i, email_result in enumerate(result if isinstance(result, list) else [result]):
                if email_result.get('success'):
                    score = email_result.get('score', 0)
                    if score < 18:
                        quality_issues.append(f"Email type {i+1}: Low score ({score}/25)")
        else:
            if result and result.get('success'):
                score = result.get('score', 0)
                expected = 18 if platform == 'twitter' else 20
                if score < expected:
                    quality_issues.append(f"{platform.title()}: Below target ({score}/25, target: {expected})")

    if quality_issues:
        print("⚠️  Quality issues found:")
        for issue in quality_issues:
            print(f"   - {issue}")
    else:
        print("✅ All content met quality thresholds")

    return results

async def test_single_platform(platform: str):
    """Test a single platform"""
    if platform.lower() == 'twitter':
        return await test_twitter()
    elif platform.lower() == 'youtube':
        return await test_youtube()
    elif platform.lower() == 'instagram':
        return await test_instagram()
    elif platform.lower() == 'email':
        return await test_all_emails()
    else:
        print(f"❌ Unknown platform: {platform}")
        print("   Available: twitter, youtube, instagram, email")
        return None

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Test specific platform
        platform = sys.argv[1]
        print(f"Testing {platform} only...")
        result = asyncio.run(test_single_platform(platform))
    else:
        # Test all platforms
        results = asyncio.run(run_all_tests())

    print("\n✨ Test complete!")
    print("=" * 80)
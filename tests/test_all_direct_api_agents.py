"""
Test All Direct API Agents - LinkedIn, Email, YouTube, Instagram, Twitter
Verifies all 5 platforms work as drop-in replacements for SDK agents
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_linkedin():
    """Test LinkedIn direct API agent"""
    print("\n" + "=" * 80)
    print("TEST 1: LINKEDIN - Thermodynamic chip post")
    print("=" * 80)

    from agents.linkedin_direct_api_agent import create_linkedin_post_workflow

    result = await create_linkedin_post_workflow(
        topic="the new thermodynamic computer chip breakthrough",
        context="I'm a kardashev scaler, so focus on what this means for garage builders and open source. I'm optimistic about garage building potential.",
        style="thought_leadership",
        user_id="test_user"
    )

    print(result)
    assert "✅ **LinkedIn Post Created**" in result, "Missing success indicator"
    assert "Quality Score:" in result, "Missing quality score"
    print("\n✅ LINKEDIN TEST PASSED")
    return True


async def test_email():
    """Test Email direct API agent"""
    print("\n" + "=" * 80)
    print("TEST 2: EMAIL - AI agents strategy")
    print("=" * 80)

    from agents.email_direct_api_agent import create_email_workflow

    result = await create_email_workflow(
        topic="How AI agents are changing content strategy",
        context="Focus on practical tips for solo operators building AI-powered content systems",
        style="Email_Value",
        user_id="test_user"
    )

    print(result)
    assert "✅ **Email Post Created**" in result, "Missing success indicator"
    assert "Quality Score:" in result, "Missing quality score"
    print("\n✅ EMAIL TEST PASSED")
    return True


async def test_youtube():
    """Test YouTube direct API agent"""
    print("\n" + "=" * 80)
    print("TEST 3: YOUTUBE - Content automation script")
    print("=" * 80)

    from agents.youtube_direct_api_agent import create_youtube_workflow

    result = await create_youtube_workflow(
        topic="3 ways AI agents will transform content creation in 2025",
        context="Educational video for content creators, focus on actionable insights",
        style="educational",
        user_id="test_user"
    )

    print(result)
    assert "✅ **YouTube Script Created**" in result, "Missing success indicator"
    assert "Quality Score:" in result, "Missing quality score"
    print("\n✅ YOUTUBE TEST PASSED")
    return True


async def test_instagram():
    """Test Instagram direct API agent"""
    print("\n" + "=" * 80)
    print("TEST 4: INSTAGRAM - Creator economy post")
    print("=" * 80)

    from agents.instagram_direct_api_agent import create_instagram_workflow

    result = await create_instagram_workflow(
        topic="Why the creator economy needs better tools",
        context="Inspirational post about empowering solo creators with AI automation",
        style="inspirational",
        user_id="test_user"
    )

    print(result)
    assert "✅ **Instagram Caption Created**" in result, "Missing success indicator"
    assert "Quality Score:" in result, "Missing quality score"
    print("\n✅ INSTAGRAM TEST PASSED")
    return True


async def test_twitter():
    """Test Twitter direct API agent"""
    print("\n" + "=" * 80)
    print("TEST 5: TWITTER - AI agents thread")
    print("=" * 80)

    from agents.twitter_direct_api_agent import create_twitter_post_workflow

    result = await create_twitter_post_workflow(
        topic="5 lessons from building AI content agents",
        context="Short tactical thread about what I learned building content automation systems",
        style="tactical",
        user_id="test_user"
    )

    print(result)
    assert "✅ **Twitter Thread Created**" in result, "Missing success indicator"
    assert "Quality Score:" in result, "Missing quality score"
    print("\n✅ TWITTER TEST PASSED")
    return True


async def run_all_tests():
    """Run all platform tests sequentially"""
    print("\n🧪 TESTING ALL DIRECT API AGENTS")
    print("=" * 80)
    print("Testing 5 platforms: LinkedIn, Email, YouTube, Instagram, Twitter")
    print("=" * 80)

    results = []

    try:
        # Test 1: LinkedIn
        results.append(("LinkedIn", await test_linkedin()))

        # Test 2: Email
        results.append(("Email", await test_email()))

        # Test 3: YouTube
        results.append(("YouTube", await test_youtube()))

        # Test 4: Instagram
        results.append(("Instagram", await test_instagram()))

        # Test 5: Twitter
        results.append(("Twitter", await test_twitter()))

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        for platform, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{platform:15s} {status}")

        all_passed = all(result[1] for result in results)

        if all_passed:
            print("\n" + "=" * 80)
            print("✅ ALL TESTS PASSED")
            print("=" * 80)
            print("\n🎉 All 5 direct API agents working correctly!")
            print("Ready for batch orchestrator integration.\n")
            return True
        else:
            print("\n" + "=" * 80)
            print("❌ SOME TESTS FAILED")
            print("=" * 80)
            return False

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TESTS FAILED")
        print("=" * 80)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

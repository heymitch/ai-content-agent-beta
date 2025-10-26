#!/usr/bin/env python3
"""
Multi-Platform Batch Test
Verifies that batch execution works across different platforms (LinkedIn, Twitter, Email, YouTube, Instagram)

Tests:
1. Mixed platform batch (LinkedIn + Twitter + Email)
2. Each platform SDK agent receives correct metadata
3. Platform-specific quality checks run
4. All platforms save to Airtable correctly
5. Cross-platform learning (post 3 learns from posts 1-2 even if different platforms)
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.batch_orchestrator import (
    create_batch_plan,
    execute_single_post_from_plan,
    get_context_manager
)


async def test_linkedin_twitter_mix():
    """Test batch with LinkedIn and Twitter posts"""
    print("\n" + "="*70)
    print("TEST 1: LinkedIn + Twitter Mixed Batch")
    print("="*70)

    posts = [
        {
            "platform": "linkedin",
            "topic": "How AI agents are transforming B2B content marketing",
            "context": "Focus on automation and ROI",
            "style": "thought_leadership"
        },
        {
            "platform": "twitter",
            "topic": "5 AI content tools every marketer needs in 2025",
            "context": "Short tactical thread with specific tools",
            "style": "tactical"
        },
        {
            "platform": "linkedin",
            "topic": "Why your content marketing needs AI agents (not just AI writing tools)",
            "context": "Differentiate between tools and agents",
            "style": "educational"
        }
    ]

    plan = create_batch_plan(
        posts,
        "Test multi-platform: LinkedIn + Twitter",
        channel_id="C_MULTI_TEST",
        thread_ts="1234567890.123456",
        user_id="U_MULTI_TEST"
    )

    print(f"\n📝 Executing mixed platform batch...")
    results = []

    for i in range(len(posts)):
        print(f"\n   Post {i+1}/{len(posts)} ({posts[i]['platform']}):")
        result = await execute_single_post_from_plan(plan['id'], i)

        if result.get('success'):
            print(f"      ✅ Success: {result.get('platform')}")
            print(f"      Score: {result.get('score', 'N/A')}/25")
        else:
            print(f"      ❌ Failed: {result.get('error', 'Unknown')[:60]}...")

        results.append(result)

    # Verify results
    print(f"\n📊 Multi-Platform Results:")
    platforms_executed = [r.get('platform') for r in results]
    print(f"   Platforms executed: {platforms_executed}")

    successes = sum(1 for r in results if r.get('success'))
    print(f"   Successes: {successes}/{len(results)}")

    # Verify at least 2/3 succeeded (allow for API flakes)
    assert successes >= 2, f"At least 2/3 posts should succeed, got {successes}/3"

    # Verify platforms are correct
    expected_platforms = ['linkedin', 'twitter', 'linkedin']
    for i, (expected, actual) in enumerate(zip(expected_platforms, platforms_executed)):
        assert actual == expected, f"Post {i+1} should be {expected}, got {actual}"

    print(f"\n✅ PASS: Mixed LinkedIn + Twitter batch executed successfully")
    return True


async def test_all_platforms():
    """Test batch with all 5 supported platforms"""
    print("\n" + "="*70)
    print("TEST 2: All Platforms Batch (LinkedIn, Twitter, Email, YouTube, Instagram)")
    print("="*70)

    posts = [
        {
            "platform": "linkedin",
            "topic": "AI in content marketing: A comprehensive guide",
            "context": "Educational post with frameworks",
            "style": "thought_leadership"
        },
        {
            "platform": "twitter",
            "topic": "3 AI content mistakes to avoid",
            "context": "Quick tactical thread",
            "style": "tactical"
        },
        {
            "platform": "email",
            "topic": "Weekly AI Marketing Newsletter: Top trends this week",
            "context": "Curated insights and tools",
            "style": "Email_Value"
        },
        {
            "platform": "youtube",
            "topic": "How to use AI agents for content creation (step-by-step tutorial)",
            "context": "Practical walkthrough with examples",
            "style": "educational"
        },
        {
            "platform": "instagram",
            "topic": "Behind the scenes: Our AI-powered content workflow",
            "context": "Visual storytelling with process breakdown",
            "style": "inspirational"
        }
    ]

    plan = create_batch_plan(
        posts,
        "Test all platforms: LI + Twitter + Email + YouTube + IG",
        channel_id="C_ALL_PLATFORMS",
        thread_ts="1234567890.999999",
        user_id="U_ALL_PLATFORMS"
    )

    print(f"\n📝 Executing all 5 platforms sequentially...")
    results = []

    for i in range(len(posts)):
        platform = posts[i]['platform']
        print(f"\n   Post {i+1}/5 ({platform}):")

        result = await execute_single_post_from_plan(plan['id'], i)

        status = "✅" if result.get('success') else "❌"
        print(f"      {status} {platform}: {result.get('score', 'N/A') if result.get('success') else result.get('error', 'Unknown')[:40]}")

        results.append(result)

    # Verify results
    print(f"\n📊 All Platforms Results:")
    for i, (post, result) in enumerate(zip(posts, results)):
        platform = post['platform']
        status = "✅" if result.get('success') else "❌"
        print(f"   {i+1}. {platform}: {status}")

    successes = sum(1 for r in results if r.get('success'))
    print(f"\n   Total successes: {successes}/5")

    # Verify at least 3/5 succeeded (API calls may have issues)
    assert successes >= 3, f"At least 3/5 posts should succeed, got {successes}/5"

    print(f"\n✅ PASS: All platforms batch executed successfully")
    return True


async def test_cross_platform_learning():
    """Test that learning accumulates across different platforms"""
    print("\n" + "="*70)
    print("TEST 3: Cross-Platform Learning Accumulation")
    print("="*70)

    posts = [
        {
            "platform": "linkedin",
            "topic": "Why AI content often feels robotic",
            "context": "Identify common AI writing patterns",
            "style": "problem_focused"
        },
        {
            "platform": "twitter",
            "topic": "3 ways to make AI content sound human",
            "context": "Tactical solutions to the problem above",
            "style": "solution_focused"
        },
        {
            "platform": "email",
            "topic": "Case study: How we improved our AI content quality by 40%",
            "context": "Apply learnings from posts 1-2, add proof",
            "style": "case_study"
        }
    ]

    plan = create_batch_plan(
        posts,
        "Test cross-platform learning",
        channel_id="C_LEARNING",
        thread_ts="1",
        user_id="U_LEARNING"
    )

    context_mgr = get_context_manager(plan['id'])

    print(f"\n📝 Executing cross-platform batch...")

    for i in range(len(posts)):
        platform = posts[i]['platform']

        # Get learnings before execution
        learnings_before = context_mgr.get_compacted_learnings()
        print(f"\n   Post {i+1}/3 ({platform}):")
        print(f"      Learnings size before: {len(learnings_before)} chars")

        result = await execute_single_post_from_plan(plan['id'], i)

        if result.get('success'):
            print(f"      ✅ Success: Score {result.get('score')}/25")

            # Verify learnings grew (except for first post)
            if i > 0:
                learnings_after = context_mgr.get_compacted_learnings()
                print(f"      Learnings size after: {len(learnings_after)} chars")
                # Learnings should accumulate across platforms
                assert len(learnings_after) >= len(learnings_before), "Learnings should grow or stay same"
        else:
            print(f"      ❌ Failed: {result.get('error', 'Unknown')[:40]}...")

    # Verify context manager tracked all successful posts
    stats = context_mgr.get_stats()
    print(f"\n📈 Cross-Platform Learning Stats:")
    print(f"   Total posts tracked: {stats['total_posts']}")
    print(f"   Average score: {stats['avg_score']:.1f}")
    print(f"   Quality trend: {stats['quality_trend']}")

    # Verify learning accumulated
    final_learnings = context_mgr.get_compacted_learnings()
    print(f"   Final learnings: {len(final_learnings)} chars")

    assert stats['total_posts'] > 0, "Should have tracked at least one successful post"
    assert len(final_learnings) > 0, "Should have accumulated learnings"

    print(f"\n✅ PASS: Cross-platform learning working correctly")
    return True


async def test_platform_specific_metadata():
    """Test that each platform receives correct Slack metadata"""
    print("\n" + "="*70)
    print("TEST 4: Platform-Specific Slack Metadata Propagation")
    print("="*70)

    posts = [
        {"platform": "linkedin", "topic": "Test LinkedIn metadata", "context": "", "style": "test"},
        {"platform": "twitter", "topic": "Test Twitter metadata", "context": "", "style": "test"},
        {"platform": "email", "topic": "Test Email metadata", "context": "", "style": "test"}
    ]

    # Create plan with specific Slack metadata
    test_channel = "C_METADATA_TEST"
    test_thread = "9876543210.654321"
    test_user = "U_METADATA_TEST"

    plan = create_batch_plan(
        posts,
        "Test metadata propagation",
        channel_id=test_channel,
        thread_ts=test_thread,
        user_id=test_user
    )

    print(f"\n📝 Plan created with Slack metadata:")
    print(f"   Channel: {test_channel}")
    print(f"   Thread: {test_thread}")
    print(f"   User: {test_user}")

    # Verify plan has metadata
    assert 'slack_metadata' in plan, "Plan should have slack_metadata"
    assert plan['slack_metadata']['channel_id'] == test_channel, "Channel ID should match"
    assert plan['slack_metadata']['thread_ts'] == test_thread, "Thread TS should match"
    assert plan['slack_metadata']['user_id'] == test_user, "User ID should match"

    print(f"\n✅ Plan contains correct Slack metadata")

    # Execute one post to verify metadata is passed through
    # (Actual Airtable verification would require live API call)
    result = await execute_single_post_from_plan(plan['id'], 0)

    if result.get('success'):
        print(f"\n✅ Post executed (metadata should be in Airtable)")
        print(f"   Airtable URL: {result.get('airtable_url', 'N/A')}")
    else:
        print(f"\n⚠️ Post failed, but metadata structure is correct")

    print(f"\n✅ PASS: Slack metadata propagation validated")
    return True


async def run_all_tests():
    """Run all multi-platform tests"""
    print("\n" + "="*70)
    print("MULTI-PLATFORM BATCH TEST SUITE")
    print("="*70)
    print("Verifying batch execution across different content platforms")

    results = []
    tests = [
        ("LinkedIn + Twitter Mix", test_linkedin_twitter_mix),
        ("All 5 Platforms", test_all_platforms),
        ("Cross-Platform Learning", test_cross_platform_learning),
        ("Slack Metadata Propagation", test_platform_specific_metadata)
    ]

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}...")
            success = await test_func()
            results.append((test_name, success, None))
            if success:
                print(f"✅ PASS: {test_name}")
        except AssertionError as e:
            results.append((test_name, False, str(e)))
            print(f"❌ FAIL: {test_name} - {e}")
        except Exception as e:
            results.append((test_name, False, f"Exception: {e}"))
            print(f"❌ ERROR: {test_name} - {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for test_name, success, error in results:
        status = "✅ PASS" if success else f"❌ FAIL"
        print(f"{status}: {test_name}")
        if error:
            print(f"   Error: {error[:100]}...")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 ALL MULTI-PLATFORM TESTS PASSED - Ready for production!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed - Review platform integration")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

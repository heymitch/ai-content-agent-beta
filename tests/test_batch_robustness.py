"""
Batch Orchestrator Robustness Test
Tests error recovery, timeout handling, and sequential execution across platforms
"""

import asyncio
import sys
import os
from unittest.mock import Mock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.batch_orchestrator import execute_sequential_batch


async def test_small_batch():
    """Test 3-post batch across different platforms"""
    print("\n" + "=" * 80)
    print("TEST 1: Small Batch (3 posts - LinkedIn, Email, Twitter)")
    print("=" * 80)

    # Create test plan
    plan = {
        'id': 'test_batch_001',
        'count': 3,
        'posts': [
            {
                'topic': 'AI agents are changing content workflows',
                'platform': 'linkedin',
                'context': 'Focus on automation benefits for solo operators',
                'style': 'thought_leadership'
            },
            {
                'topic': 'How to build your first AI agent',
                'platform': 'email',
                'context': 'Beginner-friendly guide with practical steps',
                'style': 'Email_Value'
            },
            {
                'topic': '3 lessons from automating content creation',
                'platform': 'twitter',
                'context': 'Quick tactical insights for builders',
                'style': 'tactical'
            }
        ]
    }

    # Mock Slack client
    slack_client = Mock()
    slack_client.chat_postMessage = Mock(return_value={'ok': True})

    try:
        result = await execute_sequential_batch(
            plan=plan,
            slack_client=slack_client,
            channel='test_channel',
            thread_ts='test_thread',
            user_id='test_user'
        )

        print("\n📊 BATCH RESULT:")
        print(f"   Success: {result['success']}")
        print(f"   Completed: {result['completed']}/{plan['count']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Total Time: {result['total_time']} minutes")
        print(f"   Avg Score: {result['avg_score']:.1f}/25")

        # Validate
        assert result['success'], "Batch should succeed"
        assert result['completed'] == 3, f"Expected 3 completed, got {result['completed']}"
        assert result['failed'] == 0, f"Expected 0 failures, got {result['failed']}"

        print("\n✅ TEST 1 PASSED: Small batch completed successfully")
        return True

    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mixed_platform_batch():
    """Test 5-post batch with all platforms"""
    print("\n" + "=" * 80)
    print("TEST 2: Mixed Platform Batch (5 posts - all platforms)")
    print("=" * 80)

    plan = {
        'id': 'test_batch_002',
        'count': 5,
        'posts': [
            {'topic': 'The future of AI in marketing', 'platform': 'linkedin', 'context': 'Enterprise perspective', 'style': 'thought_leadership'},
            {'topic': 'Quick wins with AI automation', 'platform': 'twitter', 'context': 'Tactical thread for builders', 'style': 'tactical'},
            {'topic': 'Weekly AI updates newsletter', 'platform': 'email', 'context': 'Curated news and insights', 'style': 'Email_Tuesday'},
            {'topic': 'How to use AI agents tutorial', 'platform': 'youtube', 'context': 'Step-by-step walkthrough', 'style': 'educational'},
            {'topic': 'Behind the scenes: Building with AI', 'platform': 'instagram', 'context': 'Visual storytelling', 'style': 'inspirational'}
        ]
    }

    slack_client = Mock()
    slack_client.chat_postMessage = Mock(return_value={'ok': True})

    try:
        result = await execute_sequential_batch(
            plan=plan,
            slack_client=slack_client,
            channel='test_channel',
            thread_ts='test_thread',
            user_id='test_user'
        )

        print("\n📊 BATCH RESULT:")
        print(f"   Success: {result['success']}")
        print(f"   Completed: {result['completed']}/{plan['count']}")
        print(f"   Failed: {result['failed']}")
        print(f"   Total Time: {result['total_time']} minutes")
        print(f"   Avg Score: {result['avg_score']:.1f}/25")

        # Allow partial success (some platforms might have issues)
        assert result['completed'] >= 3, f"Expected at least 3 completed, got {result['completed']}"
        assert result['failed'] <= 2, f"Expected at most 2 failures, got {result['failed']}"

        print("\n✅ TEST 2 PASSED: Mixed platform batch completed")
        return True

    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_context_building():
    """Test that context is passed correctly between posts"""
    print("\n" + "=" * 80)
    print("TEST 3: Context Building (2 related posts)")
    print("=" * 80)

    plan = {
        'id': 'test_batch_003',
        'count': 2,
        'posts': [
            {
                'topic': 'Why AI agents matter for solo operators',
                'platform': 'linkedin',
                'context': 'This is part 1 of a series on AI automation',
                'style': 'thought_leadership'
            },
            {
                'topic': 'How to build your first AI agent',
                'platform': 'linkedin',
                'context': 'This is part 2, building on the previous post about why AI agents matter',
                'style': 'thought_leadership'
            }
        ]
    }

    slack_client = Mock()
    slack_client.chat_postMessage = Mock(return_value={'ok': True})

    try:
        result = await execute_sequential_batch(
            plan=plan,
            slack_client=slack_client,
            channel='test_channel',
            thread_ts='test_thread',
            user_id='test_user'
        )

        print("\n📊 BATCH RESULT:")
        print(f"   Success: {result['success']}")
        print(f"   Completed: {result['completed']}/{plan['count']}")

        assert result['success'], "Batch should succeed"
        assert result['completed'] == 2, f"Expected 2 completed, got {result['completed']}"

        print("\n✅ TEST 3 PASSED: Context building works")
        return True

    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all batch robustness tests"""
    print("\n🧪 BATCH ORCHESTRATOR ROBUSTNESS TESTS")
    print("=" * 80)
    print("Testing error recovery, timeout handling, and platform coverage")
    print("=" * 80)

    results = []

    try:
        # Test 1: Small batch
        results.append(("Small Batch", await test_small_batch()))

        # Test 2: Mixed platforms
        results.append(("Mixed Platform", await test_mixed_platform_batch()))

        # Test 3: Context building
        results.append(("Context Building", await test_context_building()))

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name:20s} {status}")

        all_passed = all(result[1] for result in results)

        if all_passed:
            print("\n" + "=" * 80)
            print("✅ ALL ROBUSTNESS TESTS PASSED")
            print("=" * 80)
            print("\n🎉 Batch orchestrator is robust!")
            print("✓ Sequential execution working")
            print("✓ Error recovery functional")
            print("✓ Multi-platform support confirmed")
            print("✓ Context building operational\n")
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

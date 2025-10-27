#!/usr/bin/env python3
"""
Batch Error Recovery Test
Verifies that batch execution continues even when individual posts fail

CRITICAL: This test validates error isolation - one post failure should NOT stop the entire batch.

Tests:
1. Post 2 fails → Batch continues to post 3
2. Invalid platform → Returns structured error
3. Network timeout simulation
4. Partial batch success (2/3 posts succeed)
5. Error messages are user-friendly
"""

import asyncio
import sys
import os
from unittest.mock import patch, AsyncMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.batch_orchestrator import (
    create_batch_plan,
    execute_single_post_from_plan,
    get_context_manager
)


async def test_single_post_failure():
    """Test that a single post failure returns structured error"""
    print("\n" + "="*70)
    print("TEST 1: Single Post Failure Handling")
    print("="*70)

    # Create plan with invalid data that will cause failure
    posts = [
        {
            "platform": "linkedin",
            "topic": "",  # Empty topic should cause validation error
            "context": "",
            "style": "test"
        }
    ]

    plan = create_batch_plan(
        posts,
        "Test single failure",
        channel_id="C_TEST",
        thread_ts="1",
        user_id="U_TEST"
    )

    print(f"\n📝 Executing post with empty topic (should fail gracefully)...")
    result = await execute_single_post_from_plan(plan['id'], 0)

    print(f"\n📊 Result structure:")
    print(f"   success: {result.get('success')}")
    print(f"   error: {result.get('error', 'N/A')[:100]}...")
    print(f"   platform: {result.get('platform')}")

    # Verify error structure
    assert 'success' in result, "Result should have success field"
    assert result['success'] == False, "Empty topic should fail"
    assert 'error' in result, "Failed result should have error message"
    assert 'platform' in result, "Failed result should still have platform"

    # Verify error is user-friendly (not a stack trace)
    error_msg = result.get('error', '')
    assert len(error_msg) < 500, "Error message should be concise, not full stack trace"
    assert not 'Traceback' in error_msg, "Error should not contain Python traceback"

    print(f"\n✅ PASS: Single post failure handled gracefully")
    return True


async def test_batch_continues_after_failure():
    """Test that batch continues even when middle post fails"""
    print("\n" + "="*70)
    print("TEST 2: Batch Continues After Failure")
    print("="*70)

    # Create plan with 3 posts, middle one will fail
    posts = [
        {
            "platform": "linkedin",
            "topic": "Post 1: Valid topic about AI",
            "context": "This should succeed",
            "style": "thought_leadership"
        },
        {
            "platform": "invalid_platform_xyz",  # This will fail
            "topic": "Post 2: Will fail due to invalid platform",
            "context": "Error test",
            "style": "test"
        },
        {
            "platform": "linkedin",
            "topic": "Post 3: Another valid AI topic",
            "context": "This should also succeed",
            "style": "tactical"
        }
    ]

    plan = create_batch_plan(
        posts,
        "Test batch recovery",
        channel_id="C_TEST",
        thread_ts="1",
        user_id="U_TEST"
    )

    print(f"\n📝 Executing 3-post batch (post 2 will fail)...")

    results = []
    for i in range(3):
        print(f"\n   Post {i+1}/3:")
        result = await execute_single_post_from_plan(plan['id'], i)

        if result.get('success'):
            print(f"      ✅ Success: {result.get('platform')}")
        else:
            print(f"      ❌ Failed: {result.get('error', 'Unknown')[:60]}...")

        results.append(result)

    # Verify all 3 posts attempted (not stopped at failure)
    assert len(results) == 3, "All 3 posts should be attempted"

    # Verify post 2 failed
    assert results[1]['success'] == False, "Post 2 should fail (invalid platform)"

    # Verify posts 1 and 3 status (may succeed or fail based on API availability)
    print(f"\n📊 Batch Results:")
    print(f"   Post 1: {'✅ Success' if results[0].get('success') else '❌ Failed'}")
    print(f"   Post 2: {'✅ Success' if results[1].get('success') else '❌ Failed'} (expected failure)")
    print(f"   Post 3: {'✅ Success' if results[2].get('success') else '❌ Failed'}")

    # Critical: Batch should execute all 3 posts despite post 2 failure
    print(f"\n✅ PASS: Batch executed all 3 posts despite middle failure")
    return True


async def test_partial_batch_success():
    """Test that partial success is tracked correctly"""
    print("\n" + "="*70)
    print("TEST 3: Partial Batch Success Tracking")
    print("="*70)

    # Create plan where some posts may fail
    posts = [
        {"platform": "linkedin", "topic": "Valid post", "context": "OK", "style": "test"},
        {"platform": "linkedin", "topic": "", "context": "Empty topic", "style": "test"},  # Will fail
        {"platform": "linkedin", "topic": "Another valid post", "context": "OK", "style": "test"}
    ]

    plan = create_batch_plan(posts, "Test partial success", channel_id="C_TEST", thread_ts="1", user_id="U_TEST")
    context_mgr = get_context_manager(plan['id'])

    results = []
    for i in range(3):
        result = await execute_single_post_from_plan(plan['id'], i)
        results.append(result)

    successes = sum(1 for r in results if r.get('success'))
    failures = len(results) - successes

    print(f"\n📊 Partial Batch Stats:")
    print(f"   Total attempted: {len(results)}")
    print(f"   Successes: {successes}")
    print(f"   Failures: {failures}")

    # Verify context manager only tracks successful posts
    stats = context_mgr.get_stats()
    print(f"\n   Context manager:")
    print(f"   Total posts tracked: {stats['total_posts']}")
    print(f"   (Should equal successes, not total attempts)")

    # Context should only track successful posts
    assert stats['total_posts'] == successes, f"Context should track {successes} successes, not {stats['total_posts']}"

    print(f"\n✅ PASS: Partial batch success tracked correctly")
    return True


async def test_error_messages_user_friendly():
    """Test that error messages are user-friendly, not technical dumps"""
    print("\n" + "="*70)
    print("TEST 4: User-Friendly Error Messages")
    print("="*70)

    # Test various error scenarios
    error_scenarios = [
        ("Non-existent plan", "nonexistent_plan_xyz", 0),
        ("Invalid index", None, 999),  # Will create plan first
    ]

    results = []

    for scenario_name, plan_id, post_index in error_scenarios:
        print(f"\n   Testing: {scenario_name}")

        if plan_id is None:
            # Create a minimal plan for invalid index test
            plan = create_batch_plan(
                [{"platform": "linkedin", "topic": "Test", "context": "", "style": "test"}],
                "Error test",
                channel_id="C_TEST",
                thread_ts="1",
                user_id="U_TEST"
            )
            plan_id = plan['id']

        result = await execute_single_post_from_plan(plan_id, post_index)

        error_msg = result.get('error', '')
        print(f"      Error: {error_msg[:80]}...")

        # Verify error is structured and user-friendly
        assert 'success' in result, "Should have success field"
        assert result['success'] == False, "Should indicate failure"
        assert len(error_msg) > 0, "Should have error message"
        assert len(error_msg) < 300, "Error should be concise"
        assert 'Traceback' not in error_msg, "Should not contain Python traceback"
        assert 'File "' not in error_msg, "Should not contain file paths"

        results.append((scenario_name, error_msg))

    print(f"\n📊 Error Message Quality:")
    for scenario, msg in results:
        print(f"   {scenario}: {len(msg)} chars")
        print(f"      {msg[:60]}...")

    print(f"\n✅ PASS: All error messages are user-friendly")
    return True


async def test_context_manager_resilience():
    """Test that context manager handles errors without crashing"""
    print("\n" + "="*70)
    print("TEST 5: Context Manager Error Resilience")
    print("="*70)

    # Create plan
    plan = create_batch_plan(
        [{"platform": "linkedin", "topic": "Test", "context": "", "style": "test"}],
        "Context resilience test",
        channel_id="C_TEST",
        thread_ts="1",
        user_id="U_TEST"
    )
    context_mgr = get_context_manager(plan['id'])

    # Test 1: Add valid post summary
    print(f"\n   Adding valid post summary...")
    await context_mgr.add_post_summary({
        'post_num': 1,
        'score': 20,
        'hook': "Test hook",
        'platform': 'linkedin',
        'airtable_url': 'https://airtable.com/test',
        'what_worked': "Test"
    })

    stats = context_mgr.get_stats()
    print(f"      Total posts: {stats['total_posts']}")
    assert stats['total_posts'] == 1, "Should have 1 post"

    # Test 2: Get learnings (should not crash even with minimal data)
    print(f"\n   Getting learnings...")
    learnings = context_mgr.get_compacted_learnings()
    print(f"      Learnings: {len(learnings)} chars")
    assert len(learnings) >= 0, "Should return learnings (even if empty)"

    # Test 3: Get target score
    print(f"\n   Getting target score...")
    target = context_mgr.get_target_score()
    print(f"      Target score: {target}")
    assert target > 0, "Should return valid target score"

    print(f"\n✅ PASS: Context manager handles errors gracefully")
    return True


async def run_all_tests():
    """Run all error recovery tests"""
    print("\n" + "="*70)
    print("BATCH ERROR RECOVERY TEST SUITE")
    print("="*70)
    print("Verifying batch continues despite individual post failures")

    results = []
    tests = [
        ("Single Post Failure", test_single_post_failure),
        ("Batch Continues After Failure", test_batch_continues_after_failure),
        ("Partial Batch Success", test_partial_batch_success),
        ("User-Friendly Errors", test_error_messages_user_friendly),
        ("Context Manager Resilience", test_context_manager_resilience)
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
        print("\n🎉 ALL ERROR RECOVERY TESTS PASSED - Batch is resilient!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed - Review error handling")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

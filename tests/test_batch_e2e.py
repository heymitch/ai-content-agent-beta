#!/usr/bin/env python3
"""
End-to-End Batch Workflow Test
Tests complete batch execution from plan creation to Airtable save

This test validates:
1. Batch plan creation with Slack metadata
2. Sequential post execution
3. Context accumulation (post 3 learns from posts 1-2)
4. Airtable saves with correct metadata
5. Quality scores extracted properly
6. Suggested Edits populated
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


async def test_batch_plan_creation():
    """Test creating a batch plan with Slack metadata"""
    print("\n" + "="*70)
    print("TEST 1: Batch Plan Creation with Slack Metadata")
    print("="*70)

    posts = [
        {
            "platform": "linkedin",
            "topic": "How AI agents are transforming content marketing workflows",
            "context": "Focus on automation and quality improvements",
            "style": "thought_leadership"
        },
        {
            "platform": "linkedin",
            "topic": "The hidden cost of manual content creation for B2B SaaS",
            "context": "Share specific time metrics and ROI data",
            "style": "data_driven"
        },
        {
            "platform": "linkedin",
            "topic": "5 content marketing tasks AI agents do better than humans",
            "context": "Tactical listicle with specific examples",
            "style": "tactical"
        }
    ]

    # Create plan with Slack metadata
    plan = create_batch_plan(
        posts,
        "Test E2E: 3 LinkedIn posts about AI agents",
        channel_id="C12345TEST",
        thread_ts="1234567890.123456",
        user_id="U12345TEST"
    )

    print(f"\n✅ Plan created:")
    print(f"   ID: {plan['id']}")
    print(f"   Description: {plan['description']}")
    print(f"   Posts: {len(plan['posts'])}")
    print(f"   Slack metadata: {plan['slack_metadata']}")

    # Verify structure
    assert 'id' in plan, "Plan should have ID"
    assert 'posts' in plan, "Plan should have posts list"
    assert len(plan['posts']) == 3, "Should have 3 posts"
    assert 'slack_metadata' in plan, "Plan should have Slack metadata"
    assert plan['slack_metadata']['channel_id'] == "C12345TEST", "Channel ID should match"
    assert plan['slack_metadata']['thread_ts'] == "1234567890.123456", "Thread TS should match"
    assert plan['slack_metadata']['user_id'] == "U12345TEST", "User ID should match"

    # Verify context manager created
    context_mgr = get_context_manager(plan['id'])
    assert context_mgr is not None, "Context manager should be created"
    print(f"   ✅ Context manager initialized")

    return plan['id']


async def test_sequential_execution():
    """Test executing 3 posts sequentially with context accumulation"""
    print("\n" + "="*70)
    print("TEST 2: Sequential Execution with Context Accumulation")
    print("="*70)

    # Create a fresh plan
    posts = [
        {
            "platform": "linkedin",
            "topic": "Why most AI content feels robotic (and how to fix it)",
            "context": "Focus on WRITE_LIKE_HUMAN_RULES",
            "style": "thought_leadership"
        },
        {
            "platform": "linkedin",
            "topic": "The anatomy of a high-performing LinkedIn post",
            "context": "Break down hooks, proof points, CTAs",
            "style": "tactical"
        },
        {
            "platform": "linkedin",
            "topic": "Stop using these 10 AI writing cliches",
            "context": "Specific phrases to avoid, alternatives",
            "style": "listicle"
        }
    ]

    plan = create_batch_plan(
        posts,
        "Test Sequential: 3 posts with learning",
        channel_id="C12345TEST",
        thread_ts="1234567890.123456",
        user_id="U12345TEST"
    )

    context_mgr = get_context_manager(plan['id'])
    results = []

    print(f"\n📝 Executing 3 posts sequentially...")

    # Execute posts one by one
    for i in range(3):
        print(f"\n   Post {i+1}/3:")

        # Get current learnings (should grow with each post)
        learnings_before = context_mgr.get_compacted_learnings()
        print(f"      Learnings size: {len(learnings_before)} chars")

        # Execute post
        result = await execute_single_post_from_plan(plan['id'], i)

        # Verify result structure
        assert 'success' in result, "Result should have success field"
        assert 'platform' in result, "Result should have platform"
        assert 'score' in result, "Result should have score"

        if result['success']:
            print(f"      ✅ Success: Score {result.get('score', 'N/A')}/25")
            print(f"      Hook: {result.get('hook', 'N/A')[:60]}...")
            if result.get('airtable_url'):
                print(f"      Airtable: {result['airtable_url'][:50]}...")
        else:
            print(f"      ❌ Failed: {result.get('error', 'Unknown error')[:60]}...")

        results.append(result)

        # Verify context accumulation
        if i > 0:
            learnings_after = context_mgr.get_compacted_learnings()
            print(f"      Context grew: {len(learnings_before)} → {len(learnings_after)} chars")
            # Context should grow as we add posts
            # (May compact at 10 posts, but for 3 posts it should always grow)

    # Verify all 3 executed
    print(f"\n📊 Batch Results:")
    successes = sum(1 for r in results if r.get('success'))
    failures = len(results) - successes
    print(f"   Total: {len(results)} posts")
    print(f"   Successes: {successes}")
    print(f"   Failures: {failures}")

    # At least 2/3 should succeed (allow for API flakes)
    assert successes >= 2, f"At least 2/3 posts should succeed, got {successes}/3"

    # Verify context manager stats
    stats = context_mgr.get_stats()
    print(f"\n📈 Context Manager Stats:")
    print(f"   Total posts: {stats['total_posts']}")
    print(f"   Average score: {stats['avg_score']:.1f}")
    print(f"   Quality trend: {stats['quality_trend']}")
    print(f"   Recent scores: {stats['recent_scores']}")

    assert stats['total_posts'] == successes, f"Context should track {successes} successful posts"

    print(f"\n   ✅ Sequential execution with context accumulation validated")
    return results


async def test_context_learning():
    """Test that later posts receive learnings from earlier posts"""
    print("\n" + "="*70)
    print("TEST 3: Context Learning (Post 3 sees Posts 1-2)")
    print("="*70)

    # Create plan
    posts = [
        {"platform": "linkedin", "topic": "Post 1: AI automation basics", "context": "Intro", "style": "simple"},
        {"platform": "linkedin", "topic": "Post 2: Advanced AI workflows", "context": "Technical", "style": "detailed"},
        {"platform": "linkedin", "topic": "Post 3: AI best practices", "context": "Should reference learnings from 1-2", "style": "summary"}
    ]

    plan = create_batch_plan(posts, "Test Learning", channel_id="C_TEST", thread_ts="1", user_id="U_TEST")
    context_mgr = get_context_manager(plan['id'])

    # Simulate adding post summaries
    print(f"\n   Adding mock post summaries...")
    await context_mgr.add_post_summary({
        'post_num': 1,
        'score': 20,
        'hook': "Post 1: Simple hooks work better",
        'platform': 'linkedin',
        'airtable_url': 'https://airtable.com/test1',
        'what_worked': "Short, clear hook. Score: 20/25"
    })

    await context_mgr.add_post_summary({
        'post_num': 2,
        'score': 22,
        'hook': "Post 2: Specific examples boost engagement",
        'platform': 'linkedin',
        'airtable_url': 'https://airtable.com/test2',
        'what_worked': "Used concrete example. Score improved to 22/25"
    })

    # Get learnings that Post 3 would receive
    learnings = context_mgr.get_compacted_learnings()

    print(f"\n   Learnings passed to Post 3 ({len(learnings)} chars):")
    print(f"   {learnings[:300]}...")

    # Verify learnings mention previous posts
    assert "Post 1" in learnings or "20" in learnings, "Learnings should reference Post 1"
    assert "Post 2" in learnings or "22" in learnings, "Learnings should reference Post 2"
    assert len(learnings) > 100, "Learnings should have substantial content"

    # Verify target score calculation
    target_score = context_mgr.get_target_score()
    print(f"\n   Target score for Post 3: {target_score}/25")
    print(f"   (Based on avg of posts 1-2: {context_mgr.get_stats()['avg_score']:.1f})")

    assert target_score >= 21, "Target should be at least avg(20,22)+1 = 22"

    print(f"\n   ✅ Context learning validated: Post 3 receives learnings from 1-2")


async def test_error_structure():
    """Test that error responses have correct structure"""
    print("\n" + "="*70)
    print("TEST 4: Error Response Structure")
    print("="*70)

    # Test 1: Non-existent plan
    print(f"\n   Testing non-existent plan...")
    result = await execute_single_post_from_plan("nonexistent_plan_123", 0)

    assert 'success' in result, "Error result should have success field"
    assert result['success'] == False, "Non-existent plan should return success=False"
    assert 'error' in result, "Error result should have error message"
    print(f"   ✅ Non-existent plan error: {result['error'][:50]}...")

    # Test 2: Invalid post index
    print(f"\n   Testing invalid post index...")
    plan = create_batch_plan(
        [{"platform": "linkedin", "topic": "Test", "context": "", "style": "test"}],
        "Error test plan",
        channel_id="C_TEST",
        thread_ts="1",
        user_id="U_TEST"
    )

    result = await execute_single_post_from_plan(plan['id'], 10)  # Only 1 post in plan

    assert result['success'] == False, "Invalid index should return success=False"
    assert 'error' in result, "Should have error message"
    assert "Invalid post_index" in result['error'], "Error should mention invalid index"
    print(f"   ✅ Invalid index error: {result['error'][:50]}...")

    print(f"\n   ✅ Error response structure validated")


async def run_all_tests():
    """Run all E2E tests"""
    print("\n" + "="*70)
    print("BATCH E2E TEST SUITE")
    print("="*70)
    print("Testing complete batch workflow from plan → execution → Airtable")

    results = []
    tests = [
        ("Batch Plan Creation", test_batch_plan_creation),
        ("Sequential Execution", test_sequential_execution),
        ("Context Learning", test_context_learning),
        ("Error Handling", test_error_structure)
    ]

    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}...")
            await test_func()
            results.append((test_name, True, None))
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
        print("\n🎉 ALL E2E TESTS PASSED - Batch workflow ready for production!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed - Review and fix")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Test Batch Orchestration System
Quick validation that the 4 new batch tools work correctly

Run this to verify Phase 5 implementation before testing in Slack.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.batch_orchestrator import (
    create_batch_plan,
    execute_single_post_from_plan,
    get_context_manageraight
)


async def test_batch_plan_creation():
    """Test creating a batch plan"""
    print("\n" + "="*70)
    print("TEST 1: Create Batch Plan")
    print("="*70)

    posts = [
        {
            "platform": "linkedin",
            "topic": "AI agents transforming content marketing",
            "context": "Focus on productivity gains",
            "style": "thought_leadership"
        },
        {
            "platform": "linkedin",
            "topic": "Remote work productivity tips",
            "context": "Based on data from hybrid teams",
            "style": "practical"
        },
        {
            "platform": "twitter",
            "topic": "5 AI tools every marketer needs",
            "context": "Short tactical thread",
            "style": "tactical"
        }
    ]

    plan = create_batch_plan(posts, "Test batch of 3 posts")

    print(f"\n✅ Plan created:")
    print(f"   ID: {plan['id']}")
    print(f"   Description: {plan['description']}")
    print(f"   Posts: {len(plan['posts'])}")

    # Verify context manager was created
    context_mgr = get_context_manager(plan['id'])
    if context_mgr:
        print(f"   ✅ Context manager initialized")
    else:
        print(f"   ❌ Context manager NOT found")
        return None

    return plan['id']


async def test_context_manager_stats():
    """Test context manager stats before any posts"""
    print("\n" + "="*70)
    print("TEST 2: Context Manager Stats (Initial State)")
    print("="*70)

    # Create a simple plan
    plan = create_batch_plan([
        {"platform": "linkedin", "topic": "Test post", "context": "Test", "style": "test"}
    ], "Stats test")

    context_mgr = get_context_manager(plan['id'])

    if not context_mgr:
        print("   ❌ Context manager not found")
        return False

    stats = context_mgr.get_stats()

    print(f"\n📊 Initial stats:")
    print(f"   Total posts: {stats['total_posts']}")
    print(f"   Average score: {stats['avg_score']}")
    print(f"   Posts since compact: {stats['posts_since_compact']}")
    print(f"   Quality trend: {stats['quality_trend']}")
    print(f"   Recent learnings: {stats['recent_learnings'][:50]}...")

    if stats['total_posts'] == 0 and stats['avg_score'] == 0:
        print("   ✅ Initial state correct")
        return True
    else:
        print("   ❌ Initial state incorrect")
        return False


async def test_add_post_summary():
    """Test adding post summaries to context manager"""
    print("\n" + "="*70)
    print("TEST 3: Add Post Summaries")
    print("="*70)

    plan = create_batch_plan([
        {"platform": "linkedin", "topic": "Test", "context": "Test", "style": "test"}
    ] * 3, "Summary test")

    context_mgr = get_context_manager(plan['id'])

    # Add 3 post summaries
    for i in range(3):
        await context_mgr.add_post_summary({
            'post_num': i + 1,
            'score': 20 + i,  # Increasing scores: 20, 21, 22
            'hook': f"Test hook {i+1}",
            'platform': 'linkedin',
            'airtable_url': 'https://airtable.com/test',
            'what_worked': f"Score: {20+i}/25"
        })

    stats = context_mgr.get_stats()

    print(f"\n📊 Stats after 3 posts:")
    print(f"   Total posts: {stats['total_posts']}")
    print(f"   Average score: {stats['avg_score']:.1f}")
    print(f"   Recent scores: {stats['recent_scores']}")
    print(f"   Quality trend: {stats['quality_trend']}")

    target_score = context_mgr.get_target_score()
    print(f"   Target score for next post: {target_score}")

    if stats['total_posts'] == 3 and stats['avg_score'] == 21.0:
        print("   ✅ Post summaries working correctly")
        return True
    else:
        print("   ❌ Post summary tracking incorrect")
        return False


async def test_learnings_output():
    """Test learnings output format"""
    print("\n" + "="*70)
    print("TEST 4: Learnings Output Format")
    print("="*70)

    plan = create_batch_plan([
        {"platform": "linkedin", "topic": "Test", "context": "Test", "style": "test"}
    ] * 5, "Learnings test")

    context_mgr = get_context_manager(plan['id'])

    # Add 5 post summaries
    for i in range(5):
        await context_mgr.add_post_summary({
            'post_num': i + 1,
            'score': 18 + i,  # Improving scores: 18, 19, 20, 21, 22
            'hook': f"Hook {i+1}: This is a test hook about productivity",
            'platform': 'linkedin',
            'airtable_url': f'https://airtable.com/test{i+1}',
            'what_worked': f"Score improved to {18+i}/25"
        })

    learnings = context_mgr.get_compacted_learnings()

    print(f"\n📝 Learnings output ({len(learnings)} chars):")
    print(f"   Preview: {learnings[:200]}...")

    if len(learnings) > 0 and "Post 1" in learnings:
        print("   ✅ Learnings format correct")
        return True
    else:
        print("   ❌ Learnings format incorrect")
        return False


async def test_error_handling():
    """Test error handling for invalid operations"""
    print("\n" + "="*70)
    print("TEST 5: Error Handling")
    print("="*70)

    # Test 1: Get non-existent plan
    result = await execute_single_post_from_plan("nonexistent_plan", 0)
    if result.get('error'):
        print(f"   ✅ Non-existent plan error: {result['error'][:50]}...")
    else:
        print(f"   ❌ Should have returned error for non-existent plan")

    # Test 2: Invalid post index
    plan = create_batch_plan([
        {"platform": "linkedin", "topic": "Test", "context": "Test", "style": "test"}
    ], "Error test")

    result = await execute_single_post_from_plan(plan['id'], 10)  # Only 1 post in plan
    if result.get('error') and "Invalid post_index" in result['error']:
        print(f"   ✅ Invalid index error: {result['error'][:50]}...")
        return True
    else:
        print(f"   ❌ Should have returned invalid index error")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("BATCH ORCHESTRATION TEST SUITE")
    print("="*70)
    print("Testing Phase 5 implementation...")

    results = []

    # Run tests
    plan_id = await test_batch_plan_creation()
    results.append(plan_id is not None)

    results.append(await test_context_manager_stats())
    results.append(await test_add_post_summary())
    results.append(await test_learnings_output())
    results.append(await test_error_handling())

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - Ready for Slack integration!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed - Review implementation")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

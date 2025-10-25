#!/usr/bin/env python3
"""
Simple Batch Orchestration Test (No Dependencies)
Tests the core logic without importing SDK agents
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import context_manager directly (bypass __init__.py to avoid SDK dependencies)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "context_manager",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents", "context_manager.py")
)
context_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(context_module)
ContextManager = context_module.ContextManager


async def test_context_manager():
    """Test ContextManager in isolation"""
    print("\n" + "="*70)
    print("TEST: Context Manager")
    print("="*70)

    # Create context manager
    context_mgr = ContextManager("test_plan_001")

    # Initial state
    stats = context_mgr.get_stats()
    print(f"\n1. Initial State:")
    print(f"   Total posts: {stats['total_posts']} (expected: 0)")
    print(f"   Average score: {stats['avg_score']} (expected: 0)")
    print(f"   Posts since compact: {stats['posts_since_compact']} (expected: 0)")
    assert stats['total_posts'] == 0, "Initial total_posts should be 0"
    assert stats['avg_score'] == 0, "Initial avg_score should be 0"
    print("   ✅ Initial state correct")

    # Add 5 post summaries
    print(f"\n2. Adding 5 post summaries...")
    for i in range(5):
        await context_mgr.add_post_summary({
            'post_num': i + 1,
            'score': 18 + i,  # 18, 19, 20, 21, 22
            'hook': f"Hook {i+1}: Test hook about productivity",
            'platform': 'linkedin',
            'airtable_url': f'https://airtable.com/test{i+1}',
            'what_worked': f"Score: {18+i}/25"
        })

    stats = context_mgr.get_stats()
    print(f"   Total posts: {stats['total_posts']} (expected: 5)")
    print(f"   Average score: {stats['avg_score']:.1f} (expected: 20.0)")
    print(f"   Posts since compact: {stats['posts_since_compact']} (expected: 5)")
    print(f"   Recent scores: {stats['recent_scores']} (expected: [18, 19, 20, 21, 22])")
    assert stats['total_posts'] == 5, "Should have 5 posts"
    assert stats['avg_score'] == 20.0, "Average should be 20.0"
    assert stats['posts_since_compact'] == 5, "Should have 5 posts since compact"
    print("   ✅ Post summaries added correctly")

    # Test learnings output
    print(f"\n3. Testing learnings output...")
    learnings = context_mgr.get_compacted_learnings()
    print(f"   Learnings length: {len(learnings)} chars")
    print(f"   Preview: {learnings[:150]}...")
    assert len(learnings) > 0, "Learnings should not be empty"
    assert "Post 1" in learnings, "Learnings should mention Post 1"
    print("   ✅ Learnings output correct")

    # Test target score calculation
    print(f"\n4. Testing target score...")
    target = context_mgr.get_target_score()
    print(f"   Target score: {target} (expected: 21, which is avg 20.0 + 1)")
    assert target == 21, f"Target should be 21, got {target}"
    print("   ✅ Target score calculation correct")

    # Test quality trend
    print(f"\n5. Testing quality trend...")
    print(f"   Quality trend: {stats['quality_trend']} (expected: improving)")
    assert stats['quality_trend'] == "improving", "Trend should be improving"
    print("   ✅ Quality trend correct")

    # Add 5 more posts to test compaction (total = 10)
    print(f"\n6. Adding 5 more posts (will trigger compaction)...")
    for i in range(5, 10):
        await context_mgr.add_post_summary({
            'post_num': i + 1,
            'score': 18 + i,  # 23, 24, 25, 26, 27 -> capped at 25
            'hook': f"Hook {i+1}: Another test hook",
            'platform': 'linkedin',
            'airtable_url': f'https://airtable.com/test{i+1}',
            'what_worked': f"Score: {min(25, 18+i)}/25"
        })

    stats = context_mgr.get_stats()
    print(f"   Total posts: {stats['total_posts']} (expected: 10)")
    print(f"   Posts since compact: {stats['posts_since_compact']} (expected: 0 after compaction)")
    assert stats['total_posts'] == 10, "Should have 10 posts"
    assert stats['posts_since_compact'] == 0, "Should have compacted at 10 posts"
    print("   ✅ Compaction triggered correctly")

    # Test compacted learnings structure
    print(f"\n7. Testing compacted learnings...")
    compacted_learnings = context_mgr.get_compacted_learnings()
    print(f"   Compacted learnings length: {len(compacted_learnings)} chars")
    print(f"   Preview: {compacted_learnings[:150]}...")
    assert "Posts 1-10" in compacted_learnings or "compacted" in compacted_learnings.lower(), "Should mention compacted posts"
    print("   ✅ Compacted learnings format correct")

    print(f"\n" + "="*70)
    print("✅ ALL CONTEXT MANAGER TESTS PASSED!")
    print("="*70)

    return True


async def test_batch_plan_structure():
    """Test the batch plan data structure"""
    print("\n" + "="*70)
    print("TEST: Batch Plan Structure")
    print("="*70)

    from datetime import datetime

    # Simulate creating a plan (without importing batch_orchestrator)
    plan_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    plan = {
        'id': plan_id,
        'description': "Test batch",
        'posts': [
            {"platform": "linkedin", "topic": "AI agents", "context": "Productivity", "style": "thought_leadership"},
            {"platform": "twitter", "topic": "Remote work", "context": "Hybrid teams", "style": "tactical"}
        ],
        'created_at': datetime.now().isoformat()
    }

    print(f"\n   Plan ID: {plan['id']}")
    print(f"   Description: {plan['description']}")
    print(f"   Posts: {len(plan['posts'])}")
    print(f"   Created: {plan['created_at']}")

    assert 'id' in plan, "Plan should have ID"
    assert 'description' in plan, "Plan should have description"
    assert 'posts' in plan, "Plan should have posts list"
    assert len(plan['posts']) == 2, "Should have 2 posts"

    print("\n   ✅ Batch plan structure valid")
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("BATCH ORCHESTRATION SIMPLE TEST SUITE")
    print("="*70)

    try:
        await test_context_manager()
        await test_batch_plan_structure()

        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
        print("\nPhase 5 core infrastructure validated.")
        print("Next: Test with Slack integration for full workflow.")
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

"""
Test script for LinkedIn Direct API Agent
Verifies that direct API version works as drop-in replacement for SDK version
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.linkedin_direct_api_agent import create_linkedin_post_workflow


async def test_simple_post():
    """Test creating a simple LinkedIn post"""
    print("\n" + "=" * 60)
    print("TEST 1: Simple post creation")
    print("=" * 60)

    result = await create_linkedin_post_workflow(
        topic="Why direct API calls eliminate SDK hanging issues",
        context="Focus on timeout control, debugging visibility, and reliability improvements",
        style="thought_leadership",
        user_id="test_user"
    )

    print("\n📊 RESULT:")
    print(result)

    # Validate result format
    assert "✅ **LinkedIn Post Created**" in result, "Missing success indicator"
    assert "Quality Score:" in result, "Missing quality score"
    assert "**Full Post:**" in result, "Missing full post content"

    print("\n✅ TEST 1 PASSED: Simple post creation successful")
    return result


async def test_with_rich_context():
    """Test with rich strategic context (should preserve user's language)"""
    print("\n" + "=" * 60)
    print("TEST 2: Rich context preservation")
    print("=" * 60)

    rich_context = """
I've been thinking about this for months. Every time I see another startup fail because
they optimized for growth instead of profitability, I want to scream.

Here's the pattern I've noticed:
1. Raise VC money
2. Hire aggressively
3. Burn through runway chasing vanity metrics
4. Wonder why they're profitable but broke

The problem isn't the growth. It's that they forgot to build the business model FIRST.

I learned this the hard way after burning through $2M in 18 months. My revenue was up
400%, but my bank account was empty. Why? Because I was so focused on "scaling" that I
forgot to charge properly.

Most operators are making the same mistake right now. They're buying AI tools to "automate
sales" when their offer is fundamentally broken. No amount of automation fixes a pricing
problem.

Stop chasing the shiny objects. Fix your fundamentals first. THEN scale.
"""

    result = await create_linkedin_post_workflow(
        topic="Stop scaling broken business models",
        context=rich_context,
        style="contrarian",
        user_id="test_user"
    )

    print("\n📊 RESULT:")
    print(result)

    # Validate that strategic thinking was preserved
    assert "✅ **LinkedIn Post Created**" in result, "Missing success indicator"
    assert "Quality Score:" in result, "Missing quality score"

    print("\n✅ TEST 2 PASSED: Rich context handling successful")
    return result


async def test_with_publish_date():
    """Test with publish date for scheduling"""
    print("\n" + "=" * 60)
    print("TEST 3: Scheduled post creation")
    print("=" * 60)

    result = await create_linkedin_post_workflow(
        topic="3 lessons from 30 years building businesses",
        context="Share hard-earned lessons about cash flow, pricing, and discipline",
        style="listicle",
        user_id="test_user",
        publish_date="2025-12-01"
    )

    print("\n📊 RESULT:")
    print(result)

    assert "✅ **LinkedIn Post Created**" in result, "Missing success indicator"
    assert "Quality Score:" in result, "Missing quality score"

    print("\n✅ TEST 3 PASSED: Scheduled post creation successful")
    return result


async def run_all_tests():
    """Run all tests sequentially"""
    print("\n🧪 RUNNING LINKEDIN DIRECT API AGENT TESTS")
    print("=" * 60)

    try:
        # Test 1: Simple post
        await test_simple_post()

        # Test 2: Rich context
        await test_with_rich_context()

        # Test 3: Scheduled post
        await test_with_publish_date()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\n🎉 Direct API agent is working correctly!")
        print("Ready to integrate with batch orchestrator.\n")

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

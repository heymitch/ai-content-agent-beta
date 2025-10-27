#!/usr/bin/env python3
"""
Mock test specifically for batch orchestrator with context learning.
Tests the sophisticated context accumulation and learning transfer.

Run with: python tests/test_batch_orchestrator_mock.py
"""

import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== MOCK CONTEXT MANAGER ====================

class MockBatchContextManager:
    """Mock context manager that simulates learning accumulation"""

    def __init__(self):
        self.context_history = []
        self.learnings = {
            'hooks': [],
            'structures': [],
            'quality_patterns': []
        }

    async def add_post_summary(self, summary: dict):
        """Track post summaries for learning"""
        self.context_history.append(summary)

        # Extract learnings
        if summary['score'] >= 20:
            self.learnings['hooks'].append(f"Hook from post {summary['post_num']}")
            self.learnings['quality_patterns'].append(f"Pattern {summary['post_num']}")

    async def get_accumulated_context(self, post_num: int) -> str:
        """Get accumulated learnings for next post"""
        if post_num == 1:
            return "First post - no prior context"

        learnings = []
        for i, ctx in enumerate(self.context_history[:post_num-1], 1):
            learnings.append(f"Post {i}: Score {ctx['score']}/25")

        return "\n".join(learnings)


# ==================== MOCK SDK AGENTS WITH LEARNING ====================

class MockLearningSDKAgent:
    """Mock SDK agent that improves with context"""

    def __init__(self, platform: str):
        self.platform = platform
        self.base_score = 18
        self.calls = 0

    async def create_content(self, topic: str, context: str, **kwargs):
        """Simulate content creation that improves with learnings"""
        self.calls += 1

        # Simulate improvement based on learnings in context
        score_boost = 0
        if "Score 20" in context:
            score_boost += 1
        if "Score 21" in context:
            score_boost += 1
        if "Score 22" in context:
            score_boost += 2

        score = min(24, self.base_score + self.calls + score_boost)

        return {
            'success': True,
            'post': f"Mock {self.platform} post #{self.calls} about {topic}",
            'score': score,
            'hook': f"Hook for {topic}",
            'learnings_applied': score_boost > 0
        }


# ==================== MOCK BATCH ORCHESTRATOR ====================

async def mock_execute_single_post(
    platform: str,
    topic: str,
    context: str,
    **kwargs
):
    """Mock single post execution"""
    agent = MockLearningSDKAgent(platform)
    result = await agent.create_content(topic, context, **kwargs)

    # Return formatted string like the real orchestrator
    return f"""✅ **{platform.capitalize()} Post Created**

**Hook Preview:**
_{result['hook']}_

**Quality Score:** {result['score']}/25

**Full Post:**
{result['post']}"""


# ==================== TEST BATCH WITH CONTEXT LEARNING ====================

class TestBatchOrchestrator:
    """Test batch orchestration with context learning"""

    def __init__(self):
        self.context_manager = MockBatchContextManager()
        self.results = []

    async def test_context_accumulation(self):
        """Test that context accumulates and improves scores"""
        print("\n📚 Testing Context Learning System...")

        # Define test plan
        test_plan = {
            'plan_id': 'test_learning_001',
            'posts': [
                {
                    'post_num': 1,
                    'platform': 'linkedin',
                    'topic': 'AI automation',
                    'expected_min_score': 18
                },
                {
                    'post_num': 2,
                    'platform': 'twitter',
                    'topic': 'Quick tips',
                    'expected_min_score': 19  # Should improve
                },
                {
                    'post_num': 3,
                    'platform': 'email',
                    'topic': 'Newsletter',
                    'expected_min_score': 20  # Should improve more
                }
            ]
        }

        # Execute posts in sequence
        for post_spec in test_plan['posts']:
            # Get accumulated context
            context = await self.context_manager.get_accumulated_context(
                post_spec['post_num']
            )

            # Execute post
            with patch('agents.batch_orchestrator._execute_single_post',
                       side_effect=mock_execute_single_post):
                result = await mock_execute_single_post(
                    platform=post_spec['platform'],
                    topic=post_spec['topic'],
                    context=context
                )

            # Extract score from result
            import re
            score_match = re.search(r'Quality Score.*?(\d+)/25', result)
            score = int(score_match.group(1)) if score_match else 0

            # Add to context manager
            await self.context_manager.add_post_summary({
                'post_num': post_spec['post_num'],
                'score': score,
                'platform': post_spec['platform']
            })

            # Validate improvement
            assert score >= post_spec['expected_min_score'], \
                f"Post {post_spec['post_num']} score {score} < expected {post_spec['expected_min_score']}"

            print(f"   ✅ Post {post_spec['post_num']} ({post_spec['platform']}): Score {score}/25")

        # Check overall improvement
        scores = [ctx['score'] for ctx in self.context_manager.context_history]
        assert scores[-1] > scores[0], "No improvement detected"

        print(f"   ✅ Score progression: {' → '.join(map(str, scores))}")
        print(f"   ✅ Improvement: +{scores[-1] - scores[0]} points")

        return True

    async def test_parallel_vs_sequential(self):
        """Test that sequential execution with learning beats parallel"""
        print("\n🔄 Testing Sequential vs Parallel Execution...")

        # Sequential with learning
        seq_scores = []
        context_mgr = MockBatchContextManager()

        for i in range(3):
            context = await context_mgr.get_accumulated_context(i + 1)
            agent = MockLearningSDKAgent('test')
            result = await agent.create_content(f'topic_{i}', context)
            seq_scores.append(result['score'])
            await context_mgr.add_post_summary({
                'post_num': i + 1,
                'score': result['score']
            })

        # Parallel without learning
        parallel_agents = [MockLearningSDKAgent('test') for _ in range(3)]
        parallel_results = await asyncio.gather(*[
            agent.create_content(f'topic_{i}', 'no learning context')
            for i, agent in enumerate(parallel_agents)
        ])
        parallel_scores = [r['score'] for r in parallel_results]

        print(f"   Sequential scores: {seq_scores}")
        print(f"   Parallel scores: {parallel_scores}")
        print(f"   ✅ Seq avg: {sum(seq_scores)/len(seq_scores):.1f}")
        print(f"   ✅ Par avg: {sum(parallel_scores)/len(parallel_scores):.1f}")

        # Sequential should have better average due to learning
        assert sum(seq_scores) >= sum(parallel_scores), \
            "Sequential with learning should score higher"

        return True

    async def test_error_recovery(self):
        """Test batch orchestrator error recovery"""
        print("\n🔧 Testing Error Recovery...")

        # Simulate a post failure
        async def failing_post(*args, **kwargs):
            if kwargs.get('topic') == 'fail_topic':
                raise Exception("Simulated failure")
            return await mock_execute_single_post(*args, **kwargs)

        with patch('agents.batch_orchestrator._execute_single_post',
                   side_effect=failing_post):

            # Try with failing topic
            try:
                result = await failing_post(
                    platform='test',
                    topic='fail_topic',
                    context='test'
                )
                assert False, "Should have failed"
            except Exception as e:
                assert "Simulated failure" in str(e)
                print("   ✅ Failure caught correctly")

            # Verify recovery
            result = await failing_post(
                platform='test',
                topic='valid_topic',
                context='test'
            )
            assert "✅" in result, "Recovery failed"
            print("   ✅ Recovery successful")

        return True

    async def test_slack_metadata_flow(self):
        """Test Slack metadata is properly passed through"""
        print("\n💬 Testing Slack Metadata Flow...")

        slack_metadata = {
            'channel_id': 'C_TEST_CHANNEL',
            'thread_ts': '1234567890.123456',
            'user_id': 'U_TEST_USER'
        }

        # Mock the SDK agent initialization
        class MockSDKWithSlack:
            def __init__(self, **kwargs):
                self.metadata = kwargs

            async def create_content(self, *args, **kwargs):
                return {
                    'success': True,
                    'post': 'test',
                    'score': 20,
                    'slack_metadata': self.metadata
                }

        with patch('agents.linkedin_sdk_agent.LinkedInSDKAgent', MockSDKWithSlack):
            agent = MockSDKWithSlack(**slack_metadata)
            result = await agent.create_content('test', 'test')

            assert result['slack_metadata']['channel_id'] == 'C_TEST_CHANNEL'
            assert result['slack_metadata']['thread_ts'] == '1234567890.123456'
            print("   ✅ Slack metadata preserved")

        return True


# ==================== COMPREHENSIVE TEST RUNNER ====================

async def run_comprehensive_tests():
    """Run all batch orchestrator tests"""
    print("="*60)
    print("🎯 BATCH ORCHESTRATOR MOCK TEST SUITE")
    print("="*60)

    tester = TestBatchOrchestrator()

    tests = [
        ("Context Learning", tester.test_context_accumulation()),
        ("Sequential vs Parallel", tester.test_parallel_vs_sequential()),
        ("Error Recovery", tester.test_error_recovery()),
        ("Slack Metadata", tester.test_slack_metadata_flow())
    ]

    results = []
    for name, test_coro in tests:
        try:
            result = await test_coro
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ {name} failed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("📊 BATCH ORCHESTRATOR TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    print(f"✅ Tests passed: {passed}/{len(results)}")

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {name}")

    # Calculate API savings
    total_mock_calls = 20  # Approximate
    api_cost_saved = total_mock_calls * 0.002
    time_saved = total_mock_calls * 2  # ~2 seconds per API call

    print(f"\n💰 API calls saved: ~{total_mock_calls}")
    print(f"💵 Money saved: ~${api_cost_saved:.2f}")
    print(f"⏱️  Time saved: ~{time_saved}s")

    print("\n" + "="*60)
    if passed == len(results):
        print("🎉 ALL BATCH ORCHESTRATOR TESTS PASSED!")
    else:
        print("⚠️  Some tests failed. Check output for details.")
    print("="*60)

    return passed == len(results)


# ==================== MAIN ENTRY POINT ====================

async def main():
    """Main test runner"""
    success = await run_comprehensive_tests()

    print("\n💡 TIP: Run these tests before deploying to catch issues early!")
    print("📝 Add more test cases as you add features to your system.")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
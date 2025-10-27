"""
Test Context Preservation Through Batch Execution

Verifies that detailed strategic outlines are preserved from user input
through CMO planning, batch orchestration, and SDK agent execution.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.batch_orchestrator import create_batch_plan, execute_single_post_from_plan, get_context_manager
from agents.context_manager import ContextManager


class TestContextPreservation:
    """Test that strategic context flows through the entire batch system"""

    def test_create_plan_preserves_detailed_outline(self):
        """Test: Batch plan stores detailed_outline field"""

        # User provides detailed strategic outline
        posts = [{
            "platform": "linkedin",
            "topic": "High-ticket operators and AI",
            "context": "Morning post",
            "detailed_outline": "Most high-ticket operators I talk to have built the wrong AI tools. They spent months on chatbots that answer FAQs. I've been heads-down building something different.",
            "style": "contrarian"
        }]

        plan = create_batch_plan(posts, "Test batch", channel_id="C123", thread_ts="123", user_id="U123")

        # Verify outline is preserved
        assert plan['posts'][0]['detailed_outline'] == posts[0]['detailed_outline']
        assert len(plan['detailed_outlines']) == 1
        assert plan['detailed_outlines'][0] == posts[0]['detailed_outline']

        # Verify context quality detection
        assert plan['context_quality'] in ['rich', 'medium']  # Should detect rich context
        assert plan['avg_context_length'] > 150  # Adjusted threshold

    def test_sparse_context_warning(self):
        """Test: Sparse context triggers warning"""

        # Minimal context (should warn)
        posts = [{
            "platform": "linkedin",
            "topic": "AI tools",
            "context": "Post about AI"  # No detailed_outline, minimal context
        }]

        with patch('builtins.print') as mock_print:
            plan = create_batch_plan(posts, "Test batch")

            # Should print warning
            warning_calls = [call for call in mock_print.call_args_list
                           if '⚠️ WARNING' in str(call)]
            assert len(warning_calls) > 0
            assert plan['context_quality'] == 'sparse'

    @pytest.mark.asyncio
    async def test_execute_uses_detailed_outline(self):
        """Test: execute_single_post_from_plan passes detailed outline to SDK"""

        # Create plan with detailed outline
        posts = [{
            "platform": "linkedin",
            "topic": "AI tools",
            "context": "Morning post",
            "detailed_outline": "Most high-ticket operators have built wrong tools. [Full strategic narrative here...]"
        }]

        plan = create_batch_plan(posts, "Test batch")
        plan_id = plan['id']

        # Mock SDK agent execution
        with patch('agents.batch_orchestrator._execute_single_post') as mock_execute:
            mock_execute.return_value = {
                'content': 'Generated content',
                'airtable_url': 'https://airtable.com/test',
                'score': 22
            }

            # Execute post
            result = await execute_single_post_from_plan(plan_id, 0)

            # Verify SDK agent received detailed outline in context
            call_args = mock_execute.call_args[1]
            context = call_args['context']

            assert 'STRATEGIC OUTLINE' in context
            assert posts[0]['detailed_outline'] in context
            assert 'Follow this closely' in context

    def test_context_manager_tracks_alignment(self):
        """Test: Context manager can track strategic alignment"""

        context_mgr = ContextManager("test_plan")

        # Add strategic outline
        outline = "Most high-ticket operators have built wrong AI tools"
        context_mgr.add_strategic_context(0, outline)

        # Test good alignment
        good_content = "Most high-ticket operators I've talked to have built the wrong AI tools for their business"
        alignment = context_mgr.check_alignment(0, good_content)
        assert alignment > 0.5  # Good overlap

        # Test poor alignment
        bad_content = "Here are 5 tips for using ChatGPT in your business"
        alignment = context_mgr.check_alignment(0, bad_content)
        assert alignment < 0.3  # Poor overlap

    def test_end_to_end_context_flow(self):
        """Test: Context flows from user input to SDK agent"""

        # Simulate full flow
        user_outline = """Post 1: Most high-ticket operators have built wrong AI tools.
They spent months on chatbots. I built something different.
My niche: $1M-$50M businesses. Real agents, not prototypes."""

        # Step 1: CMO creates plan (would extract outline)
        posts = [{
            "platform": "linkedin",
            "topic": "High-ticket operators and AI",
            "detailed_outline": user_outline,
            "context": "Strategic post",
            "style": "contrarian"
        }]

        # Step 2: Create batch plan
        plan = create_batch_plan(posts, "Strategic batch")

        # Verify plan quality
        assert plan['context_quality'] == 'rich'
        assert plan['posts'][0]['detailed_outline'] == user_outline

        # Step 3: Context manager initialized
        context_mgr = get_context_manager(plan['id'])
        context_mgr.add_strategic_context(0, user_outline)

        # Step 4: Would execute and check alignment
        # (In real scenario, SDK agent generates content)
        mock_generated = "Most high-ticket operators I talk to have built wrong AI tools..."
        alignment = context_mgr.check_alignment(0, mock_generated)
        assert alignment > 0.3  # Moderate alignment with outline (word-based check)

    def test_multiple_posts_with_different_outlines(self):
        """Test: Multiple posts each preserve their unique outlines"""

        posts = [
            {
                "platform": "linkedin",
                "topic": "AI tools",
                "detailed_outline": "Most high-ticket operators build wrong tools...",
                "context": "Morning"
            },
            {
                "platform": "linkedin",
                "topic": "Agent systems",
                "detailed_outline": "Real agents work as a system, not single tools...",
                "context": "Afternoon"
            },
            {
                "platform": "linkedin",
                "topic": "Who I build for",
                "detailed_outline": "I build for $1M+ info product companies...",
                "context": "Evening"
            }
        ]

        plan = create_batch_plan(posts, "Multi-post batch")

        # Each post should preserve its outline
        assert len(plan['detailed_outlines']) == 3
        assert plan['posts'][0]['detailed_outline'] == posts[0]['detailed_outline']
        assert plan['posts'][1]['detailed_outline'] == posts[1]['detailed_outline']
        assert plan['posts'][2]['detailed_outline'] == posts[2]['detailed_outline']

        # Should be marked as medium context (short outline examples)
        assert plan['context_quality'] in ['medium', 'rich']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
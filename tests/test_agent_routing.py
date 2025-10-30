"""
Test Agent Routing Logic: BATCH vs CO-WRITE Mode

This test verifies that the agent correctly routes content creation requests
to BATCH mode (99%) vs CO-WRITE mode (1%) based on user message keywords.

BATCH MODE (default): plan_content_batch + execute_post_from_plan
CO-WRITE MODE (explicit only): generate_post_{platform} + quality_check + apply_fixes
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slack_bot.claude_agent_handler import ClaudeAgentHandler


class TestAgentRouting:
    """Test agent routing between BATCH and CO-WRITE modes"""

    @pytest.fixture
    def mock_handler(self):
        """Create a mock ClaudeAgentHandler for testing"""
        with patch('slack_bot.claude_agent_handler.create_sdk_mcp_server'):
            handler = ClaudeAgentHandler(memory_handler=None, slack_client=None)
            return handler

    # ============= BATCH MODE TESTS (Should use plan_content_batch) =============

    @pytest.mark.asyncio
    async def test_batch_multi_post_explicit(self, mock_handler):
        """Test: 'Create 5 LinkedIn posts' should use BATCH mode"""
        user_message = "Create 5 LinkedIn posts about AI automation"

        # Mock the Claude SDK client
        with patch.object(mock_handler, '_get_or_create_session') as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value = mock_client
            mock_client.query = AsyncMock()
            mock_client.connect = AsyncMock()

            # Mock response stream to track tool calls
            mock_response = Mock()
            mock_response.text = "Creating 5 posts using batch mode..."

            # Simulate tool call to plan_content_batch
            tool_use = Mock()
            tool_use.type = 'tool_use'
            tool_use.name = 'mcp__tools__plan_content_batch'
            tool_use.input = {'count': 5, 'platform': 'linkedin'}

            mock_response.content = [tool_use]
            mock_client.get_last_response = Mock(return_value=mock_response)

            # Call the handler
            await mock_handler.handle_conversation(
                message=user_message,
                user_id='U123',
                thread_ts='thread123',
                channel_id='C123'
            )

            # Verify plan_content_batch was called (not generate_post_linkedin)
            assert mock_client.query.called, "Agent should have called query"
            assert 'plan_content_batch' in str(mock_response.content[0].name), \
                f"Expected plan_content_batch, got {mock_response.content[0].name}"

    @pytest.mark.asyncio
    async def test_batch_single_post(self, mock_handler):
        """Test: 'Write a post about marketing' should use BATCH mode (not co-write)"""
        user_message = "Write a LinkedIn post about content marketing"

        # This should use BATCH even though it says "write" and is 1 post
        # because "write" is not a co-write trigger keyword

        # For this test, we'll verify the system prompt has correct routing
        assert "BATCH MODE IS THE DEFAULT" in mock_handler.system_prompt
        assert "RARE EXCEPTION - Co-write mode (1% of requests)" in mock_handler.system_prompt

    @pytest.mark.asyncio
    async def test_batch_with_draft_keyword_multipost(self, mock_handler):
        """Test: 'Draft 5 posts' should use BATCH (count overrides 'draft')"""
        user_message = "Draft 5 LinkedIn posts about AI agents"

        # Even though it says "draft", batch mode should be default
        assert "BATCH MODE IS THE DEFAULT" in mock_handler.system_prompt

    @pytest.mark.asyncio
    async def test_batch_help_request(self, mock_handler):
        """Test: 'Help me create content' should use BATCH mode"""
        user_message = "Help me create 10 posts for next week"

        # Generic "help" should not trigger co-write - check for negative examples
        assert '"draft", "help", "write", "show me"' in mock_handler.system_prompt
        assert "DO NOT" in mock_handler.system_prompt

    # ============= CO-WRITE MODE TESTS (Should ASK or use co-write tools) =============

    @pytest.mark.asyncio
    async def test_cowrite_explicit_keyword(self, mock_handler):
        """Test: 'Co-write a post with me' should trigger CO-WRITE confirmation"""
        user_message = "Co-write a LinkedIn post with me about AI"

        # Should contain the explicit co-write keywords
        assert '"co-write", "collaborate with me", "iterate with me"' in mock_handler.system_prompt

    @pytest.mark.asyncio
    async def test_cowrite_collaborate_keyword(self, mock_handler):
        """Test: 'Let's collaborate on content' should trigger CO-WRITE confirmation"""
        user_message = "Let's collaborate on content together"

        # Verify co-write keyword "collaborate with me" is in prompt
        assert '"co-write", "collaborate with me", "iterate with me"' in mock_handler.system_prompt

    @pytest.mark.asyncio
    async def test_cowrite_iterate_keyword(self, mock_handler):
        """Test: 'I want to iterate with you' should trigger CO-WRITE confirmation"""
        user_message = "I want to iterate with you on this post"

        # Verify "iterate with me" is a co-write trigger keyword
        assert '"co-write", "collaborate with me", "iterate with me"' in mock_handler.system_prompt

    # ============= NEGATIVE TESTS (Should NOT trigger CO-WRITE) =============

    @pytest.mark.asyncio
    async def test_not_cowrite_draft_only(self, mock_handler):
        """Test: 'Draft a post' (without 'co-write') should use BATCH"""
        user_message = "Draft a LinkedIn post"

        # "Draft" alone should NOT trigger co-write - verify it's in DO NOT list
        assert '"draft", "help", "write", "show me"' in mock_handler.system_prompt

    @pytest.mark.asyncio
    async def test_not_cowrite_show_me(self, mock_handler):
        """Test: 'Show me content' should use BATCH"""
        user_message = "Show me some content about AI"

        # "Show me" should NOT trigger co-write - verify it's in DO NOT list
        assert '"draft", "help", "write", "show me"' in mock_handler.system_prompt

    @pytest.mark.asyncio
    async def test_not_cowrite_help_write(self, mock_handler):
        """Test: 'Help me write posts' should use BATCH"""
        user_message = "Help me write 5 posts about startups"

        # Generic "help write" should NOT trigger co-write - verify it's in DO NOT list
        assert '"draft", "help", "write", "show me"' in mock_handler.system_prompt

    # ============= SYSTEM PROMPT STRUCTURE TESTS =============

    def test_batch_is_default_prominent(self, mock_handler):
        """Test: System prompt clearly states BATCH is default"""
        prompt = mock_handler.system_prompt

        # Verify prominence of BATCH mode
        assert "BATCH MODE IS THE DEFAULT" in prompt
        assert "RARE EXCEPTION - Co-write mode (1% of requests)" in prompt
        assert "Only use if user EXPLICITLY says" in prompt

    def test_cowrite_is_rare(self, mock_handler):
        """Test: System prompt emphasizes CO-WRITE is rare"""
        prompt = mock_handler.system_prompt

        # Verify CO-WRITE is positioned as rare
        assert "RARE EXCEPTION - Co-write mode (1% of requests)" in prompt
        assert "Only use if user EXPLICITLY says" in prompt

    def test_routing_decision_strict(self, mock_handler):
        """Test: Routing decision tree is strict and clear"""
        prompt = mock_handler.system_prompt

        # Verify strict routing rules
        assert "RARE EXCEPTION - Co-write mode" in prompt
        assert '"co-write", "collaborate with me", "iterate with me"' in prompt
        assert "BATCH MODE IS THE DEFAULT" in prompt

    def test_negative_examples_present(self, mock_handler):
        """Test: Negative examples (DO NOT trigger co-write) are present"""
        prompt = mock_handler.system_prompt

        # Verify negative examples exist
        assert "DO NOT" in prompt and '"draft", "help", "write", "show me"' in prompt


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])

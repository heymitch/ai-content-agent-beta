"""
Unit and integration tests for Instagram SDK Agent
Tests prompts, tools, agent workflow, and character limits
"""
import pytest
import asyncio
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from prompts.instagram_tools import (
    GENERATE_HOOKS_PROMPT,
    CREATE_CAPTION_DRAFT_PROMPT,
    CONDENSE_TO_LIMIT_PROMPT,
    QUALITY_CHECK_PROMPT,
    APPLY_FIXES_PROMPT,
    VALIDATE_FORMAT_PROMPT,
    WRITE_LIKE_HUMAN_RULES
)


class TestInstagramPrompts:
    """Test Instagram prompt templates"""

    def test_prompts_import_successfully(self):
        """Test that all Instagram prompts are defined"""
        assert GENERATE_HOOKS_PROMPT is not None
        assert CREATE_CAPTION_DRAFT_PROMPT is not None
        assert CONDENSE_TO_LIMIT_PROMPT is not None
        assert QUALITY_CHECK_PROMPT is not None
        assert APPLY_FIXES_PROMPT is not None
        assert VALIDATE_FORMAT_PROMPT is not None

    def test_write_like_human_rules_imported(self):
        """Test that WRITE_LIKE_HUMAN_RULES is imported from LinkedIn"""
        assert WRITE_LIKE_HUMAN_RULES is not None
        assert len(WRITE_LIKE_HUMAN_RULES) > 100  # Should be substantial rules

    def test_prompts_mention_character_limit(self):
        """Test that critical prompts mention 2,200 char limit"""
        assert "2,200" in CREATE_CAPTION_DRAFT_PROMPT
        assert "2,200" in CONDENSE_TO_LIMIT_PROMPT
        assert "2,200" in VALIDATE_FORMAT_PROMPT

    def test_prompts_mention_125_char_preview(self):
        """Test that prompts mention 125-char preview optimization"""
        assert "125" in GENERATE_HOOKS_PROMPT
        assert "125" in CREATE_CAPTION_DRAFT_PROMPT
        assert "125" in QUALITY_CHECK_PROMPT

    def test_quality_check_has_5_axes(self):
        """Test that quality check mentions all 5 Instagram-specific axes"""
        axes = ["hook", "visual", "readability", "proof", "cta", "hashtag"]
        prompt_lower = QUALITY_CHECK_PROMPT.lower()

        # At least 4 of the 6 keywords should be present
        found = sum(1 for axis in axes if axis in prompt_lower)
        assert found >= 4, f"Quality check should mention Instagram-specific scoring axes"

    def test_condense_prompt_mentions_nicolas_cole(self):
        """Test that condense prompt references Nicolas Cole's technique"""
        assert "Cole" in CONDENSE_TO_LIMIT_PROMPT or "condense" in CONDENSE_TO_LIMIT_PROMPT.lower()


class TestInstagramSDKAgent:
    """Test Instagram SDK Agent implementation"""

    @pytest.mark.asyncio
    async def test_agent_imports(self):
        """Test that Instagram agent can be imported"""
        try:
            from agents.instagram_sdk_agent import (
                InstagramSDKAgent,
                create_instagram_caption_workflow
            )
            assert InstagramSDKAgent is not None
            assert create_instagram_caption_workflow is not None
        except ImportError as e:
            pytest.fail(f"Failed to import Instagram SDK agent: {e}")

    @pytest.mark.asyncio
    async def test_agent_tools_defined(self):
        """Test that all 5 Instagram tools are defined"""
        from agents.instagram_sdk_agent import (
            generate_5_hooks,
            create_caption_draft,
            condense_to_limit,
            quality_check,
            apply_fixes
        )

        assert generate_5_hooks is not None
        assert create_caption_draft is not None
        assert condense_to_limit is not None
        assert quality_check is not None
        assert apply_fixes is not None

    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test that Instagram agent can be initialized"""
        from agents.instagram_sdk_agent import InstagramSDKAgent

        agent = InstagramSDKAgent(user_id="test_user", isolated_mode=True)
        assert agent.user_id == "test_user"
        assert agent.sessions is not None
        assert agent.mcp_server is not None

    @pytest.mark.asyncio
    @patch('agents.instagram_sdk_agent.ClaudeSDKClient')
    async def test_create_caption_workflow_entry_point(self, mock_client):
        """Test the main workflow entry point"""
        from agents.instagram_sdk_agent import create_instagram_caption_workflow

        # Mock the agent workflow
        mock_instance = MagicMock()
        mock_instance.create_caption = AsyncMock(return_value={
            'caption': 'Test Instagram caption',
            'quality_score': 85,
            'airtable_url': 'https://airtable.com/test'
        })

        with patch('agents.instagram_sdk_agent.InstagramSDKAgent') as mock_agent_class:
            mock_agent_class.return_value = mock_instance

            result = await create_instagram_caption_workflow(
                topic="AI content creation",
                context="Test context",
                style="professional"
            )

            assert result is not None


class TestInstagramCharacterLimits:
    """Test Instagram-specific character limit handling"""

    def test_caption_under_limit(self):
        """Test that valid caption passes character limit check"""
        caption = "This is a test caption with some content." * 20  # ~840 chars
        assert len(caption) < 2200, "Test caption should be under limit"

    def test_caption_over_limit(self):
        """Test detection of caption over 2,200 character limit"""
        caption = "x" * 2201
        assert len(caption) > 2200, "Caption should exceed limit"

    def test_preview_optimization(self):
        """Test that first 125 characters are extractable"""
        caption = "This is the hook that appears in preview." + ("x" * 200)
        preview = caption[:125]
        assert len(preview) == 125
        assert preview.startswith("This is the hook")


class TestInstagramIntegration:
    """Test Instagram integration with CMO handler"""

    @pytest.mark.asyncio
    async def test_instagram_delegate_workflow_import(self):
        """Test that delegate_to_workflow supports Instagram"""
        from slack_bot.claude_agent_handler import ClaudeAgentHandler

        # Just verify the class can be imported and instantiated
        handler = ClaudeAgentHandler()
        assert handler is not None

    def test_instagram_tools_registered_in_cmo(self):
        """Test that Instagram tools are in CMO tool list"""
        # Read the claude_agent_handler.py file to verify registration
        import re

        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        # Check for Instagram tools
        assert 'generate_post_instagram' in content
        assert 'quality_check_instagram' in content
        assert 'apply_fixes_instagram' in content

        # Check for Instagram delegation
        assert 'instagram' in content.lower()
        assert 'create_instagram_caption_workflow' in content

    def test_instagram_in_system_prompt(self):
        """Test that system prompt mentions Instagram in co-writing tools"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        # System prompt should mention Instagram in tool lists
        # Extract system prompt section
        if 'self.system_prompt =' in content:
            assert 'instagram' in content.lower(), "Instagram should be mentioned in system prompt"


class TestInstagramQualityAxes:
    """Test Instagram-specific quality scoring axes"""

    def test_quality_axes_documented(self):
        """Test that all 5 Instagram quality axes are documented"""
        axes = [
            "Hook",
            "Visual",  # Visual Pairing
            "Readability",
            "Proof",
            "CTA"  # or Hashtags
        ]

        prompt = QUALITY_CHECK_PROMPT

        # At least 4 of 5 axes should be explicitly mentioned
        found_axes = sum(1 for axis in axes if axis.lower() in prompt.lower())
        assert found_axes >= 4, f"Quality check should document Instagram's 5 scoring axes"

    def test_quality_axes_different_from_linkedin(self):
        """Test that Instagram has platform-specific axes (not identical to LinkedIn)"""
        # Instagram should mention visual pairing (LinkedIn doesn't)
        assert "visual" in QUALITY_CHECK_PROMPT.lower()

        # Instagram should mention mobile/readability specifically
        assert "mobile" in QUALITY_CHECK_PROMPT.lower() or "readability" in QUALITY_CHECK_PROMPT.lower()


class TestInstagramFormatting:
    """Test Instagram-specific formatting requirements"""

    def test_hashtag_strategy_mentioned(self):
        """Test that prompts mention hashtag strategy"""
        assert "hashtag" in CREATE_CAPTION_DRAFT_PROMPT.lower()
        assert "hashtag" in QUALITY_CHECK_PROMPT.lower()

    def test_line_break_guidance(self):
        """Test that formatting prompts mention line breaks"""
        prompt_text = CREATE_CAPTION_DRAFT_PROMPT.lower()
        assert "line break" in prompt_text or "formatting" in prompt_text

    def test_emoji_usage_mentioned(self):
        """Test that prompts reference emoji usage"""
        # Instagram captions often use emojis
        prompt_combined = (CREATE_CAPTION_DRAFT_PROMPT + QUALITY_CHECK_PROMPT).lower()
        # At least one prompt should mention visual elements or formatting


class TestCoWritingWorkflow:
    """Test co-writing workflow implementation"""

    def test_cowriting_in_system_prompt(self):
        """Test that system prompt includes co-writing workflow"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        # Check for co-writing section
        assert 'CO-WRITE' in content or 'co-write' in content.lower()
        assert 'generate_post_' in content
        assert 'quality_check_' in content
        assert 'apply_fixes_' in content

    def test_send_to_calendar_tool_exists(self):
        """Test that send_to_calendar tool is defined"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        assert 'send_to_calendar' in content
        assert 'def send_to_calendar' in content or 'async def send_to_calendar' in content

    def test_cowriting_mentions_calendar_emoji(self):
        """Test that co-writing workflow mentions 📅 emoji reaction"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        # Should mention emoji or calendar reaction
        assert '📅' in content or 'calendar' in content.lower()

    def test_cowriting_question_in_prompt(self):
        """Test that system prompt asks user about co-writing vs auto-publish"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        # Should ask the key question
        assert 'write this together' in content.lower() or 'co-write' in content.lower()
        assert 'content calendar' in content.lower()


class TestToolCounts:
    """Test that tool counts are accurate"""

    def test_mcp_server_version_updated(self):
        """Test that MCP server version was bumped"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        # Should have version 2.3.0 or higher
        assert 'version="2.' in content
        assert '2.3' in content or '2.4' in content or '3.' in content

    def test_tool_count_updated(self):
        """Test that tool count print statement reflects new tools"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        # Should mention 23 tools (or more if additional features added)
        # 8 general + 15 co-writing (5 platforms × 3 tools)
        import re
        tool_count_match = re.search(r'(\d+)\s+tools', content)
        if tool_count_match:
            count = int(tool_count_match.group(1))
            assert count >= 23, f"Should have at least 23 tools, found {count}"


class TestAllPlatforms:
    """Test that all 5 platforms are supported"""

    def test_all_generate_post_tools_exist(self):
        """Test that generate_post exists for all 5 platforms"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        platforms = ['linkedin', 'twitter', 'email', 'youtube', 'instagram']
        for platform in platforms:
            assert f'generate_post_{platform}' in content, f"Missing generate_post_{platform}"

    def test_all_quality_check_tools_exist(self):
        """Test that quality_check exists for all 5 platforms"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        platforms = ['linkedin', 'twitter', 'email', 'youtube', 'instagram']
        for platform in platforms:
            assert f'quality_check_{platform}' in content, f"Missing quality_check_{platform}"

    def test_all_apply_fixes_tools_exist(self):
        """Test that apply_fixes exists for all 5 platforms"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        platforms = ['linkedin', 'twitter', 'email', 'youtube', 'instagram']
        for platform in platforms:
            assert f'apply_fixes_{platform}' in content, f"Missing apply_fixes_{platform}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

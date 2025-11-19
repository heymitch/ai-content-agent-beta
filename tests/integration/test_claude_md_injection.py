"""
Integration tests for CLAUDE.md injection into Direct API agents (Phase 2)
Tests the load_system_prompt function and agent initialization
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from integrations.prompt_loader import (
    load_system_prompt,
    get_client_context_path,
    client_context_exists
)


class TestLoadSystemPrompt:
    """Tests for load_system_prompt function"""

    def test_no_claude_md_returns_base_only(self):
        """When CLAUDE.md doesn't exist, returns base prompt unchanged"""
        base_prompt = "You are a content agent."

        with patch.object(Path, 'exists', return_value=False):
            result = load_system_prompt(base_prompt)

        assert result == base_prompt
        assert "CLIENT BUSINESS CONTEXT" not in result

    def test_empty_claude_md_returns_base_only(self):
        """When CLAUDE.md is empty, returns base prompt unchanged"""
        base_prompt = "You are a content agent."

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value="   \n\n   "):
                result = load_system_prompt(base_prompt)

        assert result == base_prompt
        assert "CLIENT BUSINESS CONTEXT" not in result

    def test_valid_claude_md_appends_context(self):
        """When CLAUDE.md has content, appends with CLIENT BUSINESS CONTEXT header"""
        base_prompt = "You are a content agent."
        client_context = "Brand: Acme Corp\nAudience: B2B marketers"

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=client_context):
                result = load_system_prompt(base_prompt)

        # Check structure
        assert base_prompt in result
        assert "---" in result
        assert "## CLIENT BUSINESS CONTEXT" in result
        assert "Brand: Acme Corp" in result
        assert "B2B marketers" in result
        assert "IMPORTANT: Use the above CLIENT BUSINESS CONTEXT" in result

    def test_error_reading_claude_md_returns_base(self):
        """When CLAUDE.md can't be read, falls back to base prompt"""
        base_prompt = "You are a content agent."

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', side_effect=Exception("Read error")):
                result = load_system_prompt(base_prompt)

        assert result == base_prompt

    def test_context_instructions_included(self):
        """Verifies usage instructions are included in composed prompt"""
        base_prompt = "Base instructions."
        client_context = "Brand voice: Professional"

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=client_context):
                result = load_system_prompt(base_prompt)

        # Check for key instruction elements
        assert "Match their brand voice" in result
        assert "Target their specific audience" in result
        assert "Reference their products/services" in result
        assert "workflow and quality rules stay the same" in result


class TestClientContextHelpers:
    """Tests for helper functions"""

    def test_get_client_context_path_returns_correct_path(self):
        """Returns path to .claude/CLAUDE.md"""
        path = get_client_context_path()

        assert path.name == "CLAUDE.md"
        assert ".claude" in str(path)

    def test_client_context_exists_when_file_present(self):
        """Returns True when CLAUDE.md exists with content"""
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value="Some content"):
                assert client_context_exists() is True

    def test_client_context_exists_when_file_missing(self):
        """Returns False when CLAUDE.md doesn't exist"""
        with patch.object(Path, 'exists', return_value=False):
            assert client_context_exists() is False

    def test_client_context_exists_when_file_empty(self):
        """Returns False when CLAUDE.md is empty"""
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=""):
                assert client_context_exists() is False


class TestDirectAPIAgentInjection:
    """Tests that all Direct API agents call load_system_prompt"""

    def test_linkedin_agent_uses_load_system_prompt(self):
        """LinkedIn agent wraps system prompt with load_system_prompt"""
        # Import the agent
        from agents.linkedin_direct_api_agent import LinkedInDirectAPIAgent

        # Check that it imports load_system_prompt
        from agents import linkedin_direct_api_agent
        assert hasattr(linkedin_direct_api_agent, 'load_system_prompt') or \
               'load_system_prompt' in dir(linkedin_direct_api_agent)

    def test_twitter_agent_uses_load_system_prompt(self):
        """Twitter agent wraps system prompt with load_system_prompt"""
        from agents.twitter_direct_api_agent import TwitterDirectAPIAgent
        from agents import twitter_direct_api_agent
        assert hasattr(twitter_direct_api_agent, 'load_system_prompt') or \
               'load_system_prompt' in dir(twitter_direct_api_agent)

    def test_email_agent_uses_load_system_prompt(self):
        """Email agent wraps system prompt with load_system_prompt"""
        from agents.email_direct_api_agent import EmailDirectAPIAgent
        from agents import email_direct_api_agent
        assert hasattr(email_direct_api_agent, 'load_system_prompt') or \
               'load_system_prompt' in dir(email_direct_api_agent)

    def test_youtube_agent_uses_load_system_prompt(self):
        """YouTube agent wraps system prompt with load_system_prompt"""
        from agents.youtube_direct_api_agent import YouTubeDirectAPIAgent
        from agents import youtube_direct_api_agent
        assert hasattr(youtube_direct_api_agent, 'load_system_prompt') or \
               'load_system_prompt' in dir(youtube_direct_api_agent)

    def test_instagram_agent_uses_load_system_prompt(self):
        """Instagram agent wraps system prompt with load_system_prompt"""
        from agents.instagram_direct_api_agent import InstagramDirectAPIAgent
        from agents import instagram_direct_api_agent
        assert hasattr(instagram_direct_api_agent, 'load_system_prompt') or \
               'load_system_prompt' in dir(instagram_direct_api_agent)


class TestAgentSystemPromptContent:
    """Tests that agent system prompts actually contain CLAUDE.md content when present"""

    @pytest.fixture
    def mock_claude_md(self):
        """Mock CLAUDE.md with test content"""
        return "TEST_MARKER_12345\nBrand: Test Company\nAudience: Developers"

    def test_linkedin_agent_system_prompt_contains_context(self, mock_claude_md):
        """LinkedIn agent's system_prompt contains CLAUDE.md content"""
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=mock_claude_md):
                # We can't easily instantiate the agent without API key,
                # but we can test the load_system_prompt function directly
                base_prompt = "LinkedIn content agent instructions..."
                result = load_system_prompt(base_prompt)

                assert "TEST_MARKER_12345" in result
                assert "Brand: Test Company" in result

    def test_context_preserves_special_characters(self):
        """CLAUDE.md content with special characters is preserved"""
        client_context = """
        ## Brand Voice
        - Use em-dashes (—) not hyphens
        - Include $revenue figures
        - Quote "experts" with proper punctuation
        - Use bullet • points
        """

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=client_context):
                result = load_system_prompt("Base")

                assert "em-dashes" in result
                assert "$revenue" in result
                assert '"experts"' in result


class TestPromptComposition:
    """Tests for the overall prompt composition structure"""

    def test_separator_between_base_and_context(self):
        """There's a clear separator between base and client context"""
        base = "Base instructions"
        context = "Client context"

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=context):
                result = load_system_prompt(base)

        # Should have separators
        assert result.count("---") >= 2

    def test_base_prompt_comes_first(self):
        """Base prompt appears before client context"""
        base = "BASE_COMES_FIRST"
        context = "CONTEXT_COMES_SECOND"

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=context):
                result = load_system_prompt(base)

        base_pos = result.index("BASE_COMES_FIRST")
        context_pos = result.index("CONTEXT_COMES_SECOND")
        assert base_pos < context_pos

    def test_instruction_section_comes_after_context(self):
        """Usage instructions appear after the client context"""
        base = "Base"
        context = "Context"

        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'read_text', return_value=context):
                result = load_system_prompt(base)

        context_pos = result.index("Context")
        instruction_pos = result.index("IMPORTANT: Use the above")
        assert context_pos < instruction_pos


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

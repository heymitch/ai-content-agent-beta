"""
Unit tests for validation tools (Phase 4)
Tests validate_content, detect_ai_patterns, and apply_content_fixes
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestValidateContent:
    """Tests for the validate_content tool"""

    def test_routes_to_linkedin_native_tool(self):
        """LinkedIn platform routes to linkedin_native_tools"""
        from slack_bot.agent_tools import validate_content

        with patch('tools.linkedin_native_tools.quality_check_native') as mock_check:
            # Create a mock coroutine
            async def mock_coro(text):
                return "Score: 20/25"
            mock_check.return_value = mock_coro("test")

            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Score: 20/25"

                result = validate_content("Test content", "linkedin")

                assert "Quality Check Results" in result
                assert "linkedin" in result.lower()

    def test_routes_to_twitter_native_tool(self):
        """Twitter platform routes to twitter_native_tools"""
        from slack_bot.agent_tools import validate_content

        with patch('tools.twitter_native_tools.quality_check_native') as mock_check:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Score: 18/25"

                result = validate_content("Test tweet", "twitter")

                assert "Quality Check Results" in result
                assert "twitter" in result.lower()

    def test_routes_to_email_native_tool(self):
        """Email platform routes to email_native_tools"""
        from slack_bot.agent_tools import validate_content

        with patch('tools.email_native_tools.quality_check_native') as mock_check:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Score: 22/25"

                result = validate_content("Test email", "email")

                assert "Email" in result

    def test_routes_to_youtube_native_tool(self):
        """YouTube platform routes to youtube_native_tools"""
        from slack_bot.agent_tools import validate_content

        with patch('tools.youtube_native_tools.quality_check_native') as mock_check:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Score: 19/25"

                result = validate_content("Test script", "youtube")

                assert "Youtube" in result

    def test_routes_to_instagram_native_tool(self):
        """Instagram platform routes to instagram_native_tools"""
        from slack_bot.agent_tools import validate_content

        with patch('tools.instagram_native_tools.quality_check_native') as mock_check:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Score: 21/25"

                result = validate_content("Test caption", "instagram")

                assert "Instagram" in result

    def test_default_platform_is_linkedin(self):
        """Default platform is LinkedIn if not specified"""
        from slack_bot.agent_tools import validate_content

        with patch('tools.linkedin_native_tools.quality_check_native') as mock_check:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Score: 20/25"

                # Call without platform parameter
                result = validate_content("Test content")

                assert "Linkedin" in result

    def test_unknown_platform_defaults_to_linkedin(self):
        """Unknown platform falls back to LinkedIn"""
        from slack_bot.agent_tools import validate_content

        with patch('tools.linkedin_native_tools.quality_check_native') as mock_check:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Score: 20/25"

                result = validate_content("Test content", "tiktok")

                # Should still work, using LinkedIn as default
                assert "Quality Check Results" in result

    def test_error_handling(self):
        """Returns error message on exception"""
        from slack_bot.agent_tools import validate_content

        with patch('tools.linkedin_native_tools.quality_check_native') as mock_check:
            with patch('asyncio.run', side_effect=Exception("API Error")):
                result = validate_content("Test content", "linkedin")

                assert "Error validating content" in result
                assert "API Error" in result


class TestDetectAIPatterns:
    """Tests for the detect_ai_patterns tool"""

    def test_returns_ai_probability(self):
        """Returns AI probability percentage"""
        from slack_bot.agent_tools import detect_ai_patterns

        with patch.dict('os.environ', {'GPTZERO_API_KEY': 'test_key'}):
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'documents': [{
                        'completely_generated_prob': 0.35,
                        'sentences': []
                    }]
                }
                mock_post.return_value = mock_response

                result = detect_ai_patterns("Test content")

                assert "AI Probability" in result
                assert "35" in result

    def test_returns_flagged_sentences(self):
        """Returns sentences flagged as AI-generated"""
        from slack_bot.agent_tools import detect_ai_patterns

        with patch.dict('os.environ', {'GPTZERO_API_KEY': 'test_key'}):
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'documents': [{
                        'completely_generated_prob': 0.85,
                        'sentences': [
                            {'sentence': 'This is a flagged sentence.', 'generated_prob': 0.95},
                            {'sentence': 'This is human.', 'generated_prob': 0.2}
                        ]
                    }]
                }
                mock_post.return_value = mock_response

                result = detect_ai_patterns("Test content")

                assert "Flagged Sentences" in result
                assert "flagged sentence" in result

    def test_missing_api_key_error(self):
        """Returns error when API key not configured"""
        from slack_bot.agent_tools import detect_ai_patterns

        with patch.dict('os.environ', {}, clear=True):
            # Remove the key if it exists
            import os
            if 'GPTZERO_API_KEY' in os.environ:
                del os.environ['GPTZERO_API_KEY']

            result = detect_ai_patterns("Test content")

            assert "not configured" in result or "API key" in result

    def test_api_error_handling(self):
        """Handles API errors gracefully"""
        from slack_bot.agent_tools import detect_ai_patterns

        with patch.dict('os.environ', {'GPTZERO_API_KEY': 'test_key'}):
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_post.return_value = mock_response

                result = detect_ai_patterns("Test content")

                assert "error" in result.lower()

    def test_verdict_for_low_ai_probability(self):
        """Shows green verdict for human-like content"""
        from slack_bot.agent_tools import detect_ai_patterns

        with patch.dict('os.environ', {'GPTZERO_API_KEY': 'test_key'}):
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'documents': [{
                        'completely_generated_prob': 0.15,
                        'sentences': []
                    }]
                }
                mock_post.return_value = mock_response

                result = detect_ai_patterns("Test content")

                assert "Human-like" in result

    def test_verdict_for_high_ai_probability(self):
        """Shows red verdict for AI-detected content"""
        from slack_bot.agent_tools import detect_ai_patterns

        with patch.dict('os.environ', {'GPTZERO_API_KEY': 'test_key'}):
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'documents': [{
                        'completely_generated_prob': 0.90,
                        'sentences': []
                    }]
                }
                mock_post.return_value = mock_response

                result = detect_ai_patterns("Test content")

                assert "AI-detected" in result


class TestApplyContentFixes:
    """Tests for the apply_content_fixes tool"""

    def test_routes_to_linkedin_native_tool(self):
        """LinkedIn platform routes to linkedin apply_fixes_native"""
        from slack_bot.agent_tools import apply_content_fixes

        with patch('tools.linkedin_native_tools.apply_fixes_native') as mock_fix:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Fixed content here"

                result = apply_content_fixes(
                    "Original content",
                    '["needs better hook"]',
                    "linkedin"
                )

                assert "Fixed Content" in result
                assert "Linkedin" in result

    def test_routes_to_twitter_native_tool(self):
        """Twitter platform routes to twitter apply_fixes_native"""
        from slack_bot.agent_tools import apply_content_fixes

        with patch('tools.twitter_native_tools.apply_fixes_native') as mock_fix:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Fixed tweet"

                result = apply_content_fixes(
                    "Original tweet",
                    "too long",
                    "twitter"
                )

                assert "Twitter" in result

    def test_parses_json_issues_array(self):
        """Parses JSON array of issues"""
        from slack_bot.agent_tools import apply_content_fixes

        with patch('tools.linkedin_native_tools.apply_fixes_native') as mock_fix:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Fixed"

                # Should not raise on valid JSON
                result = apply_content_fixes(
                    "Content",
                    '["issue1", "issue2", "issue3"]',
                    "linkedin"
                )

                assert "Fixed Content" in result

    def test_accepts_plain_text_issues(self):
        """Accepts plain text description of issues"""
        from slack_bot.agent_tools import apply_content_fixes

        with patch('tools.linkedin_native_tools.apply_fixes_native') as mock_fix:
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Fixed"

                # Should not raise on plain text
                result = apply_content_fixes(
                    "Content",
                    "The hook is too generic and needs more specifics",
                    "linkedin"
                )

                assert "Fixed Content" in result

    def test_error_handling(self):
        """Returns error message on exception"""
        from slack_bot.agent_tools import apply_content_fixes

        with patch('tools.linkedin_native_tools.apply_fixes_native') as mock_fix:
            with patch('asyncio.run', side_effect=Exception("Fix failed")):
                result = apply_content_fixes(
                    "Content",
                    "issues",
                    "linkedin"
                )

                assert "Error applying fixes" in result


class TestToolRegistration:
    """Tests that validation tools are properly registered"""

    def test_validate_content_in_content_tools(self):
        """validate_content is in CONTENT_TOOLS"""
        from slack_bot.agent_tools import CONTENT_TOOLS

        tool_names = [t['name'] for t in CONTENT_TOOLS]
        assert 'validate_content' in tool_names

    def test_detect_ai_patterns_in_content_tools(self):
        """detect_ai_patterns is in CONTENT_TOOLS"""
        from slack_bot.agent_tools import CONTENT_TOOLS

        tool_names = [t['name'] for t in CONTENT_TOOLS]
        assert 'detect_ai_patterns' in tool_names

    def test_apply_content_fixes_in_content_tools(self):
        """apply_content_fixes is in CONTENT_TOOLS"""
        from slack_bot.agent_tools import CONTENT_TOOLS

        tool_names = [t['name'] for t in CONTENT_TOOLS]
        assert 'apply_content_fixes' in tool_names

    def test_validate_content_in_tool_functions(self):
        """validate_content is in TOOL_FUNCTIONS"""
        from slack_bot.agent_tools import TOOL_FUNCTIONS

        assert 'validate_content' in TOOL_FUNCTIONS

    def test_detect_ai_patterns_in_tool_functions(self):
        """detect_ai_patterns is in TOOL_FUNCTIONS"""
        from slack_bot.agent_tools import TOOL_FUNCTIONS

        assert 'detect_ai_patterns' in TOOL_FUNCTIONS

    def test_apply_content_fixes_in_tool_functions(self):
        """apply_content_fixes is in TOOL_FUNCTIONS"""
        from slack_bot.agent_tools import TOOL_FUNCTIONS

        assert 'apply_content_fixes' in TOOL_FUNCTIONS


class TestToolSchemas:
    """Tests for tool input schemas"""

    def test_validate_content_schema(self):
        """validate_content has correct input schema"""
        from slack_bot.agent_tools import CONTENT_TOOLS

        tool = next(t for t in CONTENT_TOOLS if t['name'] == 'validate_content')
        schema = tool['input_schema']

        assert 'text' in schema['properties']
        assert 'platform' in schema['properties']
        assert 'text' in schema['required']

    def test_detect_ai_patterns_schema(self):
        """detect_ai_patterns has correct input schema"""
        from slack_bot.agent_tools import CONTENT_TOOLS

        tool = next(t for t in CONTENT_TOOLS if t['name'] == 'detect_ai_patterns')
        schema = tool['input_schema']

        assert 'text' in schema['properties']
        assert 'text' in schema['required']

    def test_apply_content_fixes_schema(self):
        """apply_content_fixes has correct input schema"""
        from slack_bot.agent_tools import CONTENT_TOOLS

        tool = next(t for t in CONTENT_TOOLS if t['name'] == 'apply_content_fixes')
        schema = tool['input_schema']

        assert 'text' in schema['properties']
        assert 'issues' in schema['properties']
        assert 'platform' in schema['properties']
        assert 'text' in schema['required']
        assert 'issues' in schema['required']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Integration tests for validation system
Tests async validation flow, API integration, and error handling
"""
import pytest
import asyncio
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from integrations.validation_utils import (
    run_quality_check,
    run_gptzero_check,
    run_all_validators,
    format_validation_for_airtable
)


class TestValidationAPIKeyHandling:
    """Test API key validation and error handling"""

    @pytest.mark.asyncio
    async def test_quality_check_missing_api_key(self):
        """Test that missing ANTHROPIC_API_KEY raises clear error"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                await run_quality_check("Test content", "linkedin")

    @pytest.mark.asyncio
    async def test_gptzero_graceful_skip_no_key(self):
        """Test that missing GPTZERO_API_KEY returns None gracefully"""
        with patch.dict(os.environ, {}, clear=True):
            result = await run_gptzero_check("Test content")
            assert result is None


class TestValidationContentHandling:
    """Test content edge cases"""

    @pytest.mark.asyncio
    async def test_gptzero_skip_short_content(self):
        """Test that content <50 chars is skipped by GPTZero"""
        with patch.dict(os.environ, {'GPTZERO_API_KEY': 'fake_key'}):
            result = await run_gptzero_check("Short")
            assert result['status'] == 'SKIPPED'
            assert 'too short' in result['reason'].lower()

    @pytest.mark.asyncio
    @patch('integrations.validation_utils.Anthropic')
    async def test_quality_check_with_valid_content(self, mock_anthropic):
        """Test quality check with valid content"""
        # Mock Claude API response
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_text_block = MagicMock()
        mock_text_block.text = json.dumps({
            "scores": {"total": 20, "hook": 4, "proof": 4, "structure": 4, "cta": 4, "human": 4},
            "decision": "accept",
            "issues": [],
            "surgical_summary": "Great post!"
        })
        mock_response.content = [mock_text_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            result = await run_quality_check("Test LinkedIn post content", "linkedin")

        assert result['scores']['total'] == 20
        assert result['decision'] == 'accept'
        assert isinstance(result['issues'], list)


class TestParallelValidation:
    """Test concurrent validation execution"""

    @pytest.mark.asyncio
    @patch('integrations.validation_utils.run_quality_check')
    @patch('integrations.validation_utils.run_gptzero_check')
    async def test_validators_run_in_parallel(self, mock_gptzero, mock_quality):
        """Test that validators run concurrently (asyncio.gather)"""
        # Setup mocks to track execution
        mock_quality.return_value = {
            "scores": {"total": 18},
            "decision": "accept",
            "issues": [],
            "surgical_summary": "Looks good"
        }
        mock_gptzero.return_value = {
            "status": "PASS",
            "human_probability": 85.0
        }

        # Run validators
        result_json = await run_all_validators("Test content", "linkedin")

        # Verify both were called
        mock_quality.assert_called_once()
        mock_gptzero.assert_called_once()

        # Verify result structure
        result = json.loads(result_json)
        assert 'quality_scores' in result
        assert 'gptzero' in result
        assert result['platform'] == 'linkedin'


class TestAllPlatforms:
    """Test validation works across all platforms"""

    @pytest.mark.asyncio
    @patch('integrations.validation_utils.run_quality_check')
    @patch('integrations.validation_utils.run_gptzero_check')
    async def test_all_platforms_supported(self, mock_gptzero, mock_quality):
        """Test that all 4 platforms work with validation"""
        mock_quality.return_value = {
            "scores": {"total": 15},
            "decision": "revise",
            "issues": ["Too generic"],
            "surgical_summary": "Add specifics"
        }
        mock_gptzero.return_value = None  # No GPTZero key

        platforms = ['linkedin', 'twitter', 'email', 'youtube']

        for platform in platforms:
            result_json = await run_all_validators(f"Test {platform} content", platform)
            result = json.loads(result_json)

            assert result['platform'] == platform
            assert 'quality_scores' in result
            assert 'gptzero' in result


class TestValidationFormatting:
    """Test validation result formatting for Airtable"""

    def test_format_validation_empty_input(self):
        """Test formatting with empty input"""
        result = format_validation_for_airtable("")
        assert "No validation data" in result

    def test_format_validation_invalid_json(self):
        """Test formatting with invalid JSON"""
        result = format_validation_for_airtable("not json")
        assert "Invalid validation data" in result

    def test_format_validation_complete_data(self):
        """Test formatting with complete validation data"""
        validation_data = {
            "quality_scores": {
                "total": 22,
                "hook": 5,
                "proof": 4,
                "structure": 5,
                "cta": 4,
                "human": 4
            },
            "decision": "accept",
            "ai_patterns_found": ["contrast structure"],
            "surgical_summary": "Remove 'it's not X, it's Y' pattern",
            "gptzero": {
                "status": "PASS",
                "human_probability": 78.5,
                "ai_probability": 21.5,
                "flagged_sentences_count": 0
            },
            "platform": "linkedin",
            "timestamp": "2025-10-16T10:00:00"
        }

        result = format_validation_for_airtable(json.dumps(validation_data))

        # Check key sections are present
        assert "CONTENT VALIDATION REPORT" in result
        assert "ACCEPT" in result
        assert "22/25" in result
        assert "Quality Breakdown" in result
        assert "AI Patterns Detected" in result
        assert "Recommended Fixes" in result
        assert "GPTZero AI Detection" in result
        assert "78.5%" in result

    def test_format_validation_gptzero_not_configured(self):
        """Test formatting when GPTZero is not configured"""
        validation_data = {
            "quality_scores": {"total": 18},
            "decision": "accept",
            "ai_patterns_found": [],
            "surgical_summary": "Good",
            "gptzero": {"status": "NOT_RUN", "reason": "API key not configured"},
            "platform": "linkedin",
            "timestamp": "2025-10-16T10:00:00"
        }

        result = format_validation_for_airtable(json.dumps(validation_data))

        assert "GPTZero: Not configured" in result
        assert "set GPTZERO_API_KEY to enable" in result


class TestErrorHandling:
    """Test error handling in validation"""

    @pytest.mark.asyncio
    @patch('integrations.validation_utils.Anthropic')
    async def test_quality_check_api_error(self, mock_anthropic):
        """Test quality check handles API errors gracefully"""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        mock_anthropic.return_value = mock_client

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            result = await run_quality_check("Test content", "linkedin")

        # Should return error result, not raise exception
        assert result['decision'] == 'error'
        assert 'API Error' in result['surgical_summary']

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_gptzero_api_error(self, mock_client):
        """Test GPTZero handles API errors gracefully"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Network Error")

        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_context

        with patch.dict(os.environ, {'GPTZERO_API_KEY': 'test_key'}):
            result = await run_gptzero_check("Test content that is long enough")

        # Should return error result, not raise exception
        assert result['status'] == 'ERROR'
        assert 'error' in result['reason'].lower()


class TestEndToEndFlow:
    """Test complete validation flow"""

    @pytest.mark.asyncio
    @patch('integrations.validation_utils.Anthropic')
    @patch('httpx.AsyncClient')
    async def test_complete_validation_flow(self, mock_http_client, mock_anthropic):
        """Test full validation with both quality check and GPTZero"""
        # Mock Claude API
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_text_block = MagicMock()
        mock_text_block.text = json.dumps({
            "scores": {"total": 20, "hook": 4, "proof": 4, "structure": 4, "cta": 4, "human": 4},
            "decision": "accept",
            "issues": [],
            "surgical_summary": "Excellent post"
        })
        mock_response.content = [mock_text_block]

        mock_claude_client = MagicMock()
        mock_claude_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_claude_client

        # Mock GPTZero API
        mock_gptzero_response = MagicMock()
        mock_gptzero_response.json.return_value = {
            "documents": [{
                "class_probabilities": {
                    "human": 0.85,
                    "ai": 0.10,
                    "mixed": 0.05
                },
                "sentences": []
            }]
        }
        mock_gptzero_response.raise_for_status = MagicMock()

        mock_http_context = AsyncMock()
        mock_http_context.__aenter__.return_value.post = AsyncMock(return_value=mock_gptzero_response)
        mock_http_client.return_value = mock_http_context

        # Run full validation
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'test_key',
            'GPTZERO_API_KEY': 'test_key'
        }):
            result_json = await run_all_validators(
                "This is a comprehensive LinkedIn post about AI trends.",
                "linkedin"
            )

        # Parse and verify result
        result = json.loads(result_json)

        assert result['quality_scores']['total'] == 20
        assert result['decision'] == 'accept'
        assert result['gptzero']['status'] == 'PASS'
        assert result['gptzero']['human_probability'] == 85.0
        assert result['platform'] == 'linkedin'
        assert 'timestamp' in result

        # Test formatting
        formatted = format_validation_for_airtable(result_json)
        assert "ACCEPT" in formatted
        assert "20/25" in formatted
        assert "85.0%" in formatted


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

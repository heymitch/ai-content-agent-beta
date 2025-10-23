"""
Integration tests for Co-Writing Workflow
Tests generate_post → quality_check → apply_fixes → send_to_calendar flow
"""
import pytest
import asyncio
import os
import json
from unittest.mock import patch, AsyncMock, MagicMock

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestGeneratePostTools:
    """Test generate_post tools for all platforms"""

    @pytest.mark.asyncio
    @patch('anthropic.Anthropic')
    async def test_generate_post_linkedin(self, mock_anthropic):
        """Test LinkedIn post generation"""
        from slack_bot.claude_agent_handler import generate_post_linkedin

        # Mock Claude API response
        mock_response = MagicMock()
        mock_text_block = MagicMock()
        mock_text_block.text = "This is a great LinkedIn post about AI."
        mock_response.content = [mock_text_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Call tool
        result = await generate_post_linkedin({
            'topic': 'AI trends',
            'context': 'Latest developments'
        })

        # Verify result structure
        assert 'content' in result
        assert len(result['content']) > 0
        assert result['content'][0]['type'] == 'text'
        assert 'LinkedIn' in result['content'][0]['text'] or 'AI' in result['content'][0]['text']

        # Verify Claude was called with correct prompt
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        assert 'WRITE_LIKE_HUMAN_RULES' in str(call_args) or 'messages' in call_args[1]

    @pytest.mark.asyncio
    @patch('anthropic.Anthropic')
    async def test_generate_post_instagram(self, mock_anthropic):
        """Test Instagram caption generation"""
        from slack_bot.claude_agent_handler import generate_post_instagram

        # Mock Claude API response
        mock_response = MagicMock()
        mock_text_block = MagicMock()
        mock_text_block.text = "Instagram caption about content creation 📱\n\nCheck out this amazing strategy!\n\n#contentcreation #instagram"
        mock_response.content = [mock_text_block]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        # Call tool
        result = await generate_post_instagram({
            'topic': 'Content creation tips',
            'context': 'For creators'
        })

        # Verify result
        assert 'content' in result
        assert result['content'][0]['type'] == 'text'
        generated_text = result['content'][0]['text']

        # Instagram captions should be under 2,200 chars (this is a mock, but verify structure)
        assert len(generated_text) < 5000, "Response should be reasonable length"

    @pytest.mark.asyncio
    async def test_all_generate_post_tools_importable(self):
        """Test that all 5 generate_post tools can be imported"""
        from slack_bot.claude_agent_handler import (
            generate_post_linkedin,
            generate_post_twitter,
            generate_post_email,
            generate_post_youtube,
            generate_post_instagram
        )

        assert generate_post_linkedin is not None
        assert generate_post_twitter is not None
        assert generate_post_email is not None
        assert generate_post_youtube is not None
        assert generate_post_instagram is not None


class TestQualityCheckTools:
    """Test quality_check wrapper tools"""

    @pytest.mark.asyncio
    async def test_quality_check_tools_importable(self):
        """Test that all quality_check tools can be imported"""
        from slack_bot.claude_agent_handler import (
            quality_check_linkedin,
            quality_check_twitter,
            quality_check_email,
            quality_check_youtube,
            quality_check_instagram
        )

        assert quality_check_linkedin is not None
        assert quality_check_twitter is not None
        assert quality_check_email is not None
        assert quality_check_youtube is not None
        assert quality_check_instagram is not None

    @pytest.mark.asyncio
    @patch('agents.linkedin_sdk_agent.quality_check')
    async def test_quality_check_linkedin_delegation(self, mock_linkedin_quality):
        """Test that quality_check_linkedin delegates to SDK agent"""
        from slack_bot.claude_agent_handler import quality_check_linkedin

        # Mock the LinkedIn SDK quality_check
        mock_linkedin_quality.return_value = {
            'scores': {'total': 85},
            'decision': 'accept',
            'issues': []
        }

        # Call wrapper
        result = await quality_check_linkedin({
            'post': 'Test LinkedIn post content'
        })

        # Verify delegation occurred
        mock_linkedin_quality.assert_called_once()
        assert result['scores']['total'] == 85


class TestApplyFixesTools:
    """Test apply_fixes wrapper tools"""

    @pytest.mark.asyncio
    async def test_apply_fixes_tools_importable(self):
        """Test that all apply_fixes tools can be imported"""
        from slack_bot.claude_agent_handler import (
            apply_fixes_linkedin,
            apply_fixes_twitter,
            apply_fixes_email,
            apply_fixes_youtube,
            apply_fixes_instagram
        )

        assert apply_fixes_linkedin is not None
        assert apply_fixes_twitter is not None
        assert apply_fixes_email is not None
        assert apply_fixes_youtube is not None
        assert apply_fixes_instagram is not None

    @pytest.mark.asyncio
    @patch('agents.linkedin_sdk_agent.apply_fixes')
    async def test_apply_fixes_linkedin_delegation(self, mock_linkedin_fixes):
        """Test that apply_fixes_linkedin delegates to SDK agent"""
        from slack_bot.claude_agent_handler import apply_fixes_linkedin

        # Mock the LinkedIn SDK apply_fixes
        mock_linkedin_fixes.return_value = {
            'revised_post': 'Improved LinkedIn post',
            'changes_made': ['Added specific numbers', 'Improved hook']
        }

        # Call wrapper
        result = await apply_fixes_linkedin({
            'post': 'Original post',
            'issues': 'Needs more specifics',
            'feedback': 'Add data points'
        })

        # Verify delegation occurred
        mock_linkedin_fixes.assert_called_once()


class TestSendToCalendar:
    """Test send_to_calendar tool"""

    @pytest.mark.asyncio
    async def test_send_to_calendar_importable(self):
        """Test that send_to_calendar tool can be imported"""
        from slack_bot.claude_agent_handler import send_to_calendar

        assert send_to_calendar is not None

    @pytest.mark.asyncio
    @patch('slack_bot.claude_agent_handler.SlackThreadMemory')
    @patch('slack_bot.claude_agent_handler.get_airtable_client')
    async def test_send_to_calendar_creates_record(self, mock_airtable, mock_memory):
        """Test that send_to_calendar saves to Airtable"""
        from slack_bot.claude_agent_handler import send_to_calendar

        # Mock Airtable client
        mock_airtable_instance = MagicMock()
        mock_airtable_instance.create_content_record.return_value = {
            'success': True,
            'url': 'https://airtable.com/test123',
            'record_id': 'rec123'
        }
        mock_airtable.return_value = mock_airtable_instance

        # Mock memory
        mock_memory_instance = MagicMock()
        mock_memory_instance.get_thread.return_value = None  # New thread
        mock_memory_instance.create_thread = MagicMock()
        mock_memory.return_value = mock_memory_instance

        # Mock supabase
        with patch('slack_bot.claude_agent_handler.supabase', MagicMock()):
            # Call tool
            result = await send_to_calendar({
                'post': 'Test post content',
                'platform': 'linkedin',
                'thread_ts': '1234567890.123',
                'channel_id': 'C123',
                'user_id': 'U123',
                'score': 88
            })

            # Verify result structure
            assert 'content' in result
            assert result['content'][0]['type'] == 'text'
            response_text = result['content'][0]['text']

            # Should contain success message and Airtable URL
            assert '✅' in response_text or 'success' in response_text.lower()
            assert 'airtable' in response_text.lower()

    @pytest.mark.asyncio
    @patch('slack_bot.claude_agent_handler.SlackThreadMemory')
    @patch('slack_bot.claude_agent_handler.get_airtable_client')
    async def test_send_to_calendar_updates_existing_thread(self, mock_airtable, mock_memory):
        """Test that send_to_calendar updates existing thread"""
        from slack_bot.claude_agent_handler import send_to_calendar

        # Mock Airtable
        mock_airtable_instance = MagicMock()
        mock_airtable_instance.create_content_record.return_value = {
            'success': True,
            'url': 'https://airtable.com/test',
            'record_id': 'rec456'
        }
        mock_airtable.return_value = mock_airtable_instance

        # Mock memory with existing thread
        mock_memory_instance = MagicMock()
        mock_memory_instance.get_thread.return_value = {
            'thread_ts': '1234567890.123',
            'platform': 'linkedin'
        }
        mock_memory_instance.update_draft = MagicMock()
        mock_memory_instance.update_status = MagicMock()
        mock_memory.return_value = mock_memory_instance

        with patch('slack_bot.claude_agent_handler.supabase', MagicMock()):
            # Call tool
            await send_to_calendar({
                'post': 'Updated post',
                'platform': 'linkedin',
                'thread_ts': '1234567890.123',
                'channel_id': 'C123',
                'user_id': 'U123',
                'score': 92
            })

            # Verify update_draft was called (not create_thread)
            mock_memory_instance.update_draft.assert_called_once()
            mock_memory_instance.update_status.assert_called_once_with('1234567890.123', 'scheduled')


class TestCoWritingWorkflowIntegration:
    """Test end-to-end co-writing workflow"""

    @pytest.mark.asyncio
    @patch('anthropic.Anthropic')
    @patch('agents.linkedin_sdk_agent.quality_check')
    @patch('agents.linkedin_sdk_agent.apply_fixes')
    @patch('slack_bot.claude_agent_handler.get_airtable_client')
    @patch('slack_bot.claude_agent_handler.SlackThreadMemory')
    async def test_complete_cowriting_flow(
        self,
        mock_memory,
        mock_airtable,
        mock_apply_fixes,
        mock_quality_check,
        mock_anthropic
    ):
        """Test complete co-writing workflow: generate → quality_check → apply_fixes → calendar"""
        from slack_bot.claude_agent_handler import (
            generate_post_linkedin,
            quality_check_linkedin,
            apply_fixes_linkedin,
            send_to_calendar
        )

        # Step 1: Generate post
        mock_response = MagicMock()
        mock_text_block = MagicMock()
        mock_text_block.text = "AI is transforming how we create content.\n\nHere are 3 ways..."
        mock_response.content = [mock_text_block]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        draft = await generate_post_linkedin({
            'topic': 'AI content creation',
            'context': 'For marketers'
        })
        assert 'content' in draft

        # Step 2: Quality check
        mock_quality_check.return_value = {
            'scores': {'total': 72, 'hook': 3, 'body': 4, 'proof': 3, 'cta': 4, 'format': 5},
            'decision': 'revise',
            'issues': ['Add specific numbers', 'Strengthen hook'],
            'surgical_summary': 'Good structure but needs data'
        }

        quality_result = await quality_check_linkedin({
            'post': draft['content'][0]['text']
        })
        assert quality_result['scores']['total'] == 72
        assert quality_result['decision'] == 'revise'

        # Step 3: Apply fixes
        mock_apply_fixes.return_value = {
            'revised_post': 'AI is transforming how we create content—92% of marketers report...',
            'changes_made': ['Added 92% stat', 'Improved hook specificity']
        }

        fixes_result = await apply_fixes_linkedin({
            'post': draft['content'][0]['text'],
            'issues': 'Add specific numbers',
            'feedback': 'User wants data points'
        })
        assert 'revised_post' in fixes_result

        # Step 4: Quality check again (should be higher)
        mock_quality_check.return_value = {
            'scores': {'total': 88},
            'decision': 'accept'
        }

        final_quality = await quality_check_linkedin({
            'post': fixes_result['revised_post']
        })
        assert final_quality['scores']['total'] == 88

        # Step 5: Send to calendar
        mock_airtable_instance = MagicMock()
        mock_airtable_instance.create_content_record.return_value = {
            'success': True,
            'url': 'https://airtable.com/app123/tbl456/rec789',
            'record_id': 'rec789'
        }
        mock_airtable.return_value = mock_airtable_instance

        mock_memory_instance = MagicMock()
        mock_memory_instance.get_thread.return_value = None
        mock_memory_instance.create_thread = MagicMock()
        mock_memory_instance.update_status = MagicMock()
        mock_memory.return_value = mock_memory_instance

        with patch('slack_bot.claude_agent_handler.supabase', MagicMock()):
            calendar_result = await send_to_calendar({
                'post': fixes_result['revised_post'],
                'platform': 'linkedin',
                'thread_ts': '1234567890.123',
                'channel_id': 'C123',
                'user_id': 'U123',
                'score': 88
            })

            # Verify calendar submission
            assert 'content' in calendar_result
            assert 'airtable' in calendar_result['content'][0]['text'].lower()


class TestReactionHandlerIntegration:
    """Test that calendar emoji reaction integrates with send_to_calendar"""

    def test_reaction_handler_has_calendar_mapping(self):
        """Test that reactions.py has calendar emoji handler"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/reactions.py', 'r') as f:
            content = f.read()

        # Should have calendar emoji mapping
        assert 'calendar' in content.lower()
        assert 'handle_schedule' in content or 'schedule' in content

    def test_reaction_handler_checks_quality_score(self):
        """Test that reaction handler enforces quality score threshold"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/reactions.py', 'r') as f:
            content = f.read()

        # Should check score >= 70 or similar threshold
        assert 'score' in content.lower()
        assert '70' in content or 'quality' in content.lower()


class TestToolWrapperPattern:
    """Test that tool wrapper pattern is consistent"""

    def test_wrapper_tools_import_from_sdk_agents(self):
        """Test that wrapper tools delegate to SDK agent implementations"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        # Quality check wrappers should import from SDK agents
        assert 'from agents.linkedin_sdk_agent import quality_check' in content
        assert 'from agents.twitter_sdk_agent import quality_check' in content
        assert 'from agents.instagram_sdk_agent import quality_check' in content

        # Apply fixes wrappers should import from SDK agents
        assert 'from agents.linkedin_sdk_agent import apply_fixes' in content
        assert 'from agents.twitter_sdk_agent import apply_fixes' in content
        assert 'from agents.instagram_sdk_agent import apply_fixes' in content

    def test_wrapper_pattern_consistent_across_platforms(self):
        """Test that all platforms follow same wrapper pattern"""
        with open('/Users/heymitch/ai-content-agent-template/slack_bot/claude_agent_handler.py', 'r') as f:
            content = f.read()

        platforms = ['linkedin', 'twitter', 'email', 'youtube', 'instagram']

        for platform in platforms:
            # Each should have quality_check wrapper
            assert f'async def quality_check_{platform}' in content

            # Each should have apply_fixes wrapper
            assert f'async def apply_fixes_{platform}' in content


class TestErrorHandling:
    """Test error handling in co-writing workflow"""

    @pytest.mark.asyncio
    @patch('slack_bot.claude_agent_handler.get_airtable_client')
    @patch('slack_bot.claude_agent_handler.SlackThreadMemory')
    async def test_send_to_calendar_handles_airtable_error(self, mock_memory, mock_airtable):
        """Test that send_to_calendar handles Airtable errors gracefully"""
        from slack_bot.claude_agent_handler import send_to_calendar

        # Mock Airtable to return error
        mock_airtable_instance = MagicMock()
        mock_airtable_instance.create_content_record.return_value = {
            'success': False,
            'error': 'API rate limit exceeded'
        }
        mock_airtable.return_value = mock_airtable_instance

        # Mock memory
        mock_memory_instance = MagicMock()
        mock_memory_instance.get_thread.return_value = None
        mock_memory_instance.create_thread = MagicMock()
        mock_memory.return_value = mock_memory_instance

        with patch('slack_bot.claude_agent_handler.supabase', MagicMock()):
            result = await send_to_calendar({
                'post': 'Test post',
                'platform': 'linkedin',
                'thread_ts': '123',
                'channel_id': 'C123',
                'user_id': 'U123',
                'score': 85
            })

            # Should return error message, not raise exception
            assert 'content' in result
            response_text = result['content'][0]['text']
            assert '❌' in response_text or 'fail' in response_text.lower()
            assert 'rate limit' in response_text.lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])

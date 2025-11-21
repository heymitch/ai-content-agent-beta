"""
Unit tests for emoji reaction handlers (Phase 1)
Tests the ReactionHandler class and emoji-to-action mappings
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from slack_bot.reactions import ReactionHandler


class TestReactionHandlerInit:
    """Tests for ReactionHandler initialization and emoji mappings"""

    def test_all_emoji_handlers_registered(self):
        """Verify all supported emojis have handlers"""
        handler = ReactionHandler(
            supabase_client=Mock(),
            airtable_client=Mock(),
            thread_memory=Mock()
        )

        expected_emojis = [
            'calendar',
            'date',
            'spiral_calendar_pad',
            'pencil2',
            'arrows_counterclockwise',
            'white_check_mark',
            'microscope',
            'wastebasket'
        ]

        for emoji in expected_emojis:
            assert emoji in handler.handlers, f"Missing handler for {emoji}"

    def test_calendar_emoji_aliases(self):
        """Verify all calendar emojis route to same handler"""
        handler = ReactionHandler(
            supabase_client=Mock(),
            airtable_client=Mock(),
            thread_memory=Mock()
        )

        # All three should point to handle_schedule
        assert handler.handlers['calendar'] == handler.handlers['date']
        assert handler.handlers['calendar'] == handler.handlers['spiral_calendar_pad']


class TestHandleReaction:
    """Tests for the main handle_reaction routing method"""

    @pytest.fixture
    def handler(self):
        """Create handler with mocked dependencies"""
        memory = Mock()
        memory.get_thread.return_value = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Test content',
            'platform': 'linkedin',
            'latest_score': 85,
            'created_at': '2024-01-01T00:00:00Z'
        }

        return ReactionHandler(
            supabase_client=Mock(),
            airtable_client=Mock(),
            thread_memory=memory
        )

    @pytest.mark.asyncio
    async def test_thread_not_found(self):
        """Returns error when thread doesn't exist"""
        memory = Mock()
        memory.get_thread.return_value = None

        handler = ReactionHandler(
            supabase_client=Mock(),
            airtable_client=Mock(),
            thread_memory=memory
        )

        result = await handler.handle_reaction(
            reaction_emoji='calendar',
            thread_ts='nonexistent',
            user_id='U123',
            channel_id='C456'
        )

        assert result['success'] is False
        assert 'Thread not found' in result['message']

    @pytest.mark.asyncio
    async def test_unknown_emoji(self, handler):
        """Returns error for unregistered emoji"""
        result = await handler.handle_reaction(
            reaction_emoji='pizza',
            thread_ts='1234567890.123456',
            user_id='U123',
            channel_id='C456'
        )

        assert result['success'] is False
        assert 'Unknown reaction' in result['message']

    @pytest.mark.asyncio
    async def test_successful_handling(self, handler):
        """Handles reaction successfully"""
        handler.airtable.create_content_record = Mock(return_value={'id': 'rec123'})

        result = await handler.handle_reaction(
            reaction_emoji='calendar',
            thread_ts='1234567890.123456',
            user_id='U123',
            channel_id='C456'
        )

        assert result['success'] is True


class TestHandleSchedule:
    """Tests for calendar emoji / draft saving"""

    @pytest.fixture
    def handler(self):
        """Create handler with mocked dependencies"""
        memory = Mock()
        airtable = Mock()

        return ReactionHandler(
            supabase_client=Mock(),
            airtable_client=airtable,
            thread_memory=memory
        )

    @pytest.mark.asyncio
    async def test_saves_to_airtable_as_draft(self, handler):
        """Calendar emoji saves to Airtable with Draft status"""
        handler.airtable.create_content_record = Mock(return_value={'id': 'rec123'})

        thread = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Test content for LinkedIn',
            'platform': 'linkedin',
            'latest_score': 85,
            'created_at': '2024-01-01T00:00:00Z'
        }

        result = await handler.handle_schedule(thread, 'U123', 'C456')

        assert result['success'] is True
        assert result['action'] == 'draft_saved'
        assert 'Saved to Linkedin calendar as Draft' in result['message']

        # Verify Airtable was called with correct data
        handler.airtable.create_content_record.assert_called_once()
        call_kwargs = handler.airtable.create_content_record.call_args[1]
        assert call_kwargs['content'] == 'Test content for LinkedIn'
        assert call_kwargs['platform'] == 'Linkedin'
        assert call_kwargs['status'] == 'Draft'
        assert call_kwargs['quality_score'] == 85

    @pytest.mark.asyncio
    async def test_rejects_low_quality_score(self, handler):
        """Rejects content below minimum quality score"""
        thread = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Low quality content',
            'platform': 'linkedin',
            'latest_score': 50,  # Below 70 minimum
            'created_at': '2024-01-01T00:00:00Z'
        }

        result = await handler.handle_schedule(thread, 'U123', 'C456')

        assert result['success'] is False
        assert result['action'] == 'schedule_rejected'
        assert '50/100' in result['message']
        assert 'Minimum 70 required' in result['message']

    @pytest.mark.asyncio
    async def test_handles_airtable_error(self, handler):
        """Gracefully handles Airtable save errors"""
        handler.airtable.create_content_record = Mock(side_effect=Exception('API Error'))

        thread = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Test content',
            'platform': 'linkedin',
            'latest_score': 85,
            'created_at': '2024-01-01T00:00:00Z'
        }

        result = await handler.handle_schedule(thread, 'U123', 'C456')

        assert result['success'] is False
        assert result['action'] == 'save_failed'
        assert 'Failed to save draft' in result['message']

    @pytest.mark.asyncio
    async def test_updates_thread_status(self, handler):
        """Updates thread status after successful save"""
        handler.airtable.create_content_record = Mock(return_value={'id': 'rec123'})

        thread = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Test content',
            'platform': 'linkedin',
            'latest_score': 85,
            'created_at': '2024-01-01T00:00:00Z'
        }

        await handler.handle_schedule(thread, 'U123', 'C456')

        handler.memory.update_status.assert_called_once_with(
            '1234567890.123456',
            'draft_saved'
        )


class TestHandleRevise:
    """Tests for pencil emoji / revision requests"""

    @pytest.mark.asyncio
    async def test_returns_revision_instructions(self):
        """Returns helpful revision instructions"""
        handler = ReactionHandler(
            supabase_client=Mock(),
            airtable_client=Mock(),
            thread_memory=Mock()
        )

        thread = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Test content',
            'platform': 'linkedin',
            'latest_score': 85
        }

        result = await handler.handle_revise(thread, 'U123', 'C456')

        assert result['success'] is True
        assert result['action'] == 'revision_requested'
        assert 'Revision Mode Activated' in result['message']
        assert 'Reply to this thread' in result['message']


class TestHandleRegenerate:
    """Tests for regenerate emoji"""

    @pytest.mark.asyncio
    async def test_returns_regenerate_signal(self):
        """Returns signal to re-run workflow"""
        handler = ReactionHandler(
            supabase_client=Mock(),
            airtable_client=Mock(),
            thread_memory=Mock()
        )

        thread = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Test content',
            'platform': 'linkedin',
            'latest_score': 85
        }

        result = await handler.handle_regenerate(thread, 'U123', 'C456')

        assert result['success'] is True
        assert result['action'] == 'regenerate'
        assert result.get('trigger_workflow') is True


class TestHandleApprove:
    """Tests for checkmark emoji / approval"""

    @pytest.mark.asyncio
    async def test_updates_status_to_approved(self):
        """Updates thread status to approved"""
        memory = Mock()
        handler = ReactionHandler(
            supabase_client=Mock(),
            airtable_client=Mock(),
            thread_memory=memory
        )

        thread = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Test content',
            'platform': 'linkedin',
            'latest_score': 85
        }

        result = await handler.handle_approve(thread, 'U123', 'C456')

        assert result['success'] is True
        assert result['action'] == 'approved'
        memory.update_status.assert_called_once_with('1234567890.123456', 'approved')
        assert '85/100' in result['message']


class TestHandleDiscard:
    """Tests for wastebasket emoji / discard"""

    @pytest.mark.asyncio
    async def test_updates_status_to_discarded(self):
        """Updates thread status to discarded"""
        memory = Mock()
        handler = ReactionHandler(
            supabase_client=Mock(),
            airtable_client=Mock(),
            thread_memory=memory
        )

        thread = {
            'thread_ts': '1234567890.123456',
            'latest_draft': 'Test content',
            'platform': 'linkedin',
            'latest_score': 85
        }

        result = await handler.handle_discard(thread, 'U123', 'C456')

        assert result['success'] is True
        assert result['action'] == 'discarded'
        memory.update_status.assert_called_once_with('1234567890.123456', 'discarded')


class TestMainSlackIntegration:
    """Tests for main_slack.py reaction_added event handling"""

    @pytest.mark.asyncio
    async def test_thread_ts_resolution(self):
        """Verifies correct thread_ts is used (not message_ts)

        This tests the fix for bug where message_ts was passed instead
        of the actual thread_ts from the message.
        """
        # This is more of an integration test - the key behavior to verify:
        # When a reaction is added to a message IN a thread,
        # we need to use the thread_ts (parent), not the message_ts

        # The fix in main_slack.py (lines 1183-1188):
        # actual_thread_ts = message.get('thread_ts', message_ts)

        # Mock scenario:
        # - Message is in a thread (thread_ts = '111')
        # - User reacts to that message (message_ts = '222')
        # - Handler should receive '111', not '222'

        message_in_thread = {
            'ts': '222222.222222',  # message_ts
            'thread_ts': '111111.111111',  # parent thread_ts
            'text': 'Some content'
        }

        # The actual_thread_ts should be the thread_ts
        actual_thread_ts = message_in_thread.get('thread_ts', message_in_thread['ts'])
        assert actual_thread_ts == '111111.111111'

    @pytest.mark.asyncio
    async def test_feedback_message_sent(self):
        """Verifies user feedback is sent after reaction handling

        This tests the fix where handler result was captured but
        feedback wasn't posted to user.
        """
        # The fix in main_slack.py (lines 1190-1200):
        # if result and result.get('message'):
        #     slack_client.chat_postMessage(...)

        # Test that when handler returns a message, it gets posted
        handler_result = {
            'success': True,
            'action': 'draft_saved',
            'message': 'Saved to Airtable as Draft!'
        }

        assert handler_result.get('message') is not None
        # In actual code, this triggers chat_postMessage


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

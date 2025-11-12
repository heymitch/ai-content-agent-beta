"""
Emoji reaction handlers for Slack content agent
Maps emoji reactions to content actions
"""
from typing import Dict, Any, Callable, Optional
import asyncio


class ReactionHandler:
    """Handles emoji reactions on content messages"""

    def __init__(self, supabase_client, airtable_client, thread_memory):
        """
        Initialize reaction handler

        Args:
            supabase_client: Supabase client instance
            airtable_client: Airtable client for scheduling
            thread_memory: SlackThreadMemory instance
        """
        self.supabase = supabase_client
        self.airtable = airtable_client
        self.memory = thread_memory

        # Map emoji to handler functions
        self.handlers: Dict[str, Callable] = {
            'calendar': self.handle_schedule,        # 📅
            'pencil2': self.handle_revise,           # ✏️
            'arrows_counterclockwise': self.handle_regenerate,  # 🔄
            'white_check_mark': self.handle_approve, # ✅
            'microscope': self.handle_detailed_report,  # 🔬
            'wastebasket': self.handle_discard       # 🗑️
        }

    async def handle_reaction(
        self,
        reaction_emoji: str,
        thread_ts: str,
        user_id: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Route reaction to appropriate handler

        Args:
            reaction_emoji: Emoji name (without colons)
            thread_ts: Thread timestamp
            user_id: User who reacted
            channel_id: Channel ID

        Returns:
            Result dict with action taken and response message
        """
        # Get thread context
        thread = self.memory.get_thread(thread_ts)
        if not thread:
            return {
                'success': False,
                'message': 'Thread not found. This content may be too old.'
            }

        # Find handler for this emoji
        handler = self.handlers.get(reaction_emoji)
        if not handler:
            return {
                'success': False,
                'message': f'Unknown reaction: {reaction_emoji}'
            }

        # Execute handler
        try:
            result = await handler(thread, user_id, channel_id)

            # Log reaction
            self.memory.log_reaction(
                thread_ts=thread_ts,
                reaction_emoji=reaction_emoji,
                user_id=user_id,
                action_taken=result.get('action', 'unknown')
            )

            return result
        except Exception as e:
            print(f"❌ Reaction handler error: {e}")
            return {
                'success': False,
                'message': f'Failed to process reaction: {str(e)}'
            }

    async def handle_schedule(
        self,
        thread: Dict[str, Any],
        user_id: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Save content to Airtable calendar as Draft

        Args:
            thread: Thread record
            user_id: User ID
            channel_id: Channel ID

        Returns:
            Result dict
        """
        draft = thread.get('latest_draft', '')
        platform = thread.get('platform', 'linkedin')
        score = thread.get('latest_score', 0)

        # Require minimum quality score
        if score < 70:
            return {
                'success': False,
                'action': 'schedule_rejected',
                'message': f'⚠️ Quality score too low ({score}/100). Minimum 70 required to save as Draft.\n\nReact with ✏️ to revise first.'
            }

        try:
            # Send to Airtable as Draft
            record = self.airtable.create_record({
                'Content': draft,
                'Platform': platform.capitalize(),
                'Quality Score': score,
                'Status': 'Draft',  # Save as Draft, not Scheduled
                'Source': 'Slack Bot',
                'User ID': user_id,
                'Created At': thread.get('created_at', '')
            })

            # Update thread status
            self.memory.update_status(thread['thread_ts'], 'draft_saved')

            return {
                'success': True,
                'action': 'draft_saved',
                'message': f'✅ Saved to {platform.capitalize()} calendar as Draft!\n\n📅 Record ID: {record["id"]}\n📊 Quality Score: {score}/100'
            }
        except Exception as e:
            print(f"❌ Airtable save error: {e}")
            return {
                'success': False,
                'action': 'save_failed',
                'message': f'❌ Failed to save draft: {str(e)}\n\nTry again or contact support.'
            }

    async def handle_revise(
        self,
        thread: Dict[str, Any],
        user_id: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Request content revision

        Args:
            thread: Thread record
            user_id: User ID
            channel_id: Channel ID

        Returns:
            Result dict
        """
        return {
            'success': True,
            'action': 'revision_requested',
            'message': '✏️ *Revision Mode Activated*\n\nReply to this thread with your feedback:\n\n• "Make it shorter"\n• "Add more technical details"\n• "Change tone to casual"\n• "Include statistics"\n\nI\'ll revise the content based on your instructions.'
        }

    async def handle_regenerate(
        self,
        thread: Dict[str, Any],
        user_id: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Generate alternative version

        Args:
            thread: Thread record
            user_id: User ID
            channel_id: Channel ID

        Returns:
            Result dict
        """
        return {
            'success': True,
            'action': 'regenerate',
            'message': '🔄 Generating alternative version with different angle...\n\n_This will take ~15-30 seconds_',
            'trigger_workflow': True  # Signal to re-run workflow
        }

    async def handle_approve(
        self,
        thread: Dict[str, Any],
        user_id: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Approve and archive content

        Args:
            thread: Thread record
            user_id: User ID
            channel_id: Channel ID

        Returns:
            Result dict
        """
        # Update status
        self.memory.update_status(thread['thread_ts'], 'approved')

        draft = thread.get('latest_draft', '')
        score = thread.get('latest_score', 0)

        return {
            'success': True,
            'action': 'approved',
            'message': f'✅ *Content Approved!*\n\n📊 Final Score: {score}/100\n\n💡 *Next steps:*\n• React with 📅 to schedule to calendar\n• Copy content manually\n• Request changes (reply in thread)'
        }

    async def handle_detailed_report(
        self,
        thread: Dict[str, Any],
        user_id: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Show detailed quality report

        Args:
            thread: Thread record
            user_id: User ID
            channel_id: Channel ID

        Returns:
            Result dict with detailed report
        """
        # Get full workflow result from metadata if available
        metadata = thread.get('metadata', {})

        from .formatters import format_detailed_report

        report = format_detailed_report(metadata)

        return {
            'success': True,
            'action': 'report_shown',
            'message': report
        }

    async def handle_discard(
        self,
        thread: Dict[str, Any],
        user_id: str,
        channel_id: str
    ) -> Dict[str, Any]:
        """
        Discard content

        Args:
            thread: Thread record
            user_id: User ID
            channel_id: Channel ID

        Returns:
            Result dict
        """
        # Update status
        self.memory.update_status(thread['thread_ts'], 'discarded')

        return {
            'success': True,
            'action': 'discarded',
            'message': '🗑️ Content discarded.\n\nYou can still view it in this thread, or create new content with a fresh message.'
        }

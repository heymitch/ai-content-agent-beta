"""
Thread memory management for Slack conversations
Stores thread_id -> content mapping in Supabase
"""
from typing import Optional, Dict, Any
from datetime import datetime
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def retry_on_network_error(max_attempts=3, initial_delay=1.0, backoff_factor=2.0):
    """
    Decorator to retry operations on network errors with exponential backoff.

    Handles transient network failures like DNS resolution errors, connection timeouts, etc.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)

    Returns:
        Wrapped function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_type = type(e).__name__

                    # Check if this is a network-related error
                    is_network_error = (
                        'ConnectError' in error_type or
                        'ConnectionError' in error_type or
                        'TimeoutError' in error_type or
                        'Timeout' in error_type or
                        'NetworkError' in error_type or
                        'Name or service not known' in str(e) or
                        'Connection refused' in str(e) or
                        'Connection reset' in str(e)
                    )

                    if not is_network_error:
                        # Not a network error - don't retry
                        logger.error(f"Non-network error in {func.__name__}: {e}")
                        raise

                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"🔄 Network error in {func.__name__} (attempt {attempt + 1}/{max_attempts}): {e}"
                        )
                        logger.info(f"   Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_attempts} attempts: {e}"
                        )

            # All attempts failed
            raise last_exception

        return wrapper
    return decorator


class SlackThreadMemory:
    """Manages conversation state for Slack threads"""

    def __init__(self, supabase_client):
        """
        Initialize thread memory

        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client

    def create_thread(
        self,
        thread_ts: str,
        channel_id: str,
        user_id: str,
        platform: str,
        initial_draft: str = "",
        initial_score: int = 0
    ) -> Dict[str, Any]:
        """
        Create new thread record

        Args:
            thread_ts: Slack thread timestamp (unique ID)
            channel_id: Slack channel ID
            user_id: Slack user ID
            platform: Content platform (linkedin, twitter, email)
            initial_draft: First draft content
            initial_score: Initial quality score

        Returns:
            Created thread record
        """
        thread_data = {
            'thread_ts': thread_ts,
            'channel_id': channel_id,
            'user_id': user_id,
            'platform': platform,
            'latest_draft': initial_draft,
            'latest_score': initial_score,
            'status': 'drafting',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            result = self.supabase.table('slack_threads').insert(thread_data).execute()
            return result.data[0] if result.data else thread_data
        except Exception as e:
            print(f"⚠️ Failed to create thread record: {e}")
            return thread_data

    def get_thread(self, thread_ts: str) -> Optional[Dict[str, Any]]:
        """
        Get thread by timestamp

        Args:
            thread_ts: Slack thread timestamp

        Returns:
            Thread record or None
        """
        try:
            result = self.supabase.table('slack_threads')\
                .select('*')\
                .eq('thread_ts', thread_ts)\
                .execute()

            return result.data[0] if result.data else None
        except Exception as e:
            print(f"⚠️ Failed to get thread: {e}")
            return None

    def update_draft(
        self,
        thread_ts: str,
        draft: str,
        score: int,
        workflow_result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update thread with new draft and score

        Args:
            thread_ts: Slack thread timestamp
            draft: Updated draft content
            score: Updated quality score
            workflow_result: Full workflow result (optional, for metadata)

        Returns:
            Success boolean
        """
        update_data = {
            'latest_draft': draft,
            'latest_score': score,
            'updated_at': datetime.utcnow().isoformat()
        }

        # Store full workflow result as metadata if provided
        if workflow_result:
            update_data['metadata'] = workflow_result

        try:
            self.supabase.table('slack_threads')\
                .update(update_data)\
                .eq('thread_ts', thread_ts)\
                .execute()
            return True
        except Exception as e:
            print(f"⚠️ Failed to update thread: {e}")
            return False

    def update_status(self, thread_ts: str, status: str) -> bool:
        """
        Update thread status

        Args:
            thread_ts: Slack thread timestamp
            status: New status (drafting, approved, scheduled, discarded)

        Returns:
            Success boolean
        """
        try:
            self.supabase.table('slack_threads')\
                .update({
                    'status': status,
                    'updated_at': datetime.utcnow().isoformat()
                })\
                .eq('thread_ts', thread_ts)\
                .execute()
            return True
        except Exception as e:
            print(f"⚠️ Failed to update status: {e}")
            return False

    def get_user_threads(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """
        Get threads for a user

        Args:
            user_id: Slack user ID
            status: Filter by status (optional)
            limit: Max number of threads to return

        Returns:
            List of thread records
        """
        try:
            query = self.supabase.table('slack_threads')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .limit(limit)

            if status:
                query = query.eq('status', status)

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"⚠️ Failed to get user threads: {e}")
            return []

    def log_reaction(
        self,
        thread_ts: str,
        reaction_emoji: str,
        user_id: str,
        action_taken: str
    ) -> bool:
        """
        Log emoji reaction and action taken

        Args:
            thread_ts: Slack thread timestamp
            reaction_emoji: Emoji that was reacted
            user_id: User who reacted
            action_taken: Description of action performed

        Returns:
            Success boolean
        """
        reaction_data = {
            'thread_ts': thread_ts,
            'reaction_emoji': reaction_emoji,
            'user_id': user_id,
            'action_taken': action_taken,
            'created_at': datetime.utcnow().isoformat()
        }

        try:
            self.supabase.table('slack_reactions').insert(reaction_data).execute()
            return True
        except Exception as e:
            print(f"⚠️ Failed to log reaction: {e}")
            return False

    def get_recent_scheduled(self, days: int = 7) -> list:
        """
        Get recently scheduled content

        Args:
            days: Number of days to look back

        Returns:
            List of scheduled content
        """
        try:
            from datetime import timedelta
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

            result = self.supabase.table('slack_threads')\
                .select('*')\
                .eq('status', 'scheduled')\
                .gte('updated_at', cutoff)\
                .order('updated_at', desc=True)\
                .execute()

            return result.data if result.data else []
        except Exception as e:
            print(f"⚠️ Failed to get scheduled content: {e}")
            return []

    def add_message(
        self,
        thread_ts: str,
        channel_id: str,
        user_id: str,
        role: str,
        content: str
    ) -> bool:
        """
        Add a message to conversation history

        Args:
            thread_ts: Slack thread timestamp
            channel_id: Slack channel ID
            user_id: User ID (or 'bot')
            role: Message role ('user' or 'assistant')
            content: Message content

        Returns:
            Success boolean
        """
        message_data = {
            'thread_ts': thread_ts,
            'channel_id': channel_id,
            'user_id': user_id,
            'role': role,
            'content': content,
            'created_at': datetime.utcnow().isoformat()
        }

        @retry_on_network_error(max_attempts=3, initial_delay=1.0, backoff_factor=2.0)
        def _insert_with_retry():
            """Inner function with retry logic for network errors"""
            return self.supabase.table('conversation_history').insert(message_data).execute()

        try:
            result = _insert_with_retry()
            print(f"✅ Message saved to conversation_history (thread: {thread_ts[:8]}...)")
            return True
        except Exception as e:
            # Even after retries, still failed - log but don't crash the agent
            print(f"❌ FAILED to save message to conversation_history after retries!")
            print(f"   Error: {e}")
            print(f"   Thread: {thread_ts}")
            print(f"   Role: {role}")
            print(f"   Content length: {len(content)} chars")
            import traceback
            traceback.print_exc()
            # Return False but don't crash - agent can continue without saving history
            return False

    def get_thread_history(self, thread_ts: str, limit: int = 50) -> list:
        """
        Get conversation history for a thread

        Args:
            thread_ts: Slack thread timestamp
            limit: Max messages to return

        Returns:
            List of messages in chronological order
        """
        try:
            result = self.supabase.table('conversation_history')\
                .select('*')\
                .eq('thread_ts', thread_ts)\
                .order('created_at', desc=False)\
                .limit(limit)\
                .execute()

            return result.data if result.data else []
        except Exception as e:
            print(f"⚠️ Failed to get thread history: {e}")
            return []

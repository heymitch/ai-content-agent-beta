"""
Supabase client singleton for database operations
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client singleton"""
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY in .env")

        _supabase_client = create_client(supabase_url, supabase_key)

    return _supabase_client

def is_bot_participating_in_thread(thread_ts: str, channel_id: str = None, ttl_hours: int = 24) -> bool:
    """
    Check if bot has participated in a thread recently (within TTL).

    Args:
        thread_ts: Slack thread timestamp
        channel_id: Optional channel ID for additional filtering
        ttl_hours: How far back to look for bot participation (default 24 hours)

    Returns:
        True if bot has sent a message in this thread within the TTL period
    """
    try:
        client = get_supabase_client()
        cutoff_time = datetime.utcnow() - timedelta(hours=ttl_hours)

        # Query for assistant messages in this thread within TTL
        query = client.table('conversation_history') \
            .select('id') \
            .eq('thread_ts', thread_ts) \
            .eq('role', 'assistant') \
            .gte('created_at', cutoff_time.isoformat()) \
            .limit(1)

        # Optionally filter by channel_id
        if channel_id:
            query = query.eq('channel_id', channel_id)

        result = query.execute()

        # If we found any assistant messages, bot is participating
        return len(result.data) > 0

    except Exception as e:
        print(f"⚠️ Error checking thread participation: {e}")
        # Fail open: if we can't check, assume not participating
        return False

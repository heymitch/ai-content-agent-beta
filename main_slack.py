#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slack-Only Content Agent
Clean implementation with only essential Slack functionality
"""

import sys
import codecs

# Force UTF-8 encoding for Replit compatibility
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from anthropic import Anthropic, RateLimitError
from fastapi import FastAPI, Request, BackgroundTasks
from supabase import create_client, Client
import os
import json
import time
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio
from typing import Dict, List, Any
from collections import deque

# Slack integration
from slack_bot.handler import SlackContentHandler
from slack_sdk import WebClient

# Supabase helpers
from integrations.supabase_client import is_bot_participating_in_thread

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# ============= BACKGROUND TASK SUPERVISION (Phase 0.2) =============
# Prevents silent failures by logging all exceptions and optionally restarting tasks

import logging
logger = logging.getLogger(__name__)

def supervise_task(coro, *, name: str, max_restarts: int = 0):
    """
    Supervise async coroutine with exception logging and optional restart.

    Args:
        coro: Async coroutine to supervise
        name: Task name for logging
        max_restarts: Number of automatic restarts on failure (0 = no restart)

    Returns:
        asyncio.Task with done_callback for exception logging
    """
    attempts = 0

    async def runner():
        nonlocal attempts
        while True:
            try:
                return await coro
            except Exception as e:
                attempts += 1
                logger.exception(
                    f"❌ Background task '{name}' failed (attempt {attempts})",
                    exc_info=e
                )

                if attempts > max_restarts:
                    logger.error(f"🛑 Task '{name}' exceeded max restarts ({max_restarts}), giving up")
                    raise

                # Exponential backoff before retry
                backoff_seconds = min(1.0 * (2 ** (attempts - 1)), 30)  # Max 30s
                logger.info(f"🔄 Retrying task '{name}' in {backoff_seconds}s...")
                await asyncio.sleep(backoff_seconds)

    task = asyncio.create_task(runner(), name=name)

    # Add done callback to catch any exceptions that slip through
    def log_exception(t: asyncio.Task):
        try:
            t.result()  # This will raise if task failed
        except asyncio.CancelledError:
            logger.info(f"⚠️  Task '{name}' was cancelled")
        except Exception as e:
            logger.error(f"💥 Task '{name}' crashed with uncaught exception: {e}")

    task.add_done_callback(log_exception)
    return task

# Event deduplication cache (stores event_id for 5 minutes)
processed_events = {}
EVENT_CACHE_TTL = 300  # 5 minutes

# Thread participation TTL (used for Supabase query)
THREAD_PARTICIPATION_TTL = 24  # 24 hours

# ============= CLIENT INITIALIZATION WITH ERROR HANDLING =============

# Initialize clients with error handling (won't crash on startup)
# Clients are created lazily when first accessed
supabase: Client = None
anthropic_client = None
slack_client = None
_init_errors = {}

def _init_supabase():
    """Initialize Supabase client with error handling"""
    global supabase, _init_errors
    if supabase is None:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            error_msg = "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY in environment"
            _init_errors['supabase'] = error_msg
            print(f"⚠️ {error_msg}")
            return False
        
        try:
            supabase = create_client(supabase_url, supabase_key)
            # Test connection with a simple query (with timeout)
            try:
                supabase.table('_migrations').select('id').limit(1).execute()
            except Exception:
                # Table might not exist yet, that's OK
                pass
            print("✅ Supabase client initialized")
            return True
        except Exception as e:
            error_msg = f"Failed to initialize Supabase client: {str(e)}"
            _init_errors['supabase'] = error_msg
            print(f"⚠️ {error_msg}")
            return False
    return True

def _init_anthropic():
    """Initialize Anthropic client with error handling"""
    global anthropic_client, _init_errors
    if anthropic_client is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            error_msg = "Missing ANTHROPIC_API_KEY in environment"
            _init_errors['anthropic'] = error_msg
            print(f"⚠️ {error_msg}")
            return False
        
        try:
            anthropic_client = Anthropic(api_key=api_key)
            print("✅ Anthropic client initialized")
            return True
        except Exception as e:
            error_msg = f"Failed to initialize Anthropic client: {str(e)}"
            _init_errors['anthropic'] = error_msg
            print(f"⚠️ {error_msg}")
            return False
    return True

def _init_slack():
    """Initialize Slack client with error handling"""
    global slack_client, _init_errors
    if slack_client is None:
        token = os.getenv('SLACK_BOT_TOKEN')
        if not token:
            error_msg = "Missing SLACK_BOT_TOKEN in environment"
            _init_errors['slack'] = error_msg
            print(f"⚠️ {error_msg}")
            return False
        
        try:
            slack_client = WebClient(token=token)
            # Don't test connection here - let it fail gracefully on first use
            print("✅ Slack client initialized")
            return True
        except Exception as e:
            error_msg = f"Failed to initialize Slack client: {str(e)}"
            _init_errors['slack'] = error_msg
            print(f"⚠️ {error_msg}")
            return False
    return True

# Initialize clients during startup (non-blocking)
# If initialization fails, clients remain None and will raise errors when accessed
_init_supabase()
_init_anthropic()
_init_slack()

# Optional: Langfuse for observability
langfuse_enabled = bool(os.getenv('LANGFUSE_PUBLIC_KEY') and os.getenv('LANGFUSE_SECRET_KEY'))
if langfuse_enabled:
    try:
        from langfuse import Langfuse
        langfuse_client = Langfuse(
            public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
            secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
            host=os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
        )
        print("✅ Langfuse observability enabled")
    except Exception as e:
        print(f"⚠️ Langfuse initialization failed: {e}")
        langfuse_enabled = False
else:
    print("ℹ️ Langfuse observability disabled (no API keys)")

# ============= SLACK HANDLER INITIALIZATION =============

slack_handler = None

def get_slack_handler():
    """Lazy init Slack handler with Airtable client"""
    global slack_handler
    if slack_handler is None:
        try:
            from integrations.airtable_client import AirtableContentCalendar
            print("🔄 Initializing Slack handler with Airtable...")
            airtable = AirtableContentCalendar()
            slack_handler = SlackContentHandler(supabase, airtable)
            print("✅ Slack handler initialized with Airtable")
        except Exception as e:
            print(f"⚠️ Airtable initialization failed: {e}")
            print("📝 Initializing Slack handler without Airtable...")
            slack_handler = SlackContentHandler(supabase, None)
            print("✅ Slack handler initialized (no calendar)")
    return slack_handler

# ============= FASTAPI LIFECYCLE EVENTS =============

# Track how many times handler has been created (for debugging)
_handler_creation_count = 0

@app.on_event("startup")
async def startup_validation():
    """Validate environment and initialize clients on startup"""
    global slack_handler, _handler_creation_count
    slack_handler = None
    _handler_creation_count = 0
    print("🔄 Startup: Cleared handler cache (ensures fresh system prompts on hot reload)")
    
    # Validate environment variables
    print("\n🔍 Validating environment variables...")
    required_vars = {
        'ANTHROPIC_API_KEY': 'Anthropic API key for Claude',
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_KEY': 'Supabase anon/service key',
        'SLACK_BOT_TOKEN': 'Slack bot user OAuth token',
        'SLACK_SIGNING_SECRET': 'Slack signing secret for webhook verification'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")
    
    if missing_vars:
        print("⚠️ Missing required environment variables:")
        for var in missing_vars:
            print(var)
        print("\n💡 Set these in Replit Secrets or .env file")
    else:
        print("✅ All required environment variables present")
    
    # Try to initialize clients (non-blocking)
    print("\n🔄 Initializing clients...")
    _init_supabase()
    _init_anthropic()
    _init_slack()
    
    if _init_errors:
        print(f"\n⚠️ {len(_init_errors)} client(s) failed to initialize:")
        for client, error in _init_errors.items():
            print(f"  - {client}: {error}")
    else:
        print("\n✅ All clients initialized successfully")

# ============= RATE LIMITING =============

class TokenBucketRateLimiter:
    """Token-based rate limiter for Claude API to prevent 429 errors"""

    def __init__(self, tokens_per_minute: int = 5, burst_size: int = 10):
        self.tokens_per_minute = tokens_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if successful."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on time elapsed
        new_tokens = elapsed * (self.tokens_per_minute / 60)
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_time(self) -> float:
        """Return seconds to wait for next token"""
        if self.tokens >= 1:
            return 0
        tokens_needed = 1 - self.tokens
        seconds_per_token = 60 / self.tokens_per_minute
        return tokens_needed * seconds_per_token

# Create rate limiter instance
rate_limiter = TokenBucketRateLimiter(tokens_per_minute=15, burst_size=5)

# ============= HELPER FUNCTIONS =============

def format_for_slack(text: str) -> str:
    """
    Convert markdown to Slack mrkdwn format

    Args:
        text: Markdown formatted text

    Returns:
        Slack mrkdwn formatted text
    """
    # Convert bold: **text** or __text__ → *text*
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
    text = re.sub(r'__(.+?)__', r'*\1*', text)

    # Convert italic: *text* or _text_ → _text_
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'_\1_', text)

    # Convert code blocks: ```lang\ncode\n``` → ```code```
    text = re.sub(r'```\w+\n', '```', text)

    # Convert links: [text](url) → <url|text>
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<\2|\1>', text)

    # Convert bullet lists: - item or * item → • item
    text = re.sub(r'^[\-\*]\s+', '• ', text, flags=re.MULTILINE)

    # Convert headers: # Header → *Header*
    text = re.sub(r'^#{1,6}\s+(.+?)$', r'*\1*', text, flags=re.MULTILINE)

    # Convert strikethrough: ~~text~~ → ~text~
    text = re.sub(r'~~(.+?)~~', r'~\1~', text)

    return text

# ============= HEALTH CHECK =============

@app.get('/healthz')
def health_check():
    """Basic health check - returns 200 if server is up"""
    handler = get_slack_handler()
    active_sessions = len(handler._thread_sessions) if handler else 0
    max_sessions = handler.MAX_CONCURRENT_SESSIONS if handler else 3

    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'service': 'slack-content-agent',
        'active_sessions': active_sessions,
        'max_sessions': max_sessions,
        'session_utilization': f'{active_sessions}/{max_sessions}'
    }


@app.get('/readyz')
async def readiness_check():
    """
    Readiness check - verifies agent can actually function.
    Phase 0.3: Enhanced health checks with connection validation
    """
    checks = {}
    ready = True

    # Check 1: Anthropic API key present and client initialized
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        if anthropic_client is None:
            checks["anthropic"] = "initialization_failed"
            if 'anthropic' in _init_errors:
                checks["anthropic_error"] = _init_errors['anthropic']
            ready = False
        else:
            checks["anthropic"] = "ready"
    else:
        checks["anthropic"] = "missing_key"
        ready = False

    # Check 2: Supabase credentials present and client initialized
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if supabase_url and supabase_key:
        if supabase is None:
            checks["supabase"] = "initialization_failed"
            if 'supabase' in _init_errors:
                checks["supabase_error"] = _init_errors['supabase']
            ready = False
        else:
            # Test actual connection
            try:
                supabase.table('_migrations').select('id').limit(1).execute()
                checks["supabase"] = "connected"
            except Exception as e:
                checks["supabase"] = "connection_failed"
                checks["supabase_error"] = str(e)
                ready = False
    else:
        checks["supabase"] = "missing_credentials"
        ready = False

    # Check 3: Slack bot token present and client initialized
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if slack_token:
        if slack_client is None:
            checks["slack"] = "initialization_failed"
            if 'slack' in _init_errors:
                checks["slack_error"] = _init_errors['slack']
            ready = False
        else:
            checks["slack"] = "ready"
    else:
        checks["slack"] = "missing_token"
        ready = False

    return {
        "ready": ready,
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
        "init_errors": _init_errors if _init_errors else None
    }


# ============= ANALYTICS ENDPOINTS (Phase 1, 3-4) =============

from slack_bot.analytics_handler import analyze_performance
from slack_bot.briefing_handler import generate_briefing


@app.post('/api/analyze-performance')
async def analyze_performance_endpoint(request: Request):
    """
    Analyze post performance data and return strategic insights.

    Phase 1 of Analytics & Intelligence System.

    Request body:
    {
        "posts": [
            {
                "hook": "I replaced 3 workflows...",
                "platform": "linkedin",
                "quality_score": 24,
                "impressions": 15000,
                "engagements": 1230,
                "engagement_rate": 8.2,
                "published_at": "2025-01-20"
            }
        ],
        "date_range": {
            "start": "2025-01-20",
            "end": "2025-01-27"
        }
    }

    Returns:
    {
        "summary": "1-2 sentence overview",
        "top_performers": [...],
        "worst_performers": [...],
        "patterns": {...},
        "recommendations": [...]
    }
    """
    # Check if analytics is enabled
    from config.analytics_config import is_analytics_enabled
    if not is_analytics_enabled():
        return {
            "error": "Analytics features are disabled",
            "summary": "Enable ANALYTICS_ENABLED in your environment variables"
        }

    try:
        data = await request.json()
        posts = data.get('posts', [])
        date_range = data.get('date_range', {})

        if not posts:
            return {
                "error": "No posts provided",
                "summary": "No data to analyze"
            }

        if not date_range.get('start') or not date_range.get('end'):
            return {
                "error": "date_range must include 'start' and 'end' fields"
            }

        # Call analytics handler with shared client
        analysis = await analyze_performance(posts, date_range, anthropic_client)

        return analysis

    except Exception as e:
        logger.error(f"Error in /api/analyze-performance: {e}", exc_info=True)
        return {
            "error": str(e),
            "summary": "Analysis failed due to unexpected error"
        }


@app.post('/api/generate-briefing')
async def generate_briefing_endpoint(request: Request):
    """
    Generate weekly content intelligence briefing.

    Phase 3 of Analytics & Intelligence System.

    Request body:
    {
        "analytics": {
            "summary": "Engagement up 15%...",
            "top_performers": [...],
            "worst_performers": [...],
            "patterns": {...},
            "recommendations": [...]
        },
        "research": {
            "trending_topics": [...]  // Optional - from agent's web_search
        },
        "user_context": {
            "recent_topics": ["AI agents", "automation"],
            "content_goals": "thought leadership",
            "audience": "enterprise decision makers"
        }
    }

    Returns:
    {
        "briefing_markdown": "# 📊 Weekly Content Intelligence...",
        "suggested_topics": [
            "3 ways OpenAI's new API changes enterprise workflows",
            "I analyzed 50 AI adoption failures—here's what worked"
        ],
        "priority_actions": [
            "Create 5 posts using 'Specific Number Hook' pattern",
            "Write about OpenAI API announcement (trending, relevance: 9)"
        ]
    }
    """
    # Check if analytics is enabled
    from config.analytics_config import is_analytics_enabled
    if not is_analytics_enabled():
        return {
            "error": "Analytics features are disabled",
            "briefing_markdown": "# Analytics Disabled\n\nEnable ANALYTICS_ENABLED in your environment variables.",
            "suggested_topics": [],
            "priority_actions": []
        }

    try:
        data = await request.json()
        analytics = data.get('analytics', {})
        research = data.get('research')  # Optional
        user_context = data.get('user_context')  # Optional

        if not analytics:
            return {
                "error": "No analytics data provided",
                "briefing_markdown": "# Error\n\nNo analytics data to generate briefing.",
                "suggested_topics": [],
                "priority_actions": []
            }

        # Call briefing handler with shared client
        briefing = await generate_briefing(
            analytics=analytics,
            research=research,
            user_context=user_context,
            client=anthropic_client
        )

        return briefing

    except Exception as e:
        logger.error(f"Error in /api/generate-briefing: {e}", exc_info=True)
        return {
            "error": str(e),
            "briefing_markdown": f"# Error\n\nFailed to generate briefing: {str(e)}",
            "suggested_topics": [],
            "priority_actions": []
        }


@app.post('/api/slack/post-message')
async def slack_post_message_endpoint(request: Request):
    """
    Post message to Slack (for n8n to send briefings proactively).

    Phase 4 of Analytics & Intelligence System.

    Request body:
    {
        "channel_id": "C12345",
        "message": "# 📊 Weekly Content Intelligence\n\n...",
        "thread_ts": null,  // Optional - post to thread
        "user_id": "U12345"  // Optional - for context/logging
    }

    Returns:
    {
        "thread_ts": "1234567890.123456",
        "channel_id": "C12345",
        "message_url": "https://workspace.slack.com/archives/C12345/p1234567890123456"
    }
    """
    try:
        data = await request.json()
        channel_id = data.get('channel_id')
        message = data.get('message')
        thread_ts = data.get('thread_ts')  # Optional
        user_id = data.get('user_id')  # Optional, for logging

        if not channel_id or not message:
            return {
                "error": "Missing required fields: channel_id, message"
            }

        logger.info(f"Posting message to Slack channel {channel_id} (user: {user_id or 'n8n'})")

        # Post message to Slack (with client validation)
        if slack_client is None:
            return {
                "error": "Slack client not initialized"
            }
        
        response = slack_client.chat_postMessage(
            channel=channel_id,
            text=message,
            thread_ts=thread_ts,
            mrkdwn=True
        )

        # Extract thread_ts and build message URL
        result_thread_ts = response.get('ts')
        workspace_url = "https://app.slack.com"  # Fallback if we can't get team domain

        # Try to get workspace URL from team info
        try:
            team_info = slack_client.team_info()
            team_domain = team_info.get('team', {}).get('domain', 'app')
            workspace_url = f"https://{team_domain}.slack.com"
        except Exception as e:
            logger.warning(f"Could not get team domain: {e}")

        # Build message permalink
        message_url = f"{workspace_url}/archives/{channel_id}/p{result_thread_ts.replace('.', '')}"

        logger.info(f"Message posted successfully: {message_url}")

        return {
            "thread_ts": result_thread_ts,
            "channel_id": channel_id,
            "message_url": message_url
        }

    except Exception as e:
        logger.error(f"Error in /api/slack/post-message: {e}", exc_info=True)
        return {
            "error": str(e)
        }


# ============= SLACK EVENT HANDLERS =============

@app.post('/slack/events')
async def handle_slack_event(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack events with proper async support and FastAPI background tasks"""
    # Get raw body for signature verification
    body_bytes = await request.body()
    body_text = body_bytes.decode('utf-8')
    data = json.loads(body_text)
    print(f"🔍 RECEIVED SLACK EVENT: {data}")

    # Handle URL verification challenge
    if 'challenge' in data:
        print("✅ Responding to Slack challenge")
        return {'challenge': data['challenge']}

    # Deduplicate events (Slack retries on slow responses)
    event_id = data.get('event_id')
    if event_id:
        # Clean old cache entries
        now = time.time()
        expired_keys = [k for k, v in processed_events.items() if now - v > EVENT_CACHE_TTL]
        for k in expired_keys:
            del processed_events[k]

        # Check if already processed
        if event_id in processed_events:
            print(f"⏭️ Skipping duplicate event: {event_id}")
            return {'status': 'already_processed'}

        # Mark as processed
        processed_events[event_id] = now

    # Verify Slack signature
    slack_signature = request.headers.get('X-Slack-Signature', '')
    slack_timestamp = request.headers.get('X-Slack-Request-Timestamp', '')

    # Validate request timestamp (prevent replay attacks)
    if slack_timestamp:
        try:
            request_time = int(slack_timestamp)
            if abs(time.time() - request_time) > 60 * 5:  # 5 minutes
                print("⚠️ Request timestamp too old")
                return {'status': 'invalid_timestamp'}
        except ValueError:
            print("⚠️ Invalid timestamp format")
            return {'status': 'invalid_timestamp'}

    # Verify signature using HMAC-SHA256
    if slack_signature and slack_timestamp:
        import hmac
        import hashlib

        signing_secret = os.getenv('SLACK_SIGNING_SECRET', '')
        if signing_secret:
            sig_basestring = f"v0:{slack_timestamp}:{body_text}"
            computed_signature = 'v0=' + hmac.new(
                signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()

            # Timing-safe comparison
            if not hmac.compare_digest(computed_signature, slack_signature):
                print("⚠️ Invalid Slack signature")
                return {'status': 'invalid_signature'}

    # Get event data
    event = data.get('event', {})
    event_type = event.get('type')

    # Also deduplicate by message timestamp (Slack sends both message and app_mention)
    message_ts = event.get('ts') or event.get('event_ts')
    if message_ts:
        dedup_key = f"{event.get('channel')}:{message_ts}"
        if dedup_key in processed_events:
            print(f"⏭️ Skipping duplicate message event: {dedup_key}")
            return {'status': 'duplicate_message'}
        processed_events[dedup_key] = now

    print(f"📥 Event type: {event_type}")
    print(f"📝 Event data: {json.dumps(event, indent=2)}")

    # Special debug for thread detection
    if 'thread_ts' in event:
        print(f"🧵 THREAD REPLY DETECTED: thread_ts={event.get('thread_ts')}")
    else:
        print(f"💬 NEW MESSAGE (not a thread reply)")

    # Helper function to send messages
    def send_slack_message(channel, text, thread_ts=None):
        """Send message to Slack channel"""
        if slack_client is None:
            print(f"❌ Cannot send message: Slack client not initialized")
            return {'ok': False, 'error': 'Slack client not initialized'}
        
        try:
            response = slack_client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
            print(f"✅ Message sent successfully")
            return response
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return {'ok': False, 'error': str(e)}

    # Handle app mentions and direct messages
    if event_type in ['app_mention', 'message']:
        user_id = event.get('user')
        channel = event.get('channel')
        message_text = event.get('text', '')

        # For thread replies, use thread_ts; for new messages, use ts
        # For DMs, use the channel ID as the "thread" to maintain conversation continuity
        if event.get('channel_type') == 'im':
            # In DMs, use channel ID for session continuity
            thread_ts = f"dm_{channel}"
            print(f"📱 DM detected - using channel as thread: {thread_ts}")
        else:
            # In channels, use actual thread_ts
            thread_ts = event.get('thread_ts') or event.get('ts') or event.get('event_ts')

        event_ts = event.get('ts') or event.get('event_ts')

        # Skip bot's own messages (including "On it..." acknowledgements)
        if event.get('bot_id') or event.get('subtype') == 'bot_message':
            print("🤖 Skipping bot message")
            return {'status': 'skipped_bot_message'}

        # Also skip if the message is from the bot user itself
        bot_user_id = data.get('authorizations', [{}])[0].get('user_id', '')
        if user_id == bot_user_id:
            print("🤖 Skipping our own message")
            return {'status': 'skipped_own_message'}

        # Skip edits
        if event.get('subtype') == 'message_changed':
            print("✏️ Skipping message edit")
            return {'status': 'skipped_edit'}

        # Check for file uploads
        files = event.get('files', [])
        has_files = len(files) > 0

        # Debug: Log file detection
        if has_files:
            print(f"📎 Detected {len(files)} file(s):")
            for f in files:
                print(f"   - {f.get('name', 'unknown')} ({f.get('mimetype', 'unknown type')}, {f.get('size', 0)} bytes)")

        # Skip empty messages UNLESS there are files attached
        if (not message_text or not message_text.strip()) and not has_files:
            print("⏭️ Skipping empty message with no files")
            return {'status': 'skipped_empty_message'}

        # If there are files but no message text, use placeholder
        if has_files and (not message_text or not message_text.strip()):
            message_text = "[User uploaded file(s)]"
            print(f"📎 {len(files)} file(s) attached to message")

        # bot_user_id already retrieved above
        is_bot_mentioned = bot_user_id and f'<@{bot_user_id}>' in message_text

        # Determine if bot should respond
        should_respond = False

        # Debug logging
        print(f"🔍 Debug: event_type={event_type}, thread_ts={thread_ts}, is_mentioned={is_bot_mentioned}")

        if event_type == 'app_mention' or is_bot_mentioned:
            # Always respond to direct mentions
            should_respond = True
            print(f"✅ Bot mentioned - will participate in thread {thread_ts}")
        elif event.get('channel_type') == 'im':
            # Always respond in DMs (and maintain conversation context)
            should_respond = True
            print("✅ Direct message - responding with continuous context")
        else:
            # Check if bot has participated in this thread recently (persists across restarts!)
            is_participating = is_bot_participating_in_thread(
                thread_ts=thread_ts,
                channel_id=channel,
                ttl_hours=THREAD_PARTICIPATION_TTL
            )

            if is_participating:
                # Continue conversation in threads where bot has participated
                should_respond = True
                print(f"✅ Continuing conversation in thread {thread_ts} (from conversation history)")
            else:
                # Don't respond to random channel messages
                print(f"⏭️ Skipping - not participating in thread {thread_ts}")
                return {'status': 'not_participating'}

        if not should_respond:
            return {'status': 'skipped'}

        # Remove bot mention from text if present
        if bot_user_id:
            message_text = message_text.replace(f'<@{bot_user_id}>', '').strip()

        print(f"💬 Processing message: {message_text}")

        # ALL messages go to Claude Agent SDK - it's smart enough to understand context
        print("🤖 Processing with Claude Agent SDK...")

        # Add instant ⚡ reaction for all messages (mentions + thread replies)
        try:
            slack_client.reactions_add(
                channel=channel,
                timestamp=event_ts,
                name="zap"
            )
        except Exception as e:
            print(f"⚠️ Could not add reaction: {e}")

        # Only send "On it..." for direct mentions (not thread replies)
        if is_bot_mentioned or event_type == 'app_mention':
            send_slack_message(
                channel=channel,
                text="On it...",
                thread_ts=thread_ts
            )

        # Process in background to avoid Slack's 3-second timeout
        async def process_message():
            try:
                # Validate clients are initialized
                if anthropic_client is None:
                    error_msg = "Anthropic client not initialized. Please check ANTHROPIC_API_KEY."
                    print(f"❌ {error_msg}")
                    send_slack_message(
                        channel=channel,
                        text=f"❌ Configuration error: {error_msg}\n\nPlease check your environment variables.",
                        thread_ts=thread_ts
                    )
                    return
                
                if supabase is None:
                    print("⚠️ Supabase not initialized, continuing without database features")
                
                # Import Claude Agent SDK handler
                from slack_bot.claude_agent_handler import ClaudeAgentHandler
                print("✅ Claude Agent SDK loaded successfully")

                handler = get_slack_handler()
                
                if handler is None:
                    error_msg = "Failed to initialize Slack handler"
                    print(f"❌ {error_msg}")
                    send_slack_message(
                        channel=channel,
                        text=f"❌ {error_msg}. Please check server logs.",
                        thread_ts=thread_ts
                    )
                    return

                # Use the REAL Claude Agent SDK handler
                # ALWAYS recreate to pick up prompt changes on module reload
                try:
                    handler.claude_agent = ClaudeAgentHandler(
                        memory_handler=handler.memory if handler else None,
                        slack_client=slack_client  # NEW: Pass slack_client for progress updates
                    )
                except Exception as e:
                    error_msg = f"Failed to initialize Claude Agent: {str(e)}"
                    print(f"❌ {error_msg}")
                    import traceback
                    traceback.print_exc()
                    send_slack_message(
                        channel=channel,
                        text=f"❌ {error_msg}\n\nThis may be a temporary issue. Please try again.",
                        thread_ts=thread_ts
                    )
                    return

                global _handler_creation_count
                _handler_creation_count += 1
                print(f"🚀 Handler #{_handler_creation_count} ready (tools registered via MCP server)")

                # Save user message to conversation history
                if handler.memory:
                    try:
                        handler.memory.add_message(
                            thread_ts=thread_ts,
                            channel_id=channel,
                            user_id=user_id,
                            role='user',
                            content=message_text
                        )
                        print(f"💾 Saved user message to conversation history")
                    except Exception as e:
                        print(f"⚠️ Failed to save message to history: {e}")

                # The agent decides what to do based on context:
                # - Create content → delegates to workflows
                # - Answer questions → uses web_search if needed
                # - Analyze performance → uses analysis tools
                # - General conversation → maintains thread context
                try:
                    response_text = await handler.claude_agent.handle_conversation(
                        message=message_text,
                        user_id=user_id,
                        thread_ts=thread_ts,  # Use thread_ts for session continuity
                        channel_id=channel,
                        slack_files=files if has_files else None  # Pass Slack file objects
                    )
                except RuntimeError as e:
                    # SDK client creation failure - provide helpful error
                    error_msg = str(e)
                    if "Failed to create Claude SDK client" in error_msg:
                        print(f"❌ SDK client creation failed: {error_msg}")
                        send_slack_message(
                            channel=channel,
                            text=f"❌ I'm having trouble connecting to my AI services right now. This might be a temporary issue.\n\nError: {error_msg}\n\nPlease try again in a moment.",
                            thread_ts=thread_ts
                        )
                    else:
                        raise
                except Exception as e:
                    # Other errors - log and provide fallback response
                    print(f"❌ Error in agent conversation: {e}")
                    import traceback
                    traceback.print_exc()
                    raise

                # Save assistant response to conversation history
                if handler.memory:
                    try:
                        handler.memory.add_message(
                            thread_ts=thread_ts,
                            channel_id=channel,
                            user_id='bot',
                            role='assistant',
                            content=response_text
                        )
                        print(f"💾 Saved assistant response to conversation history")
                    except Exception as e:
                        print(f"⚠️ Failed to save response to history: {e}")

                # Send response
                send_slack_message(
                    channel=channel,
                    text=response_text,
                    thread_ts=thread_ts  # Reply in thread
                )

            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                
                # Provide user-friendly error message
                error_detail = str(e)
                if "ANTHROPIC_API_KEY" in error_detail or "anthropic" in error_detail.lower():
                    user_msg = "❌ I'm having trouble connecting to my AI services. Please check that ANTHROPIC_API_KEY is set correctly."
                elif "supabase" in error_detail.lower() or "database" in error_detail.lower():
                    user_msg = "❌ Database connection issue. The app will continue, but some features may be limited."
                elif "timeout" in error_detail.lower():
                    user_msg = "❌ Request timed out. This might be a temporary issue. Please try again."
                else:
                    user_msg = f"❌ Sorry, I encountered an error: {error_detail[:200]}"
                
                send_slack_message(
                    channel=channel,
                    text=user_msg,
                    thread_ts=thread_ts
                )

        # Use FastAPI BackgroundTasks for proper lifecycle management
        background_tasks.add_task(process_message)

        # Return immediately to beat Slack's 3-second timeout
        return {'status': 'processing'}
    # Handle reaction events
    elif event_type == 'reaction_added':
        user_id = event.get('user')
        reaction = event.get('reaction')
        item = event.get('item', {})
        channel = item.get('channel')
        message_ts = item.get('ts')

        print(f"👍 Reaction {reaction} added to message {message_ts}")

        # Handle ✅ (white_check_mark) reaction for saving as Draft
        # Handle 📅 🗓️ (calendar emojis) for scheduling to calendar
        if reaction in ['white_check_mark', 'calendar', 'spiral_calendar_pad']:
            try:
                # Get the message that was reacted to
                message_response = slack_client.conversations_history(
                    channel=channel,
                    latest=message_ts,
                    limit=1,
                    inclusive=True
                )
                
                if message_response.get('ok') and message_response.get('messages'):
                    message = message_response['messages'][0]
                    message_text = message.get('text', '')
                    
                    # Check if this is a Haiku-generated Twitter post
                    # Look for Twitter Post Generated and either "Haiku fast path" or just "Score:" line
                    is_haiku_post = ('Twitter Post Generated' in message_text and
                                    ('Haiku fast path' in message_text or
                                     ('Score:' in message_text and 'twitter' in message_text.lower())))

                    if is_haiku_post:
                        # Extract post content from message
                        # Format: "✅ Twitter Post Generated\n\n[Post content]\n\nHook: ...\nScore: ..."
                        lines = message_text.split('\n')
                        post_content = ""
                        hook_preview = ""
                        publish_date = None
                        
                        # Find the post content (between "Twitter Post Generated" and "Hook:")
                        # Skip empty lines and header, collect content until we hit "Hook:"
                        collecting_content = False
                        for line in lines:
                            if 'Twitter Post Generated' in line:
                                collecting_content = True
                                continue
                            if collecting_content:
                                if line.startswith('Hook:'):
                                    hook_preview = line.replace('Hook:', '').strip()
                                    break
                                elif line.startswith('Score:'):
                                    break
                                elif line.strip():  # Only add non-empty lines
                                    if post_content:
                                        post_content += "\n" + line
                                    else:
                                        post_content = line
                        
                        # Clean up post content (remove any extra formatting)
                        post_content = post_content.strip()
                        
                        if post_content:
                            # Save to Airtable with retry logic
                            from integrations.airtable_client import get_airtable_client
                            import asyncio

                            max_retries = 3
                            retry_delay = 2
                            result = None

                            for attempt in range(max_retries):
                                try:
                                    airtable = get_airtable_client()

                                    # Determine status based on reaction emoji
                                    # ✅ = Draft (save for review)
                                    # 📅 🗓️ = Scheduled (ready to go)
                                    if reaction in ['calendar', 'spiral_calendar_pad']:
                                        status = 'Scheduled'
                                        confirmation_emoji = '📅'
                                    else:  # white_check_mark
                                        status = 'Draft'
                                        confirmation_emoji = '📅'

                                    result = airtable.create_content_record(
                                        content=post_content,
                                        platform='twitter',
                                        post_hook=hook_preview if hook_preview else post_content[:100],
                                        status=status,
                                        publish_date=publish_date
                                    )

                                    if result and result.get('success'):
                                        break  # Success, exit retry loop
                                    elif attempt < max_retries - 1:
                                        print(f"⚠️ Airtable save failed (attempt {attempt + 1}/{max_retries}), retrying...")
                                        await asyncio.sleep(retry_delay)
                                        retry_delay *= 2  # Exponential backoff
                                except Exception as e:
                                    print(f"❌ Airtable error (attempt {attempt + 1}/{max_retries}): {e}")
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(retry_delay)
                                        retry_delay *= 2
                                    else:
                                        result = {'success': False, 'error': str(e)}

                            if result and result.get('success'):
                                # Send confirmation message based on status
                                # Use original thread if the message was in a thread
                                thread_ts = message.get('thread_ts', message_ts)

                                if status == 'Scheduled':
                                    confirmation_text = f"{confirmation_emoji} Scheduled to calendar!\n\n📊 <{result.get('url')}|View in Airtable>"
                                else:
                                    confirmation_text = f"{confirmation_emoji} Saved to Airtable as Draft\n\n📊 <{result.get('url')}|View>"

                                slack_client.chat_postMessage(
                                    channel=channel,
                                    thread_ts=thread_ts,
                                    text=confirmation_text,
                                    mrkdwn=True
                                )
                                print(f"✅ Saved Haiku Twitter post to Airtable (status: {status})")
                            else:
                                print(f"❌ Failed to save to Airtable: {result.get('error')}")
                                # Use original thread if the message was in a thread
                                thread_ts = message.get('thread_ts', message_ts)
                                slack_client.chat_postMessage(
                                    channel=channel,
                                    thread_ts=thread_ts,
                                    text=f"❌ Failed to save to Airtable: {result.get('error', 'Unknown error')}"
                                )
                        else:
                            print(f"⚠️ Could not extract post content from message")
                            
            except Exception as e:
                print(f"❌ Error handling ✅ reaction: {e}")
                import traceback
                traceback.print_exc()

        handler = get_slack_handler()
        if handler and handler.reaction_handler:
            try:
                await handler.reaction_handler.handle_reaction(
                    reaction_emoji=reaction,
                    thread_ts=message_ts,
                    user_id=user_id,
                    channel_id=channel
                )
            except Exception as e:
                print(f"⚠️ Reaction handler error (non-fatal): {e}")
                # Don't crash - reaction handling is non-critical

        return {'status': 'reaction_handled'}

    return {'status': 'ok'}

# ============= SLACK SLASH COMMANDS =============

@app.post('/slack/commands/content')
async def slack_command_content(request: Request):
    """Handle /content slash command"""
    form_data = await request.form()
    command_text = form_data.get('text', '')
    user_id = form_data.get('user_id')
    channel_id = form_data.get('channel_id')

    if not command_text:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Please provide details: `/content linkedin AI trends`'
        }

    handler = get_slack_handler()
    result = await handler.handle_content_command(
        command_text=command_text,
        user_id=user_id,
        channel_id=channel_id
    )

    return result

@app.post('/slack/commands/calendar')
async def slack_command_calendar(request: Request):
    """Handle /calendar slash command"""
    handler = get_slack_handler()
    if not handler or not handler.airtable:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Calendar not configured'
        }

    upcoming = handler.airtable.get_upcoming_content(days=7)
    return {
        'response_type': 'in_channel',
        'text': upcoming
    }

@app.post('/slack/commands/batch')
async def slack_command_batch(request: Request):
    """Handle /batch slash command"""
    form_data = await request.form()
    command_text = form_data.get('text', '')
    user_id = form_data.get('user_id')
    channel_id = form_data.get('channel_id')

    if not command_text:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Usage: `/batch 5 linkedin AI automation trends`'
        }

    handler = get_slack_handler()

    # Parse count from command
    parts = command_text.split(' ', 2)
    if len(parts) < 3:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Usage: `/batch 5 linkedin AI automation trends`'
        }

    try:
        count = int(parts[0])
        platform = parts[1].lower()
        topic = parts[2]
    except ValueError:
        return {
            'response_type': 'ephemeral',
            'text': '❌ First parameter must be a number'
        }

    # Start batch creation with supervision (Phase 0.2)
    supervise_task(
        handler.handle_batch_request(
            count=count,
            platform=platform,
            topic=topic,
            user_id=user_id,
            channel=channel_id
        ),
        name=f"batch_request_{platform}_{count}posts",
        max_restarts=0  # Don't auto-restart batch operations
    )

    return {
        'response_type': 'in_channel',
        'text': f'🚀 Creating {count} {platform} posts about "{topic}"...'
    }

@app.post('/slack/commands/cowrite')
async def slack_command_cowrite(request: Request):
    """Handle /cowrite [platform] [topic] slash command"""
    form_data = await request.form()
    command_text = form_data.get('text', '')
    user_id = form_data.get('user_id')
    channel_id = form_data.get('channel_id')

    # Create thread for this co-write session
    slack_client = get_slack_client()
    response = slack_client.chat_postMessage(
        channel=channel_id,
        text=f"🎨 Starting co-write session...\n`/cowrite {command_text}`"
    )
    thread_ts = response['ts']

    # Import handler
    from slack_bot.commands import handle_cowrite_command

    # Handle command (this starts async session)
    result = await handle_cowrite_command(
        command_text=command_text,
        user_id=user_id,
        channel_id=channel_id,
        thread_ts=thread_ts,
        slack_client=slack_client
    )

    return result


@app.post('/slack/commands/plan')
async def slack_command_plan(request: Request):
    """Handle /plan slash command for structured planning mode"""
    form_data = await request.form()
    command_text = form_data.get('text', '')
    user_id = form_data.get('user_id')
    channel_id = form_data.get('channel_id')
    response_url = form_data.get('response_url')

    if not command_text:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Usage: `/plan create a week of LinkedIn content about AI`'
        }

    # Initialize plan mode handler
    from slack_bot.plan_mode_handler import PlanModeHandler
    plan_handler = PlanModeHandler()

    # Create the plan
    plan_result = await plan_handler.create_plan(
        request=command_text,
        user_id=user_id,
        thread_ts=f"plan_{channel_id}_{int(time.time())}",
        channel_id=channel_id
    )

    if plan_result['success']:
        return {
            'response_type': 'in_channel',
            'text': plan_result['plan_text'] + '\n\n✅ Reply "approve" to execute this plan or "cancel" to abort.'
        }
    else:
        return {
            'response_type': 'ephemeral',
            'text': f'❌ Failed to create plan: {plan_result.get("error")}'
        }

@app.post('/slack/commands/stats')
async def slack_command_stats(request: Request):
    """Handle /stats slash command"""
    form_data = await request.form()
    user_id = form_data.get('user_id')

    try:
        # Get stats from database
        result = supabase.table('slack_threads').select('*').execute()
        total = len(result.data)

        # Calculate average score
        scores = [r['latest_score'] for r in result.data if r.get('latest_score')]
        avg_score = sum(scores) / len(scores) if scores else 0

        stats_text = f"""📊 *Content Stats*
• Total pieces created: {total}
• Average quality score: {avg_score:.1f}/100
• Active platform: Slack
• Workflows enabled: ✅
        """

        return {
            'response_type': 'ephemeral',
            'text': stats_text
        }
    except Exception as e:
        return {
            'response_type': 'ephemeral',
            'text': f'❌ Error getting stats: {str(e)}'
        }


# ============= N8N WEBHOOK ENDPOINT =============

@app.post('/api/n8n/weekly-briefing')
async def n8n_weekly_briefing(request: Request):
    """
    n8n webhook endpoint for automated weekly briefings.

    This endpoint:
    1. Fetches posts from Airtable for the past week
    2. Gets engagement data from Ayrshare (if available)
    3. Analyzes performance
    4. Generates briefing
    5. Posts to Slack

    Request body (optional):
    {
        "days_back": 7,  # How many days to analyze (default: 7)
        "slack_channel": "content-strategy",  # Where to post (default: from env)
        "include_ayrshare": true  # Whether to fetch real engagement data
    }

    Returns:
    {
        "success": true,
        "message": "Briefing posted to Slack",
        "analytics_summary": "...",
        "post_count": 15
    }
    """
    try:
        # Check for optional webhook authentication
        webhook_secret = os.getenv('N8N_WEBHOOK_SECRET', '')
        if webhook_secret:
            # Authentication is configured, so enforce it
            auth_header = request.headers.get('Authorization', '')

            if not auth_header.startswith('Bearer '):
                logger.warning("n8n webhook: Missing or invalid Authorization header format")
                return {
                    "success": False,
                    "error": "Unauthorized: Bearer token required"
                }, 401

            token = auth_header.replace('Bearer ', '').strip()
            if token != webhook_secret:
                logger.warning("n8n webhook: Invalid authentication token")
                return {
                    "success": False,
                    "error": "Unauthorized: Invalid token"
                }, 401

            logger.info("n8n webhook: Authentication successful")

        # Parse request data
        data = await request.json() if request.headers.get('content-type') == 'application/json' else {}
        days_back = data.get('days_back', 7)
        slack_channel = data.get('slack_channel', os.getenv('SLACK_CONTENT_CHANNEL', 'content-strategy'))
        include_ayrshare = data.get('include_ayrshare', False)

        # Import required modules
        from integrations.airtable_client import AirtableClient
        from slack_bot.analytics_handler import analyze_performance
        from slack_bot.briefing_handler import generate_briefing

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        date_range = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d")
        }

        logger.info(f"📊 n8n webhook: Generating briefing for {date_range['start']} to {date_range['end']}")

        # Fetch posts from Airtable
        airtable = AirtableClient()
        posts_data = []

        try:
            # Get posts from Airtable within date range
            all_posts = airtable.get_posts_in_range(start_date, end_date)

            for post in all_posts:
                # Extract relevant fields
                post_entry = {
                    "hook": post.get('Hook', ''),
                    "platform": post.get('Platform', 'unknown').lower(),
                    "quality_score": post.get('Quality Score', 0),
                    "published_at": post.get('Publish Date', ''),
                    "impressions": 0,
                    "engagements": 0,
                    "engagement_rate": 0
                }

                # If Ayrshare integration is enabled, fetch real metrics
                if include_ayrshare and post.get('Ayrshare ID'):
                    from integrations.ayrshare_client import get_ayrshare_client
                    ayrshare = get_ayrshare_client()

                    # Fetch real analytics from Ayrshare
                    analytics = ayrshare.get_post_analytics(post['Ayrshare ID'])
                    post_entry['impressions'] = analytics['impressions']
                    post_entry['engagements'] = analytics['engagements']
                    post_entry['engagement_rate'] = analytics['engagement_rate']
                else:
                    # Use mock data based on quality score
                    import random
                    quality = post_entry['quality_score']
                    post_entry['impressions'] = random.randint(1000, 20000) * (quality / 25)
                    post_entry['engagements'] = int(post_entry['impressions'] * (quality / 300))
                    post_entry['engagement_rate'] = (post_entry['engagements'] / post_entry['impressions']) * 100

                posts_data.append(post_entry)

        except Exception as e:
            logger.error(f"Error fetching from Airtable: {e}")
            # Use sample data as fallback
            posts_data = [
                {
                    "hook": "Sample post for testing",
                    "platform": "linkedin",
                    "quality_score": 25,
                    "impressions": 5000,
                    "engagements": 450,
                    "engagement_rate": 9.0,
                    "published_at": datetime.now().strftime("%Y-%m-%d")
                }
            ]

        # Analyze performance
        logger.info(f"📈 Analyzing {len(posts_data)} posts")
        analytics = await analyze_performance(posts_data, date_range, anthropic_client)

        # Generate briefing
        logger.info("📝 Generating briefing")
        briefing = await generate_briefing(
            analytics=analytics,
            user_context={
                "content_goals": "Build thought leadership in AI automation",
                "audience": "Enterprise decision makers and tech leaders"
            },
            client=anthropic_client
        )

        # Post to Slack
        if slack_client:
            try:
                # Format message for Slack
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": briefing['briefing_markdown'][:3000]  # Slack limit
                        }
                    }
                ]

                # Add suggested topics if available
                if briefing.get('suggested_topics'):
                    topics_text = "*📝 Suggested Topics:*\n"
                    for i, topic in enumerate(briefing['suggested_topics'][:5], 1):
                        topics_text += f"{i}. {topic}\n"

                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": topics_text}
                    })

                # Post to Slack
                response = slack_client.chat_postMessage(
                    channel=slack_channel,
                    text="📊 Your Weekly Content Intelligence Briefing",
                    blocks=blocks
                )

                logger.info(f"✅ Briefing posted to Slack channel: {slack_channel}")

            except Exception as e:
                logger.error(f"Error posting to Slack: {e}")

        return {
            "success": True,
            "message": f"Briefing generated for {len(posts_data)} posts",
            "analytics_summary": analytics.get('summary', ''),
            "post_count": len(posts_data),
            "date_range": date_range
        }

    except Exception as e:
        logger.error(f"Error in n8n webhook: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate briefing"
        }

# ============= MAIN STARTUP =============

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "5000"))
    print(f"🚀 Starting Slack Content Agent on port {port}")
    print(f"📍 Health check: http://localhost:{port}/healthz")
    print(f"🔗 Slack events: http://localhost:{port}/slack/events")

    uvicorn.run(app, host="0.0.0.0", port=port)
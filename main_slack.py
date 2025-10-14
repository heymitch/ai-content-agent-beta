"""
Slack-Only Content Agent
Clean implementation with only essential Slack functionality
"""

from anthropic import Anthropic, RateLimitError
from fastapi import FastAPI, Request
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

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Event deduplication cache (stores event_id for 5 minutes)
processed_events = {}
EVENT_CACHE_TTL = 300  # 5 minutes

# Track threads where bot is participating (thread_ts -> timestamp of last activity)
participating_threads = {}
THREAD_PARTICIPATION_TTL = 86400  # 24 hours

# Initialize Supabase
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Initialize Anthropic
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Initialize Slack client
slack_client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))

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
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'slack-content-agent'
    }

# ============= SLACK EVENT HANDLERS =============

@app.post('/slack/events')
async def handle_slack_event(request: Request):
    """Handle Slack events with proper async support"""
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

        # bot_user_id already retrieved above
        is_bot_mentioned = bot_user_id and f'<@{bot_user_id}>' in message_text

        # Clean expired thread participations
        now = time.time()
        expired_threads = [k for k, v in participating_threads.items()
                          if now - v > THREAD_PARTICIPATION_TTL]
        for k in expired_threads:
            del participating_threads[k]
            print(f"🧹 Expired thread participation: {k}")

        # Determine if bot should respond
        should_respond = False

        # Debug logging
        print(f"🔍 Debug: event_type={event_type}, thread_ts={thread_ts}, is_mentioned={is_bot_mentioned}")
        print(f"🔍 Active threads: {list(participating_threads.keys())}")

        if event_type == 'app_mention' or is_bot_mentioned:
            # Always respond to direct mentions
            should_respond = True
            # Mark this thread as participating
            participating_threads[thread_ts] = now
            print(f"✅ Bot mentioned - participating in thread {thread_ts}")
        elif event.get('channel_type') == 'im':
            # Always respond in DMs (and maintain conversation context)
            should_respond = True
            # DMs automatically participate (the whole DM channel is one conversation)
            participating_threads[thread_ts] = now
            print("✅ Direct message - responding with continuous context")
        elif thread_ts in participating_threads:
            # Respond to all messages in threads we're participating in
            should_respond = True
            # Update last activity time
            participating_threads[thread_ts] = now
            print(f"✅ Continuing conversation in thread {thread_ts}")
        else:
            # Don't respond to random channel messages
            print(f"⏭️ Skipping - not participating in thread {thread_ts}")
            print(f"   Thread {thread_ts} not in active threads: {participating_threads.keys()}")
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
                # Import Claude Agent SDK handler
                from slack_bot.claude_agent_handler import ClaudeAgentHandler
                print("✅ Claude Agent SDK loaded successfully")

                handler = get_slack_handler()

                # Use the REAL Claude Agent SDK handler
                if not hasattr(handler, 'claude_agent'):
                    handler.claude_agent = ClaudeAgentHandler(
                        memory_handler=handler.memory if handler else None
                    )

                print("🚀 Claude Agent SDK ready with 6 tools")

                # Save user message to conversation history
                if handler.memory:
                    handler.memory.add_message(
                        thread_ts=thread_ts,
                        channel_id=channel,
                        user_id=user_id,
                        role='user',
                        content=message_text
                    )
                    print(f"💾 Saved user message to conversation history")

                # The agent decides what to do based on context:
                # - Create content → delegates to workflows
                # - Answer questions → uses web_search if needed
                # - Analyze performance → uses analysis tools
                # - General conversation → maintains thread context
                response_text = await handler.claude_agent.handle_conversation(
                    message=message_text,
                    user_id=user_id,
                    thread_ts=thread_ts,  # Use thread_ts for session continuity
                    channel_id=channel
                )

                # Save assistant response to conversation history
                if handler.memory:
                    handler.memory.add_message(
                        thread_ts=thread_ts,
                        channel_id=channel,
                        user_id='bot',
                        role='assistant',
                        content=response_text
                    )
                    print(f"💾 Saved assistant response to conversation history")

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
                send_slack_message(
                    channel=channel,
                    text=f"❌ Sorry, I encountered an error: {str(e)}",
                    thread_ts=thread_ts
                )

        # Create background task
        asyncio.create_task(process_message())

        # Return immediately to beat 3-second timeout
        return {'status': 'processing'}
    # Handle reaction events
    elif event_type == 'reaction_added':
        user_id = event.get('user')
        reaction = event.get('reaction')
        item = event.get('item', {})
        channel = item.get('channel')
        message_ts = item.get('ts')

        print(f"👍 Reaction {reaction} added to message {message_ts}")

        handler = get_slack_handler()
        if handler and handler.reaction_handler:
            await handler.reaction_handler.handle_reaction(
                reaction_emoji=reaction,
                thread_ts=message_ts,
                user_id=user_id,
                channel_id=channel
            )

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

    # Start batch creation
    asyncio.create_task(
        handler.handle_batch_request(
            count=count,
            platform=platform,
            topic=topic,
            user_id=user_id,
            channel=channel_id
        )
    )

    return {
        'response_type': 'in_channel',
        'text': f'🚀 Creating {count} {platform} posts about "{topic}"...'
    }

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

# ============= MAIN STARTUP =============

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "5000"))
    print(f"🚀 Starting Slack Content Agent on port {port}")
    print(f"📍 Health check: http://localhost:{port}/healthz")
    print(f"🔗 Slack events: http://localhost:{port}/slack/events")

    uvicorn.run(app, host="0.0.0.0", port=port)
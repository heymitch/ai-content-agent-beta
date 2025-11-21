"""
Slash command handlers for Slack content agent
/content, /calendar, /batch, /stats, /cowrite, /thinking
"""
from typing import Dict, Any
import asyncio
from slack_sdk import WebClient


async def handle_content_command(
    command_text: str,
    user_id: str,
    channel_id: str,
    handler
) -> Dict[str, Any]:
    """
    Handle /content [platform] [brief] command

    Args:
        command_text: Text after /content
        user_id: Slack user ID
        channel_id: Channel ID
        handler: SlackContentHandler instance

    Returns:
        Slack response dict
    """
    parts = command_text.strip().split(' ', 1)

    if len(parts) < 2:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Usage: `/content [platform] [brief]`\n\nExample: `/content linkedin why companies should own AI infrastructure`'
        }

    platform = parts[0].lower()
    topic = parts[1]

    # Validate platform
    valid_platforms = ['linkedin', 'twitter', 'email']
    if platform not in valid_platforms:
        return {
            'response_type': 'ephemeral',
            'text': f'❌ Invalid platform: {platform}\n\nSupported: linkedin, twitter, email'
        }

    # Trigger content creation (will post result to channel)
    return {
        'response_type': 'ephemeral',
        'text': f'🎨 Creating {platform} content about: _{topic}_\n\nI\'ll post the result in this channel shortly...'
    }


async def handle_calendar_command(
    command_text: str,
    user_id: str,
    handler
) -> Dict[str, Any]:
    """
    Handle /calendar command

    Args:
        command_text: Text after /calendar (optional: 'add [date]')
        user_id: Slack user ID
        handler: SlackContentHandler instance

    Returns:
        Slack response dict
    """
    if command_text.strip().startswith('add'):
        return {
            'response_type': 'ephemeral',
            'text': '❌ Use emoji reactions to schedule content:\n\nReact with 📅 on any content message to add to calendar.'
        }

    # Show upcoming calendar
    calendar_preview = handler.get_calendar_preview(user_id, days=7)

    return {
        'response_type': 'ephemeral',
        'text': calendar_preview
    }


async def handle_batch_command(
    command_text: str,
    user_id: str,
    channel_id: str,
    handler
) -> Dict[str, Any]:
    """
    Handle /batch [count] [platform] [topic] command

    Args:
        command_text: Text after /batch
        user_id: Slack user ID
        channel_id: Channel ID
        handler: SlackContentHandler instance

    Returns:
        Slack response dict
    """
    parts = command_text.strip().split(' ', 2)

    if len(parts) < 3:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Usage: `/batch [count] [platform] [topic]`\n\nExample: `/batch 3 linkedin AI infrastructure trends`'
        }

    try:
        count = int(parts[0])
    except ValueError:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Count must be a number (1-5)'
        }

    if count < 1 or count > 5:
        return {
            'response_type': 'ephemeral',
            'text': '❌ Count must be between 1 and 5'
        }

    platform = parts[1].lower()
    topic = parts[2]

    # Validate platform
    valid_platforms = ['linkedin', 'twitter', 'email']
    if platform not in valid_platforms:
        return {
            'response_type': 'ephemeral',
            'text': f'❌ Invalid platform: {platform}\n\nSupported: linkedin, twitter, email'
        }

    # Trigger batch creation (will post results to channel)
    return {
        'response_type': 'ephemeral',
        'text': f'📦 Creating {count} {platform} posts about: _{topic}_\n\n⏱️ Estimated time: ~{count * 25} seconds\n\nI\'ll post results in this channel...'
    }


async def handle_stats_command(
    user_id: str,
    handler
) -> Dict[str, Any]:
    """
    Handle /stats command

    Args:
        user_id: Slack user ID
        handler: SlackContentHandler instance

    Returns:
        Slack response dict
    """
    # Get user's content stats
    threads = handler.memory.get_user_threads(user_id, limit=50)

    if not threads:
        return {
            'response_type': 'ephemeral',
            'text': '📊 *Your Content Stats*\n\nNo content created yet. Try: `/content linkedin [topic]`'
        }

    # Calculate stats
    total = len(threads)
    by_platform = {}
    by_status = {}
    total_score = 0

    for thread in threads:
        platform = thread.get('platform', 'unknown')
        status = thread.get('status', 'unknown')
        score = thread.get('latest_score', 0)

        by_platform[platform] = by_platform.get(platform, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        total_score += score

    avg_score = total_score / total if total > 0 else 0

    # Format response
    sections = [
        '📊 *Your Content Stats*\n',
        f'Total pieces created: {total}',
        f'Average quality score: {avg_score:.0f}/100\n',
        '*By Platform:*'
    ]

    for platform, count in by_platform.items():
        sections.append(f'• {platform.capitalize()}: {count}')

    sections.append('\n*By Status:*')
    for status, count in by_status.items():
        sections.append(f'• {status.capitalize()}: {count}')

    return {
        'response_type': 'ephemeral',
        'text': '\n'.join(sections)
    }


async def handle_cowrite_command(
    command_text: str,
    user_id: str,
    channel_id: str,
    thread_ts: str,
    slack_client: WebClient
) -> Dict[str, Any]:
    """
    Handle /cowrite [platform] [topic/brief] command

    Starts an interactive co-write session using Agent SDK with native tool access.
    Results print to Slack only - no auto-save to Airtable unless user approves.

    Examples:
        /cowrite linkedin AI agents for solo operators
        /cowrite twitter 5 lessons from building AI agents
        /cowrite email weekly newsletter about AI automation
        /cowrite youtube tutorial on getting started with AI agents
        /cowrite instagram behind the scenes: building with AI

    Args:
        command_text: Text after /cowrite (e.g., "linkedin AI agents topic")
        user_id: Slack user ID
        channel_id: Channel ID
        thread_ts: Thread timestamp (for session tracking)
        slack_client: Slack WebClient instance

    Returns:
        Slack response dict (immediate acknowledgment)
    """
    from slack_bot.cowrite_handler import get_or_create_cowrite_session

    # Parse platform and topic
    parts = command_text.strip().split(maxsplit=1)

    if len(parts) < 2:
        return {
            'response_type': 'ephemeral',
            'text': '''❌ Usage: `/cowrite [platform] [topic/brief]`

**Examples:**
• `/cowrite linkedin AI agents are changing workflows`
• `/cowrite twitter 5 lessons from automating content`
• `/cowrite email weekly AI newsletter`

**Supported platforms:** linkedin, twitter, email, youtube, instagram'''
        }

    platform = parts[0].lower()
    topic = parts[1]

    # Validate platform
    valid_platforms = ['linkedin', 'twitter', 'email', 'youtube', 'instagram']
    if platform not in valid_platforms:
        return {
            'response_type': 'ephemeral',
            'text': f'❌ Invalid platform: `{platform}`\n\n**Supported:** {", ".join(valid_platforms)}'
        }

    # Get or create co-write session for this thread
    session = get_or_create_cowrite_session(
        thread_ts=thread_ts,
        user_id=user_id,
        channel_id=channel_id,
        slack_client=slack_client
    )

    # Start session asynchronously (don't block slash command response)
    asyncio.create_task(session.start_session(platform, topic))

    # Return immediate acknowledgment
    return {
        'response_type': 'in_channel',
        'text': f'''🎨 **Co-Write Session Started**

**Platform:** {platform}
**Topic:** {topic}

⏳ Generating initial draft and quality analysis...

*I'll iterate with you as many times as you want. When you're happy, say "approve" or "send to calendar" to save.*'''
    }


async def handle_thinking_command(
    command_text: str,
    user_id: str,
    channel_id: str,
    thread_ts: str,
    slack_client: WebClient
) -> Dict[str, Any]:
    """
    Handle /thinking [platform] [topic/brief] command

    Creates content with Thinking Mode enabled - adds validation + fix loop
    for higher quality output (takes longer but produces better results).

    Examples:
        /thinking linkedin why AI agents need human oversight
        /thinking twitter 5 mistakes founders make with AI
        /thinking email weekly update on AI automation trends

    Args:
        command_text: Text after /thinking (e.g., "linkedin AI agents topic")
        user_id: Slack user ID
        channel_id: Channel ID
        thread_ts: Thread timestamp
        slack_client: Slack WebClient instance

    Returns:
        Slack response dict
    """
    # Parse platform and topic
    parts = command_text.strip().split(maxsplit=1)

    if len(parts) < 2:
        return {
            'response_type': 'ephemeral',
            'text': '''❌ Usage: `/thinking [platform] [topic/brief]`

**Thinking Mode** adds validation + fix loop for higher quality (takes ~90s vs ~45s).

**Examples:**
• `/thinking linkedin AI agents need human oversight`
• `/thinking twitter 5 mistakes founders make with AI`
• `/thinking email weekly AI automation update`

**Supported platforms:** linkedin, twitter, email, youtube, instagram'''
        }

    platform = parts[0].lower()
    topic = parts[1]

    # Validate platform
    valid_platforms = ['linkedin', 'twitter', 'email', 'youtube', 'instagram']
    if platform not in valid_platforms:
        return {
            'response_type': 'ephemeral',
            'text': f'❌ Invalid platform: `{platform}`\n\n**Supported:** {", ".join(valid_platforms)}'
        }

    # Post initial message to channel
    try:
        result = slack_client.chat_postMessage(
            channel=channel_id,
            text=f'''🧠 **Thinking Mode Activated**

**Platform:** {platform}
**Topic:** {topic}

⏳ Creating content with validation + fix loop...
*This takes ~90 seconds for higher quality output.*''',
            thread_ts=thread_ts
        )
        message_ts = result['ts']
    except Exception as e:
        return {
            'response_type': 'ephemeral',
            'text': f'❌ Failed to start thinking mode: {str(e)}'
        }

    # Import and run the appropriate agent with thinking_mode=True
    async def run_thinking_mode():
        try:
            if platform == 'linkedin':
                from agents.linkedin_direct_api_agent import create_linkedin_post_workflow
                response = await create_linkedin_post_workflow(
                    topic=topic,
                    context="",
                    style="thought_leadership",
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    user_id=user_id,
                    thinking_mode=True
                )
            elif platform == 'twitter':
                from agents.twitter_direct_api_agent import create_twitter_post_workflow
                response = await create_twitter_post_workflow(
                    topic=topic,
                    context="",
                    style="thought_leadership",
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    user_id=user_id,
                    thinking_mode=True
                )
            elif platform == 'email':
                from agents.email_direct_api_agent import create_email_workflow
                response = await create_email_workflow(
                    topic=topic,
                    context="",
                    email_type="value",
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    user_id=user_id,
                    thinking_mode=True
                )
            elif platform == 'youtube':
                from agents.youtube_direct_api_agent import create_youtube_workflow
                response = await create_youtube_workflow(
                    topic=topic,
                    context="",
                    style="thought_leadership",
                    script_type="tutorial",
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    user_id=user_id,
                    thinking_mode=True
                )
            elif platform == 'instagram':
                from agents.instagram_direct_api_agent import create_instagram_workflow
                response = await create_instagram_workflow(
                    topic=topic,
                    context="",
                    style="thought_leadership",
                    caption_type="educational",
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    user_id=user_id,
                    thinking_mode=True
                )
            else:
                response = f"❌ Platform {platform} not yet supported for thinking mode"

            # Post the result
            slack_client.chat_postMessage(
                channel=channel_id,
                text=response,
                thread_ts=thread_ts
            )
        except Exception as e:
            slack_client.chat_postMessage(
                channel=channel_id,
                text=f"❌ Thinking mode error: {str(e)}",
                thread_ts=thread_ts
            )

    # Run asynchronously
    asyncio.create_task(run_thinking_mode())

    return {
        'response_type': 'ephemeral',
        'text': '🧠 Thinking mode started. Watch the thread for results...'
    }

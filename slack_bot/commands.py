"""
Slash command handlers for Slack content agent
/content, /calendar, /batch, /stats
"""
from typing import Dict, Any
import asyncio


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

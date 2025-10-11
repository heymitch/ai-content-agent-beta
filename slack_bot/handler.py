"""
Main Slack bot handler - integrates existing workflows with Slack
Reuses all existing infrastructure: workflows, validators, supabase, airtable
"""
from typing import Dict, Any, Callable, Optional
import asyncio
from datetime import datetime

# Import existing workflow registry
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from workflows import WORKFLOW_REGISTRY

# Import local utilities
from .formatters import (
    parse_content_request,
    format_content_result,
    format_batch_result,
    format_detailed_report,
    format_error_message
)
from .memory import SlackThreadMemory
from .reactions import ReactionHandler


class SlackContentHandler:
    """Main handler for Slack content agent"""

    def __init__(self, supabase_client, airtable_client=None):
        """
        Initialize handler with existing clients

        Args:
            supabase_client: Existing Supabase client from main.py
            airtable_client: Existing Airtable client (optional)
        """
        self.supabase = supabase_client
        self.airtable = airtable_client
        self.memory = SlackThreadMemory(supabase_client)
        self.reaction_handler = ReactionHandler(
            supabase_client,
            airtable_client,
            self.memory
        )

    async def handle_content_request(
        self,
        message_text: str,
        user_id: str,
        channel: str,
        thread_ts: str,
        send_message_fn: Callable
    ) -> Dict[str, Any]:
        """
        Handle content creation request from Slack

        Args:
            message_text: User's message
            user_id: Slack user ID
            channel: Slack channel ID
            thread_ts: Thread timestamp (for threading)
            send_message_fn: Existing send_slack_message function from main.py

        Returns:
            Result dict with workflow output
        """
        try:
            # Parse request
            request_data = parse_content_request(message_text)
            platform = request_data['platform']
            topic = request_data['topic']

            # Check if topic is vague (single word like "both", "this", "that")
            vague_topics = ['both', 'this', 'that', 'it', 'them', 'those', 'these']
            if topic.lower().strip() in vague_topics:
                print(f"🔍 Vague topic detected: '{topic}' - resolving from thread context...")

                # Resolve topic from thread context
                resolved_topics = await self._resolve_vague_topic(
                    vague_reference=topic,
                    thread_ts=thread_ts,
                    message_text=message_text
                )

                if resolved_topics:
                    # If "both" was requested and we got multiple topics, create both
                    if topic.lower().strip() == 'both' and len(resolved_topics) > 1:
                        print(f"✅ Creating {len(resolved_topics)} posts: {resolved_topics}")

                        # Send acknowledgment
                        send_message_fn(
                            channel,
                            f"🎨 Creating {len(resolved_topics)} {platform} posts:\n" +
                            "\n".join([f"• {t}" for t in resolved_topics]) +
                            f"\n\nThis will take ~{len(resolved_topics) * 25} seconds...",
                            thread_ts
                        )

                        # Create each post
                        for i, resolved_topic in enumerate(resolved_topics, 1):
                            await self.handle_content_request(
                                message_text=f"write a {platform} post about {resolved_topic}",
                                user_id=user_id,
                                channel=channel,
                                thread_ts=thread_ts,
                                send_message_fn=send_message_fn
                            )
                            if i < len(resolved_topics):
                                await asyncio.sleep(2)  # Rate limit

                        return {'status': 'batch_created_from_context'}

                    else:
                        # Single topic resolved
                        topic = resolved_topics[0]
                        print(f"✅ Resolved to: '{topic}'")
                else:
                    print(f"⚠️ Could not resolve vague reference")
                    send_message_fn(
                        channel,
                        f"❓ I'm not sure what you mean by '{topic}'. Could you be more specific?",
                        thread_ts
                    )
                    return {'status': 'vague_topic_unresolved'}

            print(f"🎨 Content request: {platform} post about '{topic}'")

            # Send "working on it" message
            send_message_fn(
                channel,
                f"🎨 Creating {platform} content about: _{topic}_\n\nThis will take ~20-30 seconds...",
                thread_ts
            )

            # Load brand context (TODO: make user-specific)
            brand_context = self._load_brand_context(user_id)

            # Execute workflow using existing WORKFLOW_REGISTRY
            workflow = WORKFLOW_REGISTRY[platform](self.supabase)
            result = await workflow.execute(
                brief=topic,
                brand_context=brand_context,
                user_id=user_id,
                max_iterations=3,
                target_score=80
            )

            # Store in thread memory
            self.memory.create_thread(
                thread_ts=thread_ts,
                channel_id=channel,
                user_id=user_id,
                platform=platform,
                initial_draft=result['draft'],
                initial_score=result['grading']['score']
            )

            # Update with full metadata for detailed reports
            self.memory.update_draft(
                thread_ts=thread_ts,
                draft=result['draft'],
                score=result['grading']['score'],
                workflow_result=result
            )

            # Auto-send to Airtable if available
            airtable_url = None
            if self.airtable:
                try:
                    from datetime import timedelta

                    # Schedule for tomorrow
                    publish_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

                    # Create Airtable record with correct method name
                    record_id = self.airtable.create_content_record(
                        content=result['draft'],
                        platform=platform,
                        scheduled_date=publish_date,
                        quality_score=result.get('grading', {}).get('score', 0),
                        metadata={
                            'slack_user': user_id,
                            'slack_thread': thread_ts,
                            'iterations': result.get('iterations', 1),
                            'hooks_used': result.get('hook_used', {}).get('framework', 'unknown') if 'hook_used' in result else 'unknown'
                        }
                    )

                    # Get Airtable URL
                    base_id = os.getenv('AIRTABLE_BASE_ID')
                    table_id = os.getenv('AIRTABLE_TABLE_NAME')
                    airtable_url = f"https://airtable.com/{base_id}/{table_id}/{record_id}"

                    print(f"✅ Sent to Airtable: {record_id}")

                except Exception as e:
                    print(f"⚠️ Airtable send failed: {e}")

            # Format response for Slack
            response = format_content_result(result, platform, airtable_url)

            # Send formatted result
            send_message_fn(channel, response, thread_ts)

            return result

        except Exception as e:
            print(f"❌ Content request error: {e}")
            import traceback
            traceback.print_exc()

            error_msg = format_error_message(e, "Creating content")
            send_message_fn(channel, error_msg, thread_ts)

            return {'success': False, 'error': str(e)}

    async def handle_batch_request(
        self,
        platform: str,
        topic: str,
        count: int,
        user_id: str,
        channel: str,
        thread_ts: str,
        send_message_fn: Callable
    ) -> list:
        """
        Handle batch content creation

        Args:
            platform: Platform name
            topic: Content topic
            count: Number of pieces to create
            user_id: Slack user ID
            channel: Slack channel ID
            thread_ts: Thread timestamp
            send_message_fn: Send message function

        Returns:
            List of workflow results
        """
        try:
            # Limit batch size
            count = min(count, 5)  # Max 5 at a time

            print(f"📦 Batch request: {count} {platform} posts about '{topic}'")

            # Send progress message
            send_message_fn(
                channel,
                f"📦 Creating {count} {platform} posts about: _{topic}_\n\n⏱️ Estimated time: ~{count * 25} seconds\n_(Rate limited: 2s between posts)_",
                thread_ts
            )

            # Load brand context
            brand_context = self._load_brand_context(user_id)

            # Execute workflows with rate limiting
            workflow = WORKFLOW_REGISTRY[platform](self.supabase)
            results = []

            for i in range(count):
                print(f"📝 Creating post {i+1}/{count}...")

                # Add variation to brief for different angles
                varied_brief = f"{topic} (angle {i+1})"

                result = await workflow.execute(
                    brief=varied_brief,
                    brand_context=brand_context,
                    user_id=user_id,
                    max_iterations=2,  # Fewer iterations for batch
                    target_score=75    # Slightly lower threshold for speed
                )

                results.append(result)

                # Rate limit: 2 second delay between posts
                if i < count - 1:
                    await asyncio.sleep(2)

                # Send progress update
                send_message_fn(
                    channel,
                    f"✅ Post {i+1}/{count} complete (Score: {result['grading']['score']}/100)",
                    thread_ts
                )

            # Format batch summary
            batch_summary = format_batch_result(results, platform)
            send_message_fn(channel, batch_summary, thread_ts)

            # Send individual posts as thread replies
            for i, result in enumerate(results, 1):
                individual_msg = f"*Post {i}:*\n\n```{result['draft']}```\n\n📊 Score: {result['grading']['score']}/100"
                send_message_fn(channel, individual_msg, thread_ts)

                # Store each in memory
                post_thread_ts = f"{thread_ts}_post_{i}"
                self.memory.create_thread(
                    thread_ts=post_thread_ts,
                    channel_id=channel,
                    user_id=user_id,
                    platform=platform,
                    initial_draft=result['draft'],
                    initial_score=result['grading']['score']
                )

            return results

        except Exception as e:
            print(f"❌ Batch request error: {e}")
            error_msg = format_error_message(e, "Batch content creation")
            send_message_fn(channel, error_msg, thread_ts)
            return []

    async def handle_revision_request(
        self,
        thread_ts: str,
        revision_feedback: str,
        channel: str,
        send_message_fn: Callable
    ) -> Dict[str, Any]:
        """
        Handle revision request in thread

        Args:
            thread_ts: Original thread timestamp
            revision_feedback: User's revision instructions
            channel: Slack channel
            send_message_fn: Send message function

        Returns:
            Revised workflow result
        """
        try:
            # Get thread context
            thread = self.memory.get_thread(thread_ts)
            if not thread:
                send_message_fn(
                    channel,
                    "❌ Thread not found. Start a new content request.",
                    thread_ts
                )
                return {'success': False}

            platform = thread['platform']
            current_draft = thread['latest_draft']

            print(f"✏️ Revision request for {platform} content")

            # Send working message
            send_message_fn(
                channel,
                f"✏️ Revising based on your feedback...\n\n_This will take ~15-20 seconds_",
                thread_ts
            )

            # Use reviser agent directly
            workflow = WORKFLOW_REGISTRY[platform](self.supabase)

            # Run single revision iteration
            revised_draft = await workflow._reviser_agent(
                draft=current_draft,
                feedback=revision_feedback,
                brand_context=self._load_brand_context(thread['user_id']),
                verified_facts=""
            )

            # Re-validate
            grading = await workflow._validator_agent(revised_draft)

            # Update thread
            self.memory.update_draft(
                thread_ts=thread_ts,
                draft=revised_draft,
                score=grading['score']
            )

            # Format response
            result = {
                'draft': revised_draft,
                'grading': grading,
                'iterations': 1,
                'platform': platform
            }

            response = format_content_result(result, platform)
            send_message_fn(channel, response, thread_ts)

            return result

        except Exception as e:
            print(f"❌ Revision error: {e}")
            error_msg = format_error_message(e, "Revising content")
            send_message_fn(channel, error_msg, thread_ts)
            return {'success': False}

    async def handle_reaction(
        self,
        reaction_emoji: str,
        thread_ts: str,
        user_id: str,
        channel: str,
        send_message_fn: Callable
    ) -> Dict[str, Any]:
        """
        Handle emoji reaction on content

        Args:
            reaction_emoji: Emoji name (without colons)
            thread_ts: Thread timestamp
            user_id: User who reacted
            channel: Channel ID
            send_message_fn: Send message function

        Returns:
            Action result
        """
        try:
            result = await self.reaction_handler.handle_reaction(
                reaction_emoji=reaction_emoji,
                thread_ts=thread_ts,
                user_id=user_id,
                channel_id=channel
            )

            # Send response message
            if result.get('message'):
                send_message_fn(channel, result['message'], thread_ts)

            # Special handling for regenerate
            if result.get('trigger_workflow'):
                thread = self.memory.get_thread(thread_ts)
                if thread:
                    # Re-run workflow with same parameters
                    await self.handle_content_request(
                        message_text=f"write a {thread['platform']} post about [regenerated version]",
                        user_id=user_id,
                        channel=channel,
                        thread_ts=thread_ts,
                        send_message_fn=send_message_fn
                    )

            return result

        except Exception as e:
            print(f"❌ Reaction error: {e}")
            error_msg = format_error_message(e, "Processing reaction")
            send_message_fn(channel, error_msg, thread_ts)
            return {'success': False}

    async def _resolve_vague_topic(
        self,
        vague_reference: str,
        thread_ts: str,
        message_text: str
    ) -> Optional[list]:
        """
        Resolve vague reference like "both", "this", "that" using thread context

        Args:
            vague_reference: The vague word ("both", "this", etc.)
            thread_ts: Thread timestamp for context
            message_text: Full message text

        Returns:
            List of resolved topics, or None if couldn't resolve
        """
        try:
            from anthropic import Anthropic

            # Get thread history
            thread_history = self.memory.get_thread_history(thread_ts)

            if not thread_history or len(thread_history) < 2:
                return None

            # Build context from last 10 messages
            context_messages = thread_history[-10:]
            context_text = "\n".join([
                f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
                for msg in context_messages
            ])

            # Use Claude to resolve the reference
            client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

            resolution_prompt = f"""Given this conversation thread, what does "{vague_reference}" refer to in the latest message?

CONVERSATION HISTORY:
{context_text}

LATEST MESSAGE: "{message_text}"

TASK: Extract the specific topic(s) that "{vague_reference}" refers to.

RULES:
- If "{vague_reference}" is "both", return EXACTLY 2 topics as a JSON array
- If it's "this/that/it", return 1 topic as a JSON array with one item
- Topics should be clear, specific content brief descriptions
- Return ONLY a JSON array, nothing else

EXAMPLE OUTPUT:
["differences between true agents and node-based builders", "AgentKit and what it means for workflow builders"]

YOUR OUTPUT (JSON array only):"""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": resolution_prompt}]
            )

            # Extract JSON array from response
            response_text = response.content[0].text.strip()

            # Parse JSON
            import json
            topics = json.loads(response_text)

            if isinstance(topics, list) and len(topics) > 0:
                print(f"🔍 Resolved '{vague_reference}' to: {topics}")
                return topics
            else:
                return None

        except Exception as e:
            print(f"❌ Error resolving vague topic: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _load_brand_context(self, user_id: str) -> str:
        """
        Load brand context for user (from DB or default)

        Args:
            user_id: Slack user ID

        Returns:
            Brand context string
        """
        # TODO: Load from user preferences table
        # For now, return default context
        return """
You are writing for a B2B SaaS marketing team.

BRAND VOICE:
- Direct and specific (numbers, examples, timelines)
- Conversational but professional
- Value-first (lead with insight)
- Avoid hype and AI clichés

WRITING STYLE:
- Short paragraphs (2-3 lines max)
- Concrete over abstract
- Actionable insights
- Mobile-friendly formatting
"""

    def get_calendar_preview(self, user_id: str, days: int = 7) -> str:
        """
        Get scheduled content for next N days

        Args:
            user_id: Slack user ID
            days: Number of days to preview

        Returns:
            Formatted calendar preview
        """
        scheduled = self.memory.get_recent_scheduled(days=days)

        if not scheduled:
            return f"📅 *Upcoming {days} Days*\n\nNo content scheduled yet."

        sections = [f"📅 *Upcoming {days} Days*\n"]

        for item in scheduled:
            platform = item.get('platform', 'unknown').capitalize()
            score = item.get('latest_score', 0)
            preview = item.get('latest_draft', '')[:60] + "..."
            updated = item.get('updated_at', '')

            sections.append(f"• *{platform}* ({score}/100)")
            sections.append(f"  _{preview}_")
            sections.append(f"  Scheduled: {updated}")
            sections.append("")

        return "\n".join(sections)


# Utility function to detect content vs strategy requests
def is_content_request(message: str) -> bool:
    """
    Detect if message is content creation request vs strategy request

    Args:
        message: Message text

    Returns:
        True if content request, False if strategy request
    """
    message_lower = message.lower()

    # Content trigger words - must be explicit requests
    content_triggers = [
        'write a', 'create a', 'draft a', 'make a', 'generate a',
        'write me', 'create me', 'draft me', 'make me',
        'linkedin post about', 'twitter thread about', 'tweet about',
        'email about', 'content about', 'post about'
    ]

    # Strategy trigger words (existing CMO agent)
    strategy_triggers = [
        'plan', 'strategy', 'analyze', 'research',
        'execute plan', 'what should', 'help me think'
    ]

    # Check for content triggers
    has_content_trigger = any(trigger in message_lower for trigger in content_triggers)

    # Check for strategy triggers
    has_strategy_trigger = any(trigger in message_lower for trigger in strategy_triggers)

    # Content wins if both present (e.g., "write a content plan")
    if has_content_trigger:
        return True

    if has_strategy_trigger:
        return False

    # Don't trigger content creation just for mentioning platforms
    # Only if explicitly asking for content (with trigger words)
    return False

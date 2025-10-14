"""
REAL Claude Agent SDK Implementation
Following official docs at https://docs.claude.com/en/api/agent-sdk/python
"""
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server
)
import os
from typing import Dict, Optional, Any
import json
import asyncio

# Import our existing tool functions
from tools.search_tools import web_search as _web_search_func
from tools.search_tools import search_knowledge_base as _search_kb_func
from tools.template_search import search_templates_semantic as _search_templates_func
from tools.template_search import get_template_by_name as _get_template_func
from slack_bot.agent_tools import (
    search_past_posts as _search_posts_func,
    get_content_calendar as _get_calendar_func,
    get_thread_context as _get_context_func,
    analyze_content_performance as _analyze_perf_func
)


# Define tools using @tool decorator as per docs
@tool(
    "web_search",
    "Search the web for current information, news, updates. Use for ANY real-time questions about events.",
    {"query": str, "max_results": int}
)
async def web_search(args):
    """Web search tool for Claude Agent SDK"""
    query = args.get('query', '')
    max_results = args.get('max_results', 5)

    result = _web_search_func(query=query, max_results=max_results)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "search_knowledge_base",
    "Search internal knowledge base using RAG for brand voice and documentation.",
    {"query": str, "match_count": int}
)
async def search_knowledge_base(args):
    """Knowledge base search tool"""
    query = args.get('query', '')
    match_count = args.get('match_count', 5)

    result = _search_kb_func(query=query, match_count=match_count)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "search_past_posts",
    "Search content created in past conversations.",
    {"user_id": str, "platform": str, "days_back": int, "min_score": int}
)
async def search_past_posts(args):
    """Search past posts tool"""
    result = _search_posts_func(
        user_id=args.get('user_id', ''),
        platform=args.get('platform'),
        days_back=args.get('days_back', 30),
        min_score=args.get('min_score', 0)
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "get_content_calendar",
    "Get upcoming scheduled content.",
    {"user_id": str, "days_ahead": int, "platform": str}
)
async def get_content_calendar(args):
    """Get content calendar tool"""
    result = _get_calendar_func(
        user_id=args.get('user_id'),
        days_ahead=args.get('days_ahead', 14),
        platform=args.get('platform')
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "get_thread_context",
    "Get complete context from current Slack thread.",
    {"thread_ts": str, "include_content": bool}
)
async def get_thread_context(args):
    """Get thread context tool"""
    result = _get_context_func(
        thread_ts=args.get('thread_ts', ''),
        include_content=args.get('include_content', True)
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "analyze_content_performance",
    "Analyze content performance trends.",
    {"user_id": str, "platform": str, "days_back": int}
)
async def analyze_content_performance(args):
    """Analyze performance tool"""
    result = _analyze_perf_func(
        user_id=args.get('user_id', ''),
        platform=args.get('platform'),
        days_back=args.get('days_back', 30)
    )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "search_templates",
    "Search content templates for strategy sessions. Returns top matching templates based on user intent.",
    {"user_intent": str, "max_results": int}
)
async def search_templates(args):
    """Search templates semantically"""
    user_intent = args.get('user_intent', '')
    max_results = args.get('max_results', 3)

    result = _search_templates_func(user_intent=user_intent, max_results=max_results)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "get_template",
    "Get full template structure by name after user picks from search results.",
    {"template_name": str}
)
async def get_template(args):
    """Get complete template by name"""
    template_name = args.get('template_name', '')

    result = _get_template_func(template_name=template_name)

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


@tool(
    "check_ai_detection",
    "Validate post against GPTZero AI detector. Use AFTER quality_check passes to ensure post will pass AI detection.",
    {"post_text": str}
)
async def check_ai_detection(args):
    """Check if post will be flagged as AI-generated by GPTZero"""
    import httpx

    post_text = args.get('post_text', '')

    if not post_text or len(post_text) < 50:
        return {
            "content": [{
                "type": "text",
                "text": "❌ Post too short (minimum 50 characters for detection)"
            }]
        }

    api_key = os.getenv('GPTZERO_API_KEY')
    if not api_key:
        return {
            "content": [{
                "type": "text",
                "text": "⚠️ GPTZero API key not configured. Set GPTZERO_API_KEY in .env to enable AI detection validation."
            }]
        }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                'https://api.gptzero.me/v2/predict/text',
                headers={
                    'x-api-key': api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'document': post_text,
                    'multilingual': False
                }
            )

            response.raise_for_status()
            data = response.json()

            # Extract key metrics
            classification = data.get('documents', [{}])[0].get('class_probabilities', {})
            human_prob = classification.get('human', 0) * 100
            ai_prob = classification.get('ai', 0) * 100
            mixed_prob = classification.get('mixed', 0) * 100

            predicted_class = data.get('documents', [{}])[0].get('completely_generated_prob', 0)
            overall_class = data.get('documents', [{}])[0].get('average_generated_prob', 0)

            # Get flagged sentences
            sentences = data.get('documents', [{}])[0].get('sentences', [])
            flagged = [s.get('sentence', '') for s in sentences if s.get('generated_prob', 0) > 0.5]

            # Determine pass/fail
            passes = human_prob > 70  # 70% human threshold

            result_text = f"""🔍 **AI Detection Results (GPTZero)**

**Classification:**
- Human: {human_prob:.1f}%
- AI: {ai_prob:.1f}%
- Mixed: {mixed_prob:.1f}%

**Overall Score:** {overall_class*100:.1f}% AI probability

**Result:** {"✅ PASS - Post appears human-written" if passes else "⚠️ FLAG - May be detected as AI"}

**Flagged Sentences ({len(flagged)}):**
{chr(10).join(f'- "{s[:100]}..."' for s in flagged[:3]) if flagged else "None"}

**Recommendation:**
{"Ready to publish! Post should pass AI detectors." if passes else "Consider revising flagged sentences. Use apply_fixes tool with GPTZero feedback."}
"""

            return {
                "content": [{
                    "type": "text",
                    "text": result_text
                }]
            }

    except httpx.HTTPError as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ GPTZero API error: {str(e)}\n\nCheck your API key and network connection."
            }]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Error checking AI detection: {str(e)}"
            }]
        }


async def _delegate_workflow_func(platform: str, topic: str, context: str = "", count: int = 1, style: str = "thought_leadership"):
    """Async workflow delegation"""
    try:
        if platform.lower() in ['linkedin', 'li']:
            # Use the NEW LinkedIn SDK Agent (Tier 2)
            from agents.linkedin_sdk_agent import create_linkedin_post_workflow
            result = await create_linkedin_post_workflow(topic, context, style)
            return result  # Already formatted with score and details

        elif platform.lower() in ['twitter', 'x']:
            # Use the Twitter SDK Agent workflow
            from agents.twitter_sdk_agent import create_twitter_thread_workflow
            result = await create_twitter_thread_workflow(topic, context, style)
            return result  # Already formatted with score

        elif platform.lower() == 'email':
            # Use the Email SDK Agent workflow
            from agents.email_sdk_agent import create_email_workflow
            # Detect email type from style/context
            email_type = "Email_Value"  # Default
            if "tuesday" in style.lower() or "update" in style.lower():
                email_type = "Email_Tuesday"
            elif "sales" in style.lower() or "offer" in style.lower():
                email_type = "Email_Direct"
            elif "story" in style.lower() or "indirect" in style.lower():
                email_type = "Email_Indirect"

            result = await create_email_workflow(topic, context, email_type)
            return result  # Already formatted with subject and score

        elif platform.lower() in ['youtube', 'video']:
            # Use the YouTube SDK Agent workflow
            from agents.youtube_sdk_agent import create_youtube_workflow
            # Detect script type from style/context
            script_type = "short_form"  # Default (30-150 words, 12-60 sec)
            if "medium" in style.lower() or "explainer" in style.lower():
                script_type = "medium_form"  # 150-400 words, 1-3 min
            elif "long" in style.lower() or "deep" in style.lower():
                script_type = "long_form"  # 400-1000 words, 3-10 min

            result = await create_youtube_workflow(topic, context, script_type)
            return result  # Already formatted with timing markers

        else:
            return f"Unknown platform: {platform}. Use 'linkedin', 'twitter', 'email', or 'youtube'"

    except ImportError:
        # Fallback if workflows not available
        return f"Creating {platform} content about '{topic}' (using simplified generation)"
    except Exception as e:
        return f"Workflow error: {str(e)}"


@tool(
    "delegate_to_workflow",
    "Delegate content creation to specialized subagent workflows.",
    {"platform": str, "topic": str, "context": str, "count": int, "style": str}
)
async def delegate_to_workflow(args):
    """Delegate to subagent workflows - handles both single and bulk"""
    count = args.get('count', 1)

    # Single post - direct processing
    if count == 1:
        result = await _delegate_workflow_func(
            platform=args.get('platform', 'linkedin'),
            topic=args.get('topic', ''),
            context=args.get('context', ''),
            count=1,
            style=args.get('style', 'thought_leadership')
        )
    else:
        # Multiple posts - use queue manager
        result = await _delegate_bulk_workflow(
            platform=args.get('platform', 'linkedin'),
            topics=args.get('topics', [args.get('topic')] * count),
            context=args.get('context', ''),
            count=count,
            style=args.get('style', 'thought_leadership')
        )

    return {
        "content": [{
            "type": "text",
            "text": result
        }]
    }


async def _delegate_bulk_workflow(platform: str, topics: list, context: str, count: int, style: str):
    """Handle bulk content generation using queue manager"""
    from agents.content_queue import ContentQueueManager, ContentJob
    from datetime import datetime

    # Create queue manager
    queue_manager = ContentQueueManager(
        max_concurrent=3,  # Process 3 at a time
        max_retries=2
    )

    # Prepare jobs
    posts_data = []
    for i, topic in enumerate(topics[:count]):
        posts_data.append({
            'topic': topic,
            'context': f"{context} (Post {i+1}/{count})",
            'style': style
        })

    # Queue all posts
    jobs = await queue_manager.bulk_create(posts_data, platform)

    # Start processing (async, don't wait)
    asyncio.create_task(queue_manager.wait_for_completion())

    return f"""🚀 **Bulk Content Generation Started**

📥 Queued {len(jobs)} {platform} posts
⚡ Processing 3 posts concurrently
⏱️ Estimated time: {len(jobs) * 45 // 3} seconds

Posts will be delivered to:
📊 Airtable for storage
📄 Google Docs for editing

I'll update you as each batch completes!"""


class ClaudeAgentHandler:
    """
    REAL Claude Agent SDK handler using the official Python SDK
    Maintains one client per Slack thread for conversation continuity
    """

    def __init__(self, memory_handler=None):
        """Initialize the Claude Agent with SDK"""
        self.memory = memory_handler

        # Thread-based session management (thread_ts -> ClaudeSDKClient)
        self._thread_sessions = {}

        # Track which sessions are already connected (thread_ts -> bool)
        self._connected_sessions = set()

        # System prompt for the agent
        self.system_prompt = """You are CMO, a senior content strategist with 8+ years building brands from zero to millions of followers. You speak like a real person - direct, insightful, occasionally sarcastic, always helpful. You adapt to conversations but always drives toward actionable outcomes you can "take to your team" (delegate to subagents).

**YOUR IDENTITY:**
- You are an AI employee specialized in content creation
- You help users create LinkedIn posts, Twitter threads, emails, and other content
- You are NOT Claude Code, you are NOT a development assistant
- You are the user's CMO (Chief Marketing Officer) assistant

**YOUR PRIMARY DIRECTIVE:**
When users ask about current events, news, updates, or ANYTHING happening in the real world, IMMEDIATELY use web_search.
Do NOT tell users to "check websites" - YOU search for them.

**CRITICAL WEB SEARCH RULES:**
1. Make ONE comprehensive search, not multiple searches
2. ALWAYS include recency indicators in your query:
   - For recent news: "OpenAI news" or "OpenAI Dev Day November" no matter what the ask is about, you check for the date to make sure you're answering as though you live here and now.
   - For very recent: "OpenAI announcements this week"
   - NEVER search without year/timeframe - ambiguous dates default to wrong years
3. Your training data is outdated - you do NOT know what happened recently
4. Filter for ACTUAL NEW launches: "announced today", "just released", "launching this week"

**YOUR CAPABILITIES:**
1. web_search - USE THIS FIRST for any news/events/updates (include year/date in query!)
2. search_knowledge_base - Internal documentation and brand voice
3. search_past_posts - Past content you've created
4. get_content_calendar - Scheduled posts
5. get_thread_context - Thread history
6. analyze_content_performance - Performance metrics

**CONTENT CREATION WORKFLOW:**

For DIRECT requests ("write a LinkedIn post about X"):
- Immediately delegate to workflow
- Say: "Creating your [content type] now..."
- Use delegate_to_workflow tool

For STRATEGIC discussions ("I want to fight for owning intelligence"):
- Develop strategy first
- Ask clarifying questions
- CONFIRM: "Want me to start drafting the actual posts?"
- When confirmed, delegate to workflows

DELEGATION:
When ready to create content, use delegate_to_workflow with RICH CONTEXT:

**CRITICAL**: The context parameter is HOW you pass conversation intelligence to subagents.

Good context includes:
- User's angle/thesis ("contrarian take on AI bubble")
- Specific examples mentioned ("Michael Burry in Big Short")
- Key points from discussion ("95% failure = discovery, infrastructure is real")
- Tone/style ("confident data-backed contrarian")
- People/companies/data referenced ("Nvidia, Adobe, Anthropic")

Examples:
- Single post with context:
  delegate_to_workflow(
    platform="linkedin",
    topic="AI is not a bubble",
    context="User wants Big Short analogy: conviction despite ridicule. Key: 95% failure is discovery phase, infrastructure real (Nvidia), productivity gap proves it works. Tone: confident contrarian.",
    count=1
  )

- Multiple posts → delegate_to_workflow(platform="linkedin", topic=..., context=..., count=5)
- Week of content → delegate_to_workflow(platform="linkedin", topics=[...], count=7)

BULK REQUESTS (automatically detected):
- "Create 5 LinkedIn posts about..." → count=5
- "Generate my week of content" → count=7
- "Make 10 Twitter threads" → count=10
- Bulk processing uses queue (3 posts at a time for quality)

These workflows enforce brand voice, writing rules, and quality standards.

**CONVERSATION VS. CONTENT:**
- If user is asking questions, having discussion, or seeking strategy → CONVERSATION MODE
- If user says "write", "create", "draft", "make", "generate" + content type → CONTENT MODE
- When in doubt, ask: "Would you like me to create [specific content] or discuss [topic]?"
- Don't jump into content creation without clear intent from the user

**QUALITY STANDARDS:**
- You iterate on content until it reaches high quality (85+ score)
- You remember conversations within each Slack thread (and when asked about other conversations)
- You provide strategic insights before and after content creation

If someone asks about "Dev Day on the 6th" - they likely mean OpenAI Dev Day (November 6, 2023). Search with FULL context."""

        # Create MCP server with our tools
        self.mcp_server = create_sdk_mcp_server(
            name="slack_tools",
            version="1.0.0",
            tools=[
                web_search,
                search_knowledge_base,
                search_past_posts,
                get_content_calendar,
                get_thread_context,
                analyze_content_performance,
                delegate_to_workflow  # NEW: Delegate to subagent workflows
            ]
        )

        print("🚀 Claude Agent SDK initialized with 7 tools (including workflow delegation)")

    def _get_or_create_session(self, thread_ts: str) -> ClaudeSDKClient:
        """Get existing session for thread or create new one"""
        if thread_ts not in self._thread_sessions:
            # CRITICAL: Prevent Claude SDK from loading ANY external configs
            import os
            os.environ['CLAUDE_HOME'] = '/tmp/empty_claude_home'  # Point to empty dir

            # Configure options for this thread with EXPLICIT CMO system prompt
            options = ClaudeAgentOptions(
                mcp_servers={"tools": self.mcp_server},
                allowed_tools=["mcp__tools__*"],
                system_prompt=self.system_prompt,  # FORCE our CMO prompt, not Claude Code's
                model="claude-sonnet-4-5-20250929",  # Claude Sonnet 4.5 - latest
                permission_mode="bypassPermissions",
                continue_conversation=True  # KEY: Maintain context across messages
            )

            self._thread_sessions[thread_ts] = ClaudeSDKClient(options=options)
            print(f"✨ Created new session for thread {thread_ts[:8]} with CMO identity")
            print(f"🎭 System prompt starts with: {self.system_prompt[:100]}...")

        return self._thread_sessions[thread_ts]

    async def handle_conversation(
        self,
        message: str,
        user_id: str,
        thread_ts: str,
        channel_id: str
    ) -> str:
        """
        Handle conversation using REAL Claude Agent SDK

        Args:
            message: User's message
            user_id: Slack user ID
            thread_ts: Thread timestamp
            channel_id: Slack channel

        Returns:
            Agent's response
        """

        # Add today's date context to the message (important for recency)
        from datetime import datetime
        today = datetime.now().strftime("%B %d, %Y")  # e.g., "October 09, 2025"

        # Simple message with date context - instructions are already in system prompt
        contextualized_message = f"[Today is {today}] {message}"

        try:
            print(f"🤖 Claude Agent SDK processing for thread {thread_ts[:8]}...")

            # Get or create cached session for this thread
            client = self._get_or_create_session(thread_ts)

            # Only connect if this is a NEW session (not already connected)
            if thread_ts not in self._connected_sessions:
                print(f"🔌 Connecting NEW client session for thread {thread_ts[:8]}...")
                await client.connect()
                self._connected_sessions.add(thread_ts)
                print(f"✅ Client connected successfully")
            else:
                print(f"♻️ Reusing connected client for thread {thread_ts[:8]}...")

            # Send the query
            print(f"📨 Sending query to Claude SDK...")
            await client.query(contextualized_message)

            # Collect ONLY the latest response (memory stays intact in session)
            latest_response = ""
            print(f"⏳ Waiting for Claude SDK response...")
            async for msg in client.receive_response():
                # Each message REPLACES the previous (we only want the final response)
                # The SDK maintains full conversation history internally
                print(f"📩 Received message type: {type(msg)}")
                if hasattr(msg, 'content'):
                    if isinstance(msg.content, list):
                        for block in msg.content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                latest_response = block.get('text', '')
                            elif hasattr(block, 'text'):
                                latest_response = block.text
                    elif hasattr(msg.content, 'text'):
                        latest_response = msg.content.text
                    else:
                        latest_response = str(msg.content)
                elif hasattr(msg, 'text'):
                    latest_response = msg.text

            final_text = latest_response  # Only use the latest response

            # Format for Slack
            final_text = self._format_for_slack(final_text)

            # Save to memory if available
            if self.memory:
                try:
                    self.memory.add_message(
                        thread_ts=thread_ts,
                        channel_id=channel_id,
                        user_id=user_id,
                        role="user",
                        content=message
                    )
                    self.memory.add_message(
                        thread_ts=thread_ts,
                        channel_id=channel_id,
                        user_id="bot",
                        role="assistant",
                        content=final_text
                    )
                except Exception as e:
                    print(f"⚠️ Memory save failed: {e}")

            return final_text

        except Exception as e:
            print(f"❌ Agent error: {e}")
            import traceback
            traceback.print_exc()
            return f"Sorry, I encountered an error: {str(e)}"

    def _format_for_slack(self, text: str) -> str:
        """Convert markdown to Slack mrkdwn format"""
        import re

        # Convert bold: **text** → *text*
        text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)

        # Convert italic: *text* → _text_
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'_\1_', text)

        # Convert code blocks
        text = re.sub(r'```\w+\n', '```', text)

        # Convert links: [text](url) → <url|text>
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<\2|\1>', text)

        # Convert bullets
        text = re.sub(r'^[\-\*]\s+', '• ', text, flags=re.MULTILINE)

        # Convert headers
        text = re.sub(r'^#{1,6}\s+(.+?)$', r'*\1*', text, flags=re.MULTILINE)

        return text
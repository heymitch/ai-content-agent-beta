"""
Co-Write Handler - Standalone Interactive Content Creation
Activated via /cowrite slash command for iterative content crafting
"""

import asyncio
from typing import Optional, Dict, Any
from anthropic import Anthropic
from claude_agent_sdk import create_sdk_mcp_server, AgentSession
from slack_sdk import WebClient


class CoWriteHandler:
    """
    Standalone co-write session handler for /cowrite slash command

    Provides direct access to native tools for interactive content creation:
    - Generation tools (all 5 platforms)
    - Quality check + AI detection
    - RAG search for proof points and examples
    - Manual save to Airtable (only on approval)
    """

    def __init__(
        self,
        user_id: str,
        channel_id: str,
        thread_ts: str,
        slack_client: WebClient
    ):
        """Initialize co-write handler with dedicated SDK session"""
        self.user_id = user_id
        self.channel_id = channel_id
        self.thread_ts = thread_ts
        self.slack_client = slack_client

        # Create MCP server with all co-write tools
        self.mcp_server = self._create_cowrite_mcp_server()

        # Create SDK session
        self.sdk_session = None  # Lazy-loaded on first use

    def _create_cowrite_mcp_server(self):
        """Create MCP server with all co-write tools loaded"""
        from slack_bot.cowrite_tools import get_cowrite_tools
        from slack_bot.claude_agent_handler import (
            search_company_documents,
            search_content_examples,
            check_ai_detection,
            send_to_calendar
        )

        # Base tools: RAG search, AI detection, manual save
        base_tools = [
            search_company_documents,
            search_content_examples,
            check_ai_detection,
            send_to_calendar  # Only saves when user explicitly approves
        ]

        # Co-write tools: generation, quality_check, apply_fixes (all platforms)
        cowrite_tools = get_cowrite_tools()

        # Combine all tools
        all_tools = base_tools + cowrite_tools

        # Create MCP server
        return create_sdk_mcp_server(
            name="cowrite_tools",
            version="1.0.0",
            tools=all_tools
        )

    def _create_system_prompt(self) -> str:
        """System prompt for co-write session"""
        return """You are a content co-writing assistant in interactive mode.

**YOUR ROLE:**
Help the user craft high-quality content through iterative collaboration.

**WORKFLOW:**
1. Generate initial draft using `generate_post_{platform}`
2. Run quality check using `quality_check_{platform}`
3. Share both draft and analysis with user
4. Iterate based on their feedback using `apply_fixes_{platform}`
5. Use RAG search tools for proof points and examples:
   - `search_company_documents` - User's case studies/testimonials
   - `search_content_examples` - 700+ high-performing examples
6. When user approves, use `send_to_calendar` to save

**CRITICAL RULES:**
- Do NOT auto-save to Airtable
- Only use `send_to_calendar` when user explicitly says "approve", "send to calendar", "looks good", etc.
- Show quality scores and AI detection results
- Iterate as many times as user wants
- Be conversational and collaborative

**TOOLS AVAILABLE:**
- Generation: generate_post_{platform}
- Quality: quality_check_{platform}
- Fixes: apply_fixes_{platform}
- RAG: search_company_documents, search_content_examples
- AI Detection: check_ai_detection
- Save: send_to_calendar (manual approval only)

Start by generating a draft based on the user's topic."""

    async def _get_or_create_session(self) -> AgentSession:
        """Lazy-load SDK session"""
        if self.sdk_session is None:
            anthropic_client = Anthropic()
            self.sdk_session = AgentSession(
                client=anthropic_client,
                mcp_server=self.mcp_server,
                model="claude-sonnet-4-5-20250929",
                system_prompt=self._create_system_prompt()
            )
        return self.sdk_session

    async def start_session(self, platform: str, topic: str) -> str:
        """
        Initialize co-write session and generate first draft

        Args:
            platform: linkedin, twitter, email, youtube, instagram
            topic: Content brief/topic

        Returns:
            Initial response from Claude (draft + quality analysis)
        """
        # Validate platform
        valid_platforms = ['linkedin', 'twitter', 'email', 'youtube', 'instagram']
        if platform.lower() not in valid_platforms:
            return f"❌ Invalid platform: {platform}. Use: {', '.join(valid_platforms)}"

        # Create initial prompt
        initial_prompt = f"""Start a co-write session for {platform}.

**Topic:** {topic}

Please:
1. Generate a draft using generate_post_{platform}
2. Run quality_check_{platform} to analyze it
3. Share both the draft and quality analysis with me
4. Ask if I want to iterate or approve

Remember: Do NOT auto-save. Only save when I explicitly approve."""

        # Send to Slack as starting message
        self.slack_client.chat_postMessage(
            channel=self.channel_id,
            thread_ts=self.thread_ts,
            text=f"🎨 Starting co-write session for **{platform}**\n\n📝 Topic: {topic}\n\n⏳ Generating draft..."
        )

        # Get SDK session
        session = await self._get_or_create_session()

        # Send message and get response
        try:
            response = await asyncio.wait_for(
                session.send_message(initial_prompt),
                timeout=180.0  # 3 minutes for generation + quality check
            )

            # Send response to Slack
            self.slack_client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=self.thread_ts,
                text=response
            )

            return response

        except asyncio.TimeoutError:
            error_msg = "⏱️ Session timed out after 3 minutes. Please try again."
            self.slack_client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=self.thread_ts,
                text=error_msg
            )
            return error_msg

    async def handle_user_message(self, message: str) -> str:
        """
        Handle user feedback/iteration during co-write session

        Args:
            message: User's feedback or instruction

        Returns:
            Claude's response
        """
        session = await self._get_or_create_session()

        try:
            response = await asyncio.wait_for(
                session.send_message(message),
                timeout=120.0  # 2 minutes for iteration
            )

            # Send to Slack
            self.slack_client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=self.thread_ts,
                text=response
            )

            return response

        except asyncio.TimeoutError:
            error_msg = "⏱️ Response timed out. Please try again."
            self.slack_client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=self.thread_ts,
                text=error_msg
            )
            return error_msg

    def close_session(self):
        """Clean up SDK session"""
        if self.sdk_session:
            # SDK session cleanup (if needed)
            self.sdk_session = None


# Global registry of active co-write sessions (thread_ts -> handler)
_active_cowrite_sessions: Dict[str, CoWriteHandler] = {}


def get_or_create_cowrite_session(
    thread_ts: str,
    user_id: str,
    channel_id: str,
    slack_client: WebClient
) -> CoWriteHandler:
    """
    Get existing co-write session or create new one

    Args:
        thread_ts: Slack thread timestamp (session ID)
        user_id: User who started session
        channel_id: Slack channel
        slack_client: Slack WebClient

    Returns:
        CoWriteHandler instance
    """
    if thread_ts not in _active_cowrite_sessions:
        _active_cowrite_sessions[thread_ts] = CoWriteHandler(
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            slack_client=slack_client
        )

    return _active_cowrite_sessions[thread_ts]


def close_cowrite_session(thread_ts: str):
    """Close and clean up co-write session"""
    if thread_ts in _active_cowrite_sessions:
        _active_cowrite_sessions[thread_ts].close_session()
        del _active_cowrite_sessions[thread_ts]

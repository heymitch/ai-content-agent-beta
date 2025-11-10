#!/usr/bin/env python3
"""Test Claude Agent SDK searching company documents (simulates Slack bot behavior)"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv(override=True)

async def test_agent_sdk_search():
    """Test Agent SDK calling search_company_documents like the Slack bot does"""

    print("=" * 80)
    print("TESTING CLAUDE AGENT SDK COMPANY DOCUMENTS SEARCH")
    print("(Simulating Slack bot behavior)")
    print("=" * 80)

    from anthropic import Anthropic
    from claude_agent_sdk import create_sdk_mcp_server, AgentSession
    from tools.company_documents import search_company_documents

    # Create MCP server with search tool (like cowrite_handler does)
    print("\n1. Creating MCP server with search_company_documents tool...")

    mcp_server = create_sdk_mcp_server(
        name="test_search_tools",
        tools=[search_company_documents]
    )

    print("   ✅ MCP server created")

    # Create Agent SDK session (like Slack bot does)
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    print("\n2. Creating Agent SDK session...")

    session = AgentSession(
        client=client,
        model="claude-sonnet-4-5-20250929",
        mcp_servers=[mcp_server]
    )

    print("   ✅ Session created")
    print("\n3. Sending message to agent:")
    print("   'Search our company documents for case studies about AI agents automation'")
    print()
    print("-" * 80)

    # Send message that should trigger search
    response = await session.send(
        "Search our company documents for case studies or testimonials about AI agents and automation. Tell me what you find."
    )

    print("\n4. Agent response:")
    print("-" * 80)
    print(response)
    print("-" * 80)

    print("\n5. Check the output above for:")
    print("   - 🔗 Connecting to Supabase: [which URL?]")
    print("   - 🔍 Searching company_documents: [what query?]")
    print("   - ✅ RPC call completed: [how many results?]")
    print()
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_agent_sdk_search())

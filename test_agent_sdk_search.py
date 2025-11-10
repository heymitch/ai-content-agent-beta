#!/usr/bin/env python3
"""Test Claude Agent SDK searching company documents (simulates Slack bot behavior)"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv(override=True)

def test_agent_sdk_search():
    """Test Agent SDK calling search_company_documents like the Slack bot does"""

    print("=" * 80)
    print("TESTING CLAUDE AGENT SDK COMPANY DOCUMENTS SEARCH")
    print("(Simulating Slack bot behavior)")
    print("=" * 80)

    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server
    from tools.company_documents import search_company_documents as _search_func

    # Create wrapped tool (like claude_agent_handler does)
    print("\n1. Creating wrapped search_company_documents tool...")

    @tool(
        "search_company_documents",
        "Search user-uploaded company documents (case studies, testimonials, product docs)",
        {"query": str, "match_count": int, "document_type": str}
    )
    async def search_company_documents_tool(args):
        """Search company documents wrapper"""
        print(f"\n🔧 TOOL WRAPPER: search_company_documents called")
        print(f"   Args received: {args}")

        query = args.get('query', '')
        match_count = args.get('match_count', 3)
        document_type = args.get('document_type')

        print(f"   Calling search function with:")
        print(f"      query={query}")
        print(f"      match_count={match_count}")
        print(f"      document_type={document_type}")

        # Run blocking I/O in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: _search_func(
                query=query,
                match_count=match_count,
                document_type=document_type
            )
        )

        print(f"   Result length: {len(result) if result else 0}")
        print(f"   Result preview: {result[:200] if result else 'NONE'}")

        return {
            "content": [{
                "type": "text",
                "text": result
            }]
        }

    print("   ✅ Tool wrapped")

    # Create MCP server with tool
    print("\n2. Creating MCP server...")

    mcp_server = create_sdk_mcp_server(
        name="test_tools",
        tools=[search_company_documents_tool]
    )

    print("   ✅ MCP server created")

    # Create Agent SDK client (like Slack bot does)
    print("\n3. Creating Claude SDK client...")

    # SDK uses ANTHROPIC_API_KEY from environment automatically
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5-20250929",
        mcp_servers={"test_tools": mcp_server},
        allowed_tools=["mcp__test_tools__*"],
        permission_mode="bypassPermissions"
    )

    client = ClaudeSDKClient(options=options)

    print("   ✅ Client created")
    print("\n4. Sending message to agent:")
    print("   'Search our company documents for case studies about AI agents automation'")
    print()
    print("-" * 80)

    # Send message that should trigger search (synchronous in SDK)
    response = client.chat(
        "Search our company documents for case studies or testimonials about AI agents and automation. Tell me what you find."
    )

    print("\n5. Agent response:")
    print("-" * 80)
    print(response)
    print("-" * 80)

    print("\n6. Check the output above for:")
    print("   - 🔗 Connecting to Supabase: [which URL?]")
    print("   - 🔍 Searching company_documents: [what query?]")
    print("   - ✅ RPC call completed: [how many results?]")
    print()
    print("=" * 80)

if __name__ == "__main__":
    test_agent_sdk_search()

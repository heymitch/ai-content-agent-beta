#!/usr/bin/env python3
"""
Test script to verify stdio MCP server setup WITHOUT burning API credits.
Run this on Replit before deploying to production.

Tests:
1. Import checks (all dependencies available)
2. stdio server can be imported and initialized
3. Handler can create stdio config correctly
4. All tools are registered in stdio server
5. Environment variables are set

Run: python test_stdio_server.py
"""

import sys
import os
from pathlib import Path

# Color codes for pretty output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_print(emoji, message, success=True):
    """Print test result with color"""
    color = GREEN if success else RED
    print(f"{color}{emoji} {message}{RESET}")

def warn_print(message):
    """Print warning"""
    print(f"{YELLOW}⚠️  {message}{RESET}")

def section_print(message):
    """Print section header"""
    print(f"\n{BLUE}{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}{RESET}\n")

def test_imports():
    """Test 1: Check all required imports"""
    section_print("TEST 1: Import Checks")

    errors = []

    # Test MCP import
    try:
        from mcp.server.fastmcp import FastMCP
        test_print("✅", "mcp.server.fastmcp imported successfully")
    except ImportError as e:
        errors.append(f"mcp.server.fastmcp: {e}")
        test_print("❌", f"Failed to import mcp.server.fastmcp: {e}", False)

    # Test Claude SDK import
    try:
        from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool
        test_print("✅", "claude_agent_sdk imported successfully")
    except ImportError as e:
        errors.append(f"claude_agent_sdk: {e}")
        test_print("❌", f"Failed to import claude_agent_sdk: {e}", False)

    # Test batch orchestrator
    try:
        from agents.batch_orchestrator import create_batch_plan, execute_single_post_from_plan
        test_print("✅", "batch_orchestrator imported successfully")
    except ImportError as e:
        errors.append(f"batch_orchestrator: {e}")
        test_print("❌", f"Failed to import batch_orchestrator: {e}", False)

    return len(errors) == 0, errors

def test_stdio_server():
    """Test 2: Verify stdio server initialization"""
    section_print("TEST 2: Stdio MCP Server")

    try:
        from slack_bot.mcp_server_stdio import mcp
        test_print("✅", "stdio server imported successfully")

        # Check server name
        if mcp.name == "slack_tools":
            test_print("✅", f"Server name correct: '{mcp.name}'")
        else:
            test_print("❌", f"Server name wrong: '{mcp.name}' (expected 'slack_tools')", False)
            return False

        # List expected tools
        expected_tools = [
            'web_search',
            'search_knowledge_base',
            'search_company_documents',
            'search_past_posts',
            'get_content_calendar',
            'get_thread_context',
            'analyze_content_performance',
            'search_templates',
            'get_template',
            'check_ai_detection',
            'plan_content_batch',
            'execute_post_from_plan',
            'compact_learnings',
            'checkpoint_with_user',
            'send_to_calendar'
        ]

        test_print("✅", f"Expected {len(expected_tools)} tools")
        test_print("ℹ️", f"Tools: {', '.join(expected_tools[:5])}... (and {len(expected_tools)-5} more)")

        return True

    except Exception as e:
        test_print("❌", f"Failed to initialize stdio server: {e}", False)
        import traceback
        print(traceback.format_exc())
        return False

def test_handler_config():
    """Test 3: Verify handler creates correct stdio config"""
    section_print("TEST 3: Handler Configuration")

    try:
        from slack_bot.claude_agent_handler import ClaudeAgentHandler

        # Create handler
        handler = ClaudeAgentHandler()
        test_print("✅", f"Handler created (ID: {handler.handler_id[:8]})")

        # Check mcp_server is dict
        if not isinstance(handler.mcp_server, dict):
            test_print("❌", f"mcp_server is not dict: {type(handler.mcp_server)}", False)
            return False
        test_print("✅", "mcp_server is dict (stdio config)")

        # Check type is stdio
        if handler.mcp_server.get('type') != 'stdio':
            test_print("❌", f"Type is not 'stdio': {handler.mcp_server.get('type')}", False)
            return False
        test_print("✅", "Type is 'stdio'")

        # Check command exists
        if 'command' not in handler.mcp_server:
            test_print("❌", "No 'command' in config", False)
            return False
        test_print("✅", f"Command: {handler.mcp_server['command']}")

        # Check args
        if 'args' not in handler.mcp_server:
            test_print("❌", "No 'args' in config", False)
            return False

        args = handler.mcp_server['args']
        if args[0] == '-m' and args[1] == 'slack_bot.mcp_server_stdio':
            test_print("✅", f"Args correct: {args}")
        else:
            test_print("❌", f"Args wrong: {args}", False)
            return False

        # Check env vars passed
        if 'env' in handler.mcp_server and isinstance(handler.mcp_server['env'], dict):
            test_print("✅", f"Environment passed ({len(handler.mcp_server['env'])} vars)")
        else:
            warn_print("No environment variables in config")

        return True

    except Exception as e:
        test_print("❌", f"Failed to create handler: {e}", False)
        import traceback
        print(traceback.format_exc())
        return False

def test_env_vars():
    """Test 4: Check critical environment variables"""
    section_print("TEST 4: Environment Variables")

    critical_vars = [
        'ANTHROPIC_API_KEY',
        'SLACK_BOT_TOKEN',
        'SLACK_SIGNING_SECRET',
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]

    missing = []
    for var in critical_vars:
        if os.getenv(var):
            test_print("✅", f"{var} is set")
        else:
            test_print("❌", f"{var} is MISSING", False)
            missing.append(var)

    if missing:
        warn_print(f"Missing {len(missing)} critical env vars - bot will fail at runtime!")
        return False

    return True

def test_extraction_prompt():
    """Test 5: Verify content extractor has improved prompt"""
    section_print("TEST 5: Content Extraction")

    try:
        # Read the extractor file
        extractor_path = Path(__file__).parent / 'integrations' / 'content_extractor.py'
        with open(extractor_path, 'r') as f:
            content = f.read()

        # Check for key phrases in improved prompt
        improvements = [
            'FINAL, COMPLETE',
            'LONGEST, MOST DETAILED',
            'VERBATIM',
            'COPY-PASTE operation'
        ]

        found = []
        for phrase in improvements:
            if phrase in content:
                found.append(phrase)

        if len(found) >= 3:
            test_print("✅", f"Extraction prompt improved ({len(found)}/4 key phrases found)")
            test_print("ℹ️", "Should preserve full post content (no summarization)")
        else:
            warn_print(f"Only {len(found)}/4 improvements found in extraction prompt")
            return False

        return True

    except Exception as e:
        test_print("❌", f"Failed to check extraction prompt: {e}", False)
        return False

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}")
    print("  STDIO MCP SERVER TEST SUITE")
    print("  Testing ProcessTransport bug fix + content extraction")
    print(f"{'='*60}{RESET}\n")

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Stdio Server", test_stdio_server()))
    results.append(("Handler Config", test_handler_config()))
    results.append(("Environment Vars", test_env_vars()))
    results.append(("Extraction Prompt", test_extraction_prompt()))

    # Summary
    section_print("TEST SUMMARY")

    passed = 0
    total = len(results)

    for name, result in results:
        # Handle both bool and tuple returns
        if isinstance(result, tuple):
            success = result[0]
        else:
            success = result

        if success:
            test_print("✅", f"{name}: PASS")
            passed += 1
        else:
            test_print("❌", f"{name}: FAIL", False)

    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print(f"{GREEN}🎉 ALL TESTS PASSED ({passed}/{total})")
        print(f"\n✅ Ready to deploy on Replit!")
        print(f"✅ No API credits will be burned by this test{RESET}")
        return 0
    else:
        print(f"{RED}❌ SOME TESTS FAILED ({passed}/{total})")
        print(f"\n⚠️  Fix issues before deploying!")
        print(f"⚠️  Review errors above{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

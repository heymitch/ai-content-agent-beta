#!/usr/bin/env python3
"""
Smoke test for Claude Agent Handler
Quick verification that the agent can initialize and has correct structure
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that modules import without errors"""
    print("1️⃣ Testing imports...")
    try:
        from slack_bot.claude_agent_handler import ClaudeAgentHandler
        print("   ✅ ClaudeAgentHandler imported")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False


def test_instantiation():
    """Test that handler can be instantiated"""
    print("\n2️⃣ Testing instantiation...")
    try:
        from slack_bot.claude_agent_handler import ClaudeAgentHandler
        handler = ClaudeAgentHandler()
        print("   ✅ Handler instantiated")
        return handler
    except Exception as e:
        print(f"   ❌ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_structure(handler):
    """Test that handler has expected attributes and methods"""
    print("\n3️⃣ Testing structure...")

    checks = []

    # Check attributes
    attrs = ['_thread_sessions', '_processing_sessions', '_connected_sessions',
             'cowrite_mode', 'mcp_server']
    for attr in attrs:
        if hasattr(handler, attr):
            print(f"   ✅ Has attribute: {attr}")
            checks.append(True)
        else:
            print(f"   ❌ Missing attribute: {attr}")
            checks.append(False)

    # Check methods
    methods = ['handle_conversation', '_get_or_create_session', '_detect_cowrite_mode']
    for method in methods:
        if hasattr(handler, method) and callable(getattr(handler, method)):
            print(f"   ✅ Has method: {method}")
            checks.append(True)
        else:
            print(f"   ❌ Missing method: {method}")
            checks.append(False)

    return all(checks)


def test_session_cleanup():
    """Test that _processing_sessions cleanup is implemented"""
    print("\n4️⃣ Testing session cleanup logic...")

    from slack_bot.claude_agent_handler import ClaudeAgentHandler
    import inspect

    # Get the source code of handle_conversation
    source = inspect.getsource(ClaudeAgentHandler.handle_conversation)

    checks = []

    # Check that we add to _processing_sessions
    if '_processing_sessions.add' in source:
        print("   ✅ Sessions are tracked (_processing_sessions.add)")
        checks.append(True)
    else:
        print("   ❌ Sessions not tracked")
        checks.append(False)

    # Check that we remove from _processing_sessions
    if '_processing_sessions.discard' in source:
        print("   ✅ Sessions are cleaned up (_processing_sessions.discard)")
        checks.append(True)
    else:
        print("   ❌ Sessions not cleaned up (memory leak risk!)")
        checks.append(False)

    # Check that RequestContextManager is NOT used
    if 'RequestContextManager' not in source:
        print("   ✅ RequestContextManager removed (simplified)")
        checks.append(True)
    else:
        print("   ⚠️ RequestContextManager still present (should be removed)")
        checks.append(False)

    return all(checks)


def main():
    print("=" * 60)
    print("🧪 CLAUDE AGENT HANDLER - SMOKE TEST")
    print("=" * 60)

    results = []

    # Test 1: Import
    results.append(("Import", test_import()))

    # Test 2: Instantiation
    handler = test_instantiation()
    results.append(("Instantiation", handler is not None))

    if handler:
        # Test 3: Structure
        results.append(("Structure", test_structure(handler)))

        # Test 4: Session cleanup
        results.append(("Session Cleanup", test_session_cleanup()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {name:20s} {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL SMOKE TESTS PASSED!")
        print("   The agent structure looks good")
        print("   Safe to test in production")
    else:
        print("❌ SOME TESTS FAILED")
        print("   Fix issues before deploying")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()

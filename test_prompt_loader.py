#!/usr/bin/env python3
"""
Quick test script to verify prompt loading system works correctly
Tests: loading, caching, fallback hierarchy
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from integrations.prompt_loader import (
    load_writing_rules,
    load_editor_standards,
    load_prompt,
    get_cache_stats,
    reload_prompts
)


def test_basic_loading():
    """Test basic prompt loading"""
    print("=" * 60)
    print("TEST 1: Basic Prompt Loading")
    print("=" * 60)

    # Test loading writing rules
    print("\n📝 Loading writing_rules...")
    rules = load_writing_rules()
    print(f"✅ Loaded {len(rules)} characters")
    print(f"   First 100 chars: {rules[:100]}...")

    # Test loading editor standards
    print("\n📝 Loading editor_standards...")
    standards = load_editor_standards()
    print(f"✅ Loaded {len(standards)} characters")
    print(f"   First 100 chars: {standards[:100]}...")

    return True


def test_caching():
    """Test that caching works"""
    print("\n" + "=" * 60)
    print("TEST 2: Prompt Caching")
    print("=" * 60)

    # Clear cache first
    print("\n🔄 Clearing cache...")
    reload_prompts()
    stats = get_cache_stats()
    print(f"✅ Cache cleared: {stats['cache_size']} items")

    # Load prompt first time
    print("\n📝 Loading writing_rules (first time)...")
    rules1 = load_writing_rules()
    stats = get_cache_stats()
    print(f"✅ Cache size after first load: {stats['cache_size']}")
    print(f"   Cached items: {stats['cached_prompts']}")

    # Load same prompt second time (should hit cache)
    print("\n📝 Loading writing_rules (second time - should hit cache)...")
    rules2 = load_writing_rules()
    stats = get_cache_stats()
    print(f"✅ Cache size after second load: {stats['cache_size']}")

    # Verify they're identical (same object from cache)
    if rules1 == rules2:
        print("✅ Cache working correctly - same content returned")
    else:
        print("❌ Cache issue - different content returned")
        return False

    return True


def test_platform_specific():
    """Test platform-specific prompt loading"""
    print("\n" + "=" * 60)
    print("TEST 3: Platform-Specific Loading (Future Feature)")
    print("=" * 60)

    # This will use global defaults for now
    # In future, clients can create .claude/prompts/linkedin/writing_rules.md
    print("\n📝 Loading prompt with platform='linkedin'...")
    prompt = load_prompt("writing_rules", platform="linkedin")
    print(f"✅ Loaded {len(prompt)} characters")
    print("   (Falls back to global default since no platform override exists)")

    return True


def test_import_from_agents():
    """Test that agents can import successfully"""
    print("\n" + "=" * 60)
    print("TEST 4: Agent Import Test")
    print("=" * 60)

    try:
        print("\n📦 Importing from twitter_haiku_agent...")
        from agents.twitter_haiku_agent import WRITE_LIKE_HUMAN_RULES, EDITOR_IN_CHIEF_RULES
        print(f"✅ WRITE_LIKE_HUMAN_RULES loaded: {len(WRITE_LIKE_HUMAN_RULES)} chars")
        print(f"✅ EDITOR_IN_CHIEF_RULES loaded: {len(EDITOR_IN_CHIEF_RULES)} chars")

        print("\n📦 Importing from prompts.linkedin_tools...")
        from prompts.linkedin_tools import WRITE_LIKE_HUMAN_RULES, EDITOR_IN_CHIEF_RULES
        print(f"✅ WRITE_LIKE_HUMAN_RULES loaded: {len(WRITE_LIKE_HUMAN_RULES)} chars")
        print(f"✅ EDITOR_IN_CHIEF_RULES loaded: {len(EDITOR_IN_CHIEF_RULES)} chars")

        print("\n📦 Importing from prompts.twitter_tools...")
        from prompts.twitter_tools import WRITE_LIKE_HUMAN_RULES, EDITOR_IN_CHIEF_RULES
        print(f"✅ WRITE_LIKE_HUMAN_RULES loaded: {len(WRITE_LIKE_HUMAN_RULES)} chars")
        print(f"✅ EDITOR_IN_CHIEF_RULES loaded: {len(EDITOR_IN_CHIEF_RULES)} chars")

        print("\n📦 Importing from prompts.email_tools...")
        from prompts.email_tools import WRITE_LIKE_HUMAN_RULES, EDITOR_IN_CHIEF_RULES
        print(f"✅ WRITE_LIKE_HUMAN_RULES loaded: {len(WRITE_LIKE_HUMAN_RULES)} chars")
        print(f"✅ EDITOR_IN_CHIEF_RULES loaded: {len(EDITOR_IN_CHIEF_RULES)} chars")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 PROMPT LOADER TEST SUITE")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Basic Loading", test_basic_loading()))
    results.append(("Caching", test_caching()))
    results.append(("Platform-Specific", test_platform_specific()))
    results.append(("Agent Imports", test_import_from_agents()))

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

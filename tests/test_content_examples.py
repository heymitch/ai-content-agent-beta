#!/usr/bin/env python3
"""
Test the search_content_examples function directly
"""
import sys
sys.path.append('/Users/heymitch/ai-content-agent-template')

from tools.search_tools import search_content_examples

print("=" * 60)
print("Testing search_content_examples function")
print("=" * 60)

# Test 1: Simple query
print("\n📝 Test 1: Search for 'framework post'")
result = search_content_examples("framework post", match_count=3)
print(result)

# Test 2: Platform filter
print("\n📝 Test 2: Search LinkedIn posts about 'AI agents'")
result = search_content_examples("AI agents", platform="LinkedIn", match_count=3)
print(result)

# Test 3: Broad query
print("\n📝 Test 3: Search for 'testing'")
result = search_content_examples("testing", match_count=5)
print(result)

print("\n" + "=" * 60)
print("Tests complete")
print("=" * 60)

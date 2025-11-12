"""
Test hybrid search for company documents
Verify keyword + semantic search works for simple queries like "Joel"
"""
import json
from tools.company_documents import search_company_documents

def test_simple_name_search():
    """Test that searching for 'Joel' finds 'Joel lift-off OB' document"""
    print("\n" + "="*60)
    print("TEST: Simple name search for 'Joel'")
    print("="*60)

    result = search_company_documents("Joel", match_count=5)
    data = json.loads(result)

    print(f"\nResult success: {data['success']}")
    print(f"Matches found: {data['count']}")

    if data['matches']:
        print("\nMatched documents:")
        for match in data['matches']:
            print(f"  - Title: {match['title']}")
            print(f"    Type: {match.get('match_type', 'unknown')}")
            print(f"    Similarity: {match['similarity']}")
            print()
    else:
        print("\n⚠️ No matches found")

    return data

def test_verbose_query():
    """Test that verbose queries like 'Joel meeting notes' still work"""
    print("\n" + "="*60)
    print("TEST: Verbose query 'Joel meeting notes insights'")
    print("="*60)

    result = search_company_documents("Joel meeting notes insights takeaways discussion", match_count=5)
    data = json.loads(result)

    print(f"\nResult success: {data['success']}")
    print(f"Matches found: {data['count']}")

    if data['matches']:
        print("\nMatched documents:")
        for match in data['matches']:
            print(f"  - Title: {match['title']}")
            print(f"    Type: {match.get('match_type', 'unknown')}")
            print(f"    Similarity: {match['similarity']}")
            print()
    else:
        print("\n⚠️ No matches found")

    return data

if __name__ == "__main__":
    print("\n🧪 Testing Hybrid Search Implementation\n")

    # Test 1: Simple name
    result1 = test_simple_name_search()

    # Test 2: Verbose query (should extract "Joel" keyword)
    result2 = test_verbose_query()

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Simple search ('Joel'): {result1['count']} matches")
    print(f"Verbose search: {result2['count']} matches")

    if result1['count'] > 0 and result2['count'] > 0:
        print("\n✅ Hybrid search working correctly!")
    else:
        print("\n❌ Hybrid search needs debugging")
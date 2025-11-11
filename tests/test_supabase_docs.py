#!/usr/bin/env python3
"""Quick test to diagnose company_documents search issue"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv()

def test_supabase_documents():
    """Test Supabase company_documents table and RPC function"""

    print("=" * 80)
    print("SUPABASE COMPANY DOCUMENTS DIAGNOSTICS")
    print("=" * 80)

    # Initialize clients
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    print(f"\n1. Checking environment variables:")
    print(f"   SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"   SUPABASE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")
    print(f"   OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Missing'}")

    if not all([supabase_url, supabase_key, openai_key]):
        print("\n❌ Missing required environment variables!")
        return

    # Create clients
    supabase = create_client(supabase_url, supabase_key)
    openai_client = OpenAI(api_key=openai_key)

    print(f"\n2. Direct table query (checking if documents exist):")
    try:
        result = supabase.table('company_documents').select('*').limit(10).execute()
        print(f"   Found {len(result.data)} documents")

        if result.data:
            print(f"\n   Documents in table:")
            for i, doc in enumerate(result.data, 1):
                print(f"   {i}. Title: {doc.get('title', 'Untitled')}")
                print(f"      Type: {doc.get('document_type', 'unknown')}")
                print(f"      Status: {doc.get('status', 'unknown')}")
                print(f"      Searchable: {doc.get('searchable', False)}")
                print(f"      Has embedding: {'✅' if doc.get('embedding') else '❌'}")
                print(f"      Content length: {len(doc.get('content', ''))} chars")
                print()
        else:
            print(f"   ⚠️  No documents found in table!")

    except Exception as e:
        print(f"   ❌ Error querying table: {e}")
        return

    print(f"\n3. Testing RPC function (match_company_documents):")
    try:
        # Generate test embedding
        test_query = "AI agents automation"
        print(f"   Query: '{test_query}'")

        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=test_query
        )
        query_embedding = response.data[0].embedding
        print(f"   ✅ Generated embedding: {len(query_embedding)} dimensions")

        # Test RPC function
        rpc_result = supabase.rpc(
            'match_company_documents',
            {
                'query_embedding': query_embedding,
                'filter_type': None,
                'match_threshold': 0.5,
                'match_count': 5
            }
        ).execute()

        print(f"   RPC returned {len(rpc_result.data)} matches")

        if rpc_result.data:
            print(f"\n   Matched documents:")
            for i, match in enumerate(rpc_result.data, 1):
                print(f"   {i}. {match.get('title', 'Untitled')}")
                print(f"      Similarity: {match.get('similarity', 0):.3f}")
                print(f"      Type: {match.get('document_type', 'unknown')}")
                print()
        else:
            print(f"   ⚠️  RPC returned 0 matches")
            print(f"\n   Possible issues:")
            print(f"   - Documents missing embeddings")
            print(f"   - searchable = false on documents")
            print(f"   - RPC function has bugs")
            print(f"   - Similarity threshold too high (0.5)")

    except Exception as e:
        print(f"   ❌ Error calling RPC function: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n4. Testing with lower similarity threshold (0.3):")
    try:
        rpc_result = supabase.rpc(
            'match_company_documents',
            {
                'query_embedding': query_embedding,
                'filter_type': None,
                'match_threshold': 0.3,  # Lower threshold
                'match_count': 5
            }
        ).execute()

        print(f"   RPC returned {len(rpc_result.data)} matches with 0.3 threshold")
        if rpc_result.data:
            for match in rpc_result.data:
                print(f"   - {match.get('title')}: {match.get('similarity', 0):.3f}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_supabase_documents()

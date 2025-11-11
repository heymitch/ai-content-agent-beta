#!/usr/bin/env python3
"""
Direct test of Supabase connection and company_documents query
Run this on Replit to verify the connection works outside the agent
"""
import os
from supabase import create_client

# Get credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

print(f"Testing Supabase connection...")
print(f"URL: {supabase_url}")
print(f"Key: {supabase_key[:20]}..." if supabase_key else "Key: NOT SET")
print()

# Create client
try:
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Client created")
except Exception as e:
    print(f"❌ Failed to create client: {e}")
    exit(1)

# Test 1: Direct table query
print("\n--- Test 1: Direct table query ---")
try:
    result = supabase.table('company_documents').select('*').execute()
    print(f"✅ Query successful")
    print(f"   Found {len(result.data)} documents")
    for doc in result.data:
        print(f"   - {doc.get('title')}")
except Exception as e:
    print(f"❌ Query failed: {e}")

# Test 2: RPC function call
print("\n--- Test 2: RPC function call ---")
try:
    # Get an embedding from existing doc
    doc_result = supabase.table('company_documents').select('embedding').limit(1).execute()

    if doc_result.data and doc_result.data[0].get('embedding'):
        test_embedding = doc_result.data[0]['embedding']

        rpc_result = supabase.rpc(
            'match_company_documents',
            {
                'query_embedding': test_embedding,
                'filter_type': None,
                'match_threshold': 0.1,
                'match_count': 10
            }
        ).execute()

        print(f"✅ RPC call successful")
        print(f"   Found {len(rpc_result.data)} matches")
        for match in rpc_result.data:
            print(f"   - {match.get('title')} (similarity: {match.get('similarity', 0):.2f})")
    else:
        print("⚠️  No embeddings found in documents")

except Exception as e:
    print(f"❌ RPC call failed: {e}")

# Test 3: OpenAI embedding generation
print("\n--- Test 3: OpenAI embedding generation ---")
try:
    from openai import OpenAI
    openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input="testing"
    )

    query_embedding = response.data[0].embedding
    print(f"✅ Generated embedding ({len(query_embedding)} dimensions)")

    # Test with generated embedding
    rpc_result = supabase.rpc(
        'match_company_documents',
        {
            'query_embedding': query_embedding,
            'filter_type': None,
            'match_threshold': 0.1,
            'match_count': 10
        }
    ).execute()

    print(f"✅ Search with generated embedding successful")
    print(f"   Found {len(rpc_result.data)} matches")
    for match in rpc_result.data:
        print(f"   - {match.get('title')} (similarity: {match.get('similarity', 0):.2f})")

except Exception as e:
    print(f"❌ OpenAI test failed: {e}")

print("\n=== Tests complete ===")

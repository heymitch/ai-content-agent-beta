#!/usr/bin/env python3
"""Check which migrations have been applied"""

import os
from dotenv import load_dotenv

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    import sys
    try:
        # Try --user flag first (works in most environments including Nix)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '--user'])
    except subprocess.CalledProcessError:
        try:
            # Try --break-system-packages for some managed environments
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary', '--break-system-packages'])
        except subprocess.CalledProcessError:
            # Last resort: try without any flags
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'])
    import psycopg2

load_dotenv(override=True)

db_url = os.getenv('SUPABASE_DB_URL')
if not db_url:
    print("❌ SUPABASE_DB_URL not set")
    exit(1)

conn = psycopg2.connect(db_url)
cursor = conn.cursor()

print("=" * 80)
print("CHECKING MIGRATION STATUS")
print("=" * 80)

# Check if _migrations table exists
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = '_migrations'
    );
""")
exists = cursor.fetchone()[0]

if not exists:
    print("\n❌ _migrations table does not exist")
    print("   Bootstrap has never run successfully")
else:
    print("\n✅ _migrations table exists")
    print("\nApplied migrations:")

    cursor.execute("SELECT filename, applied_at FROM _migrations ORDER BY id;")
    rows = cursor.fetchall()

    if rows:
        for filename, applied_at in rows:
            print(f"   ✅ {filename} (applied {applied_at})")
    else:
        print("   (none)")

print("\n" + "=" * 80)
print("CHECKING CURRENT RPC FUNCTION")
print("=" * 80)

# Get the function definition
cursor.execute("""
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'match_company_documents';
""")

result = cursor.fetchone()
if result:
    func_def = result[0]
    print("\n✅ Function exists")
    print("\nChecking for semantic-first filter:")

    if "company_documents.document_type IS NULL" in func_def:
        print("   ✅ HAS the fix: 'document_type IS NULL' clause found")
    else:
        print("   ❌ MISSING the fix: old filter logic still in place")
        print("\nCurrent WHERE clause:")
        # Extract WHERE clause
        if "WHERE" in func_def:
            where_start = func_def.index("WHERE")
            where_end = func_def.index("ORDER BY") if "ORDER BY" in func_def else len(func_def)
            print(func_def[where_start:where_end])
else:
    print("\n❌ Function does NOT exist")

print("\n" + "=" * 80)
print("TESTING ACTUAL SEARCH FUNCTIONALITY")
print("=" * 80)

# Test search with filter_type to see if NULL documents are found
print("\n1. Testing company_documents search with filter...")

from supabase import create_client
from openai import OpenAI

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
openai_key = os.getenv('OPENAI_API_KEY')

if not all([supabase_url, supabase_key, openai_key]):
    print("   ⚠️  Missing API keys, skipping search test")
else:
    supabase = create_client(supabase_url, supabase_key)
    openai_client = OpenAI(api_key=openai_key)

    # Get embedding for test query
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input="AI agents automation"
    )
    query_embedding = response.data[0].embedding

    # Test with filter (should find NULL documents if fix is applied)
    result = supabase.rpc(
        'match_company_documents',
        {
            'query_embedding': query_embedding,
            'filter_type': 'case studies',
            'match_threshold': 0.5,
            'match_count': 5
        }
    ).execute()

    print(f"\n   Search with filter_type='case studies':")
    print(f"   Results: {len(result.data)} matches")

    if len(result.data) > 0:
        print("   ✅ SEARCH WORKING - documents found")
        for match in result.data[:3]:
            doc_type = match.get('document_type') or 'NULL'
            print(f"      - {match['title']}: similarity {match['similarity']:.3f}, type={doc_type}")
    else:
        # Check if ANY documents exist
        cursor.execute("SELECT COUNT(*) FROM company_documents WHERE status = 'active' AND searchable = true;")
        count = cursor.fetchone()[0]
        print(f"   ❌ SEARCH BROKEN - 0 results (but {count} active documents exist)")

print("\n2. Testing content_examples search...")

if supabase_url and supabase_key and openai_key:
    # Test content_examples search
    result = supabase.rpc(
        'search_content_examples',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.5,
            'match_count': 5
        }
    ).execute()

    print(f"\n   Search content_examples:")
    print(f"   Results: {len(result.data)} matches")

    if len(result.data) > 0:
        print("   ✅ CONTENT EXAMPLES SEARCHABLE")
        for match in result.data[:3]:
            print(f"      - Platform: {match.get('platform')}, similarity {match.get('similarity', 0):.3f}")
    else:
        cursor.execute("SELECT COUNT(*) FROM content_examples;")
        count = cursor.fetchone()[0]
        print(f"   ❌ CONTENT EXAMPLES NOT SEARCHABLE (but {count} examples exist)")

cursor.close()
conn.close()

print("\n" + "=" * 80)

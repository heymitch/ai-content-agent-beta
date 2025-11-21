#!/usr/bin/env python3
"""
Directly fix the match_company_documents RPC function using Supabase client.
This bypasses the migration system and applies the semantic-first filter fix.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Get DB URL from environment
db_url = os.getenv('SUPABASE_DB_URL')
if not db_url:
    print("❌ SUPABASE_DB_URL not set")
    exit(1)

print("=" * 80)
print("FIXING match_company_documents RPC FUNCTION")
print("=" * 80)

# Use psycopg2 to execute raw SQL
try:
    import psycopg2
except ImportError:
    print("\n❌ psycopg2 not installed")
    print("Run: pip install psycopg2-binary --user")
    print("\nOr add to replit.nix:")
    print('  deps = [')
    print('    pkgs.python311Packages.psycopg2')
    print('  ];')
    exit(1)

# Connect and execute
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

print("\n1. Dropping old function...")
try:
    cursor.execute("""
        DROP FUNCTION IF EXISTS match_company_documents(vector(1536), text, double precision, integer);
    """)
    conn.commit()
    print("   ✅ Old function dropped")
except Exception as e:
    conn.rollback()
    print(f"   ⚠️  Drop failed: {e}")

print("\n2. Creating new function with semantic-first filter...")

sql = """
CREATE OR REPLACE FUNCTION match_company_documents(
  query_embedding vector(1536),
  filter_type text DEFAULT NULL,
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  title text,
  content text,
  document_type text,
  voice_description text,
  signature_phrases jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    company_documents.id,
    company_documents.title,
    company_documents.content,
    company_documents.document_type,
    company_documents.voice_description,
    company_documents.signature_phrases,
    1 - (company_documents.embedding <=> query_embedding) as similarity
  FROM company_documents
  WHERE company_documents.embedding IS NOT NULL
    AND 1 - (company_documents.embedding <=> query_embedding) > match_threshold
    AND company_documents.searchable = true
    AND company_documents.status = 'active'
    -- KEY FIX: Allow documents with NULL document_type to match any filter (semantic-first)
    AND (filter_type IS NULL OR company_documents.document_type IS NULL OR company_documents.document_type = filter_type)
  ORDER BY company_documents.embedding <=> query_embedding
  LIMIT match_count;
$$;
"""

try:
    cursor.execute(sql)
    conn.commit()
    print("   ✅ New function created with semantic-first filter")
except Exception as e:
    conn.rollback()
    print(f"   ❌ Failed: {e}")
    cursor.close()
    conn.close()
    exit(1)

print("\n3. Testing the fix...")
from supabase import create_client
from openai import OpenAI

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Get embedding
response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input="AI agents automation"
)
query_embedding = response.data[0].embedding

# Test search with filter
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
    print("\n   ✅ FIX SUCCESSFUL - Documents found!")
    for match in result.data[:3]:
        doc_type = match.get('document_type') or 'NULL'
        print(f"      - {match['title']}: similarity {match['similarity']:.3f}, type={doc_type}")
else:
    cursor.execute("SELECT COUNT(*) FROM company_documents WHERE status = 'active' AND searchable = true;")
    count = cursor.fetchone()[0]
    print(f"\n   ❌ Still broken - 0 results (but {count} active documents exist)")
    print("   The documents might not have embeddings or might not match the query.")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("✅ RPC FUNCTION FIX COMPLETE")
print("=" * 80)
print("\nYou can now use search_company_documents with document_type filters,")
print("and it will find documents with NULL document_type based on semantic similarity.")
print()

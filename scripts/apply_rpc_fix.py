#!/usr/bin/env python3
"""Manually apply the RPC function fix to Supabase"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 80)
print("APPLYING RPC FUNCTION FIX TO SUPABASE")
print("=" * 80)

# Drop the old function
print("\n1. Dropping old match_company_documents function...")
drop_sql = """
DROP FUNCTION IF EXISTS match_company_documents(vector(1536), text, double precision, integer);
"""

try:
    supabase.rpc('exec_sql', {'query': drop_sql}).execute()
    print("   ✅ Old function dropped")
except Exception as e:
    print(f"   ⚠️  Drop failed (might not exist): {e}")

# Create the new function with fixed filter logic
print("\n2. Creating new match_company_documents function...")
create_sql = """
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

# Note: We can't use rpc('exec_sql') for CREATE FUNCTION, so we'll use psycopg2
print("   Using direct PostgreSQL connection...")

import psycopg2

db_url = os.getenv('SUPABASE_DB_URL')
if not db_url:
    print("   ❌ SUPABASE_DB_URL not set")
    print("   Set it in .env or Replit Secrets")
    exit(1)

conn = psycopg2.connect(db_url)
cursor = conn.cursor()

try:
    cursor.execute(create_sql)
    conn.commit()
    print("   ✅ New function created with semantic-first filter")
except Exception as e:
    conn.rollback()
    print(f"   ❌ Failed to create function: {e}")
    exit(1)
finally:
    cursor.close()
    conn.close()

print("\n3. Testing the fix...")
print("   Searching with filter='case studies' (should now find NULL documents)")

from openai import OpenAI
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input="AI agents automation"
)
query_embedding = response.data[0].embedding

result = supabase.rpc(
    'match_company_documents',
    {
        'query_embedding': query_embedding,
        'filter_type': 'case studies',
        'match_threshold': 0.5,
        'match_count': 5
    }
).execute()

print(f"\n   Results: {len(result.data)} matches")
if len(result.data) > 0:
    for match in result.data:
        print(f"      - {match['title']}: similarity {match['similarity']:.3f}, document_type={match['document_type']}")
else:
    print("      ⚠️  Still returning 0 matches - something else is wrong")

print("\n" + "=" * 80)
print("✅ RPC FIX APPLIED")
print("=" * 80)

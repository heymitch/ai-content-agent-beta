-- Migration 003 V2: Fix match_company_documents RPC (Defensive Version)
--
-- This version checks prerequisites and provides better error messages
--
-- PROBLEM: Original function filtered too strictly - excluded documents with
-- document_type = NULL when a specific type filter was provided.
--
-- SOLUTION: Allow NULL document_type to match ANY filter, making search semantic-first.
--
-- Applied: 2025-01-12

-- ============================================================================
-- STEP 1: Verify Prerequisites
-- ============================================================================

-- Check if vector extension exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
    RAISE EXCEPTION 'Vector extension not installed. Run: CREATE EXTENSION vector;';
  END IF;
END $$;

-- Check if company_documents table exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'company_documents') THEN
    RAISE EXCEPTION 'Table company_documents does not exist. Run migration 001_full_database.sql first.';
  END IF;
END $$;

-- Check if embedding column exists and is vector(1536)
DO $$
DECLARE
  col_type TEXT;
BEGIN
  SELECT data_type INTO col_type
  FROM information_schema.columns
  WHERE table_name = 'company_documents'
  AND column_name = 'embedding';

  IF col_type IS NULL THEN
    RAISE EXCEPTION 'Column company_documents.embedding does not exist';
  END IF;

  -- Note: vector type shows as USER-DEFINED in information_schema
  -- We'll trust it's the right dimension if it exists
END $$;

-- ============================================================================
-- STEP 2: Drop and Recreate Function
-- ============================================================================

-- Drop existing function (must match EXACT signature including vector dimension)
DROP FUNCTION IF EXISTS match_company_documents(vector(1536), text, double precision, integer);
DROP FUNCTION IF EXISTS match_company_documents(vector(1536), text, float, integer);
DROP FUNCTION IF EXISTS match_company_documents(vector(1536), text, real, integer);

-- Recreate with fixed filter logic
-- IMPORTANT: All types must EXACTLY match the table schema
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
    (1 - (company_documents.embedding <=> query_embedding))::float as similarity
  FROM company_documents
  WHERE company_documents.embedding IS NOT NULL
    AND (1 - (company_documents.embedding <=> query_embedding)) > match_threshold
    AND company_documents.searchable = true
    AND company_documents.status = 'active'
    -- KEY FIX: Allow documents with NULL document_type to match any filter (semantic-first)
    AND (filter_type IS NULL OR company_documents.document_type IS NULL OR company_documents.document_type = filter_type)
  ORDER BY company_documents.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- ============================================================================
-- STEP 3: Grant Permissions
-- ============================================================================

GRANT EXECUTE ON FUNCTION match_company_documents TO authenticated;
GRANT EXECUTE ON FUNCTION match_company_documents TO anon;
GRANT EXECUTE ON FUNCTION match_company_documents TO service_role;

-- ============================================================================
-- STEP 4: Verify Function Works
-- ============================================================================

-- Test with a dummy vector (should return 0 rows, but not error)
DO $$
DECLARE
  test_result RECORD;
BEGIN
  -- Create a test vector (all zeros)
  SELECT * INTO test_result
  FROM match_company_documents(
    array_fill(0::float, ARRAY[1536])::vector(1536),
    NULL,
    0.9,
    1
  )
  LIMIT 1;

  RAISE NOTICE '✅ Function match_company_documents verified successfully';
EXCEPTION
  WHEN OTHERS THEN
    RAISE EXCEPTION 'Function verification failed: %', SQLERRM;
END $$;
-- Migration 003: Fix match_company_documents RPC to handle NULL document_type
--
-- PROBLEM: Original function filtered too strictly - excluded documents with
-- document_type = NULL when a specific type filter was provided.
--
-- SOLUTION: Allow NULL document_type to match ANY filter, making search semantic-first.
-- This enables documents without explicit types to be found based on content relevance.
--
-- Applied: 2025-01-10

-- Drop existing function (required before recreating with same signature)
-- Note: Must match exact signature including vector dimension
DROP FUNCTION IF EXISTS match_company_documents(vector(1536), text, double precision, integer);

-- Recreate with fixed filter logic
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
  signature_phrases text[],
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

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION match_company_documents TO authenticated;
GRANT EXECUTE ON FUNCTION match_company_documents TO anon;
GRANT EXECUTE ON FUNCTION match_company_documents TO service_role;

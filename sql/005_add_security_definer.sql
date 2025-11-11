-- Migration 005: Add SECURITY DEFINER to RPC functions to bypass RLS
--
-- PROBLEM: RPC functions respect RLS policies, causing 0 results from Python
-- SQL Editor works because it bypasses RLS, but API calls don't
--
-- SOLUTION: Add SECURITY DEFINER so functions run with creator privileges
--
-- Applied: 2025-01-10

-- Update match_content_examples with SECURITY DEFINER
DROP FUNCTION IF EXISTS match_content_examples(vector(1536), text, float, integer) CASCADE;

CREATE OR REPLACE FUNCTION match_content_examples(
  query_embedding vector(1536),
  filter_platform text DEFAULT NULL,
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  platform text,
  content text,
  human_score integer,
  engagement_rate numeric,
  content_type text,
  creator text,
  hook_line text,
  tags jsonb,
  similarity float
)
LANGUAGE sql STABLE
SECURITY DEFINER
AS $$
  SELECT
    content_examples.id,
    content_examples.platform,
    content_examples.content,
    content_examples.human_score,
    content_examples.engagement_rate,
    content_examples.content_type,
    content_examples.creator,
    content_examples.hook_line,
    content_examples.tags,
    1 - (content_examples.embedding <=> query_embedding) as similarity
  FROM content_examples
  WHERE content_examples.embedding IS NOT NULL
    AND 1 - (content_examples.embedding <=> query_embedding) > match_threshold
    AND (filter_platform IS NULL OR LOWER(content_examples.platform) = LOWER(filter_platform))
    AND content_examples.status = 'approved'
  ORDER BY content_examples.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Update match_company_documents with SECURITY DEFINER
DROP FUNCTION IF EXISTS match_company_documents(vector(1536), text, double precision, integer) CASCADE;

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
SECURITY DEFINER
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
    AND (filter_type IS NULL OR company_documents.document_type IS NULL OR company_documents.document_type = filter_type)
  ORDER BY company_documents.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION match_content_examples TO authenticated;
GRANT EXECUTE ON FUNCTION match_content_examples TO anon;
GRANT EXECUTE ON FUNCTION match_content_examples TO service_role;

GRANT EXECUTE ON FUNCTION match_company_documents TO authenticated;
GRANT EXECUTE ON FUNCTION match_company_documents TO anon;
GRANT EXECUTE ON FUNCTION match_company_documents TO service_role;

-- Fix match_company_documents RPC function to handle NULL document_type correctly
-- This allows semantic search to find documents even when document_type filter is specified
-- but the document itself has document_type = NULL

CREATE OR REPLACE FUNCTION match_company_documents(
  query_embedding vector(1536),
  filter_type text DEFAULT NULL,
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 3
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
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    company_documents.id,
    company_documents.title,
    company_documents.content,
    company_documents.document_type,
    company_documents.voice_description,
    company_documents.signature_phrases,
    1 - (company_documents.embedding <=> query_embedding) AS similarity
  FROM company_documents
  WHERE
    company_documents.status = 'active'
    AND company_documents.searchable = true
    -- KEY FIX: Allow documents with NULL document_type to match any filter
    -- This makes search semantic-first, filter-second
    AND (
      filter_type IS NULL                          -- No filter = match all
      OR company_documents.document_type IS NULL   -- Untyped docs match all searches
      OR company_documents.document_type = filter_type  -- Exact type match
    )
    AND 1 - (company_documents.embedding <=> query_embedding) > match_threshold
  ORDER BY company_documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION match_company_documents TO authenticated;
GRANT EXECUTE ON FUNCTION match_company_documents TO anon;
GRANT EXECUTE ON FUNCTION match_company_documents TO service_role;

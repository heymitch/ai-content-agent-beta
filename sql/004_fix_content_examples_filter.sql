-- Migration 004: Fix match_content_examples platform filter to be case-insensitive
--
-- PROBLEM: Platform filter uses exact case-sensitive matching
-- Database has 'LinkedIn' but searches send 'linkedin', so 0 results
--
-- SOLUTION: Make platform comparison case-insensitive
--
-- Applied: 2025-01-10

-- Update function with case-insensitive platform filter
-- Using CREATE OR REPLACE to handle any type differences
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
  tags text[],
  similarity double precision
)
LANGUAGE sql STABLE
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
    -- KEY FIX: Case-insensitive platform matching
    AND (filter_platform IS NULL OR LOWER(content_examples.platform) = LOWER(filter_platform))
    AND content_examples.status = 'approved'
  ORDER BY content_examples.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION match_content_examples TO authenticated;
GRANT EXECUTE ON FUNCTION match_content_examples TO anon;
GRANT EXECUTE ON FUNCTION match_content_examples TO service_role;

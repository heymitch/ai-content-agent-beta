-- ============================================================================
-- COMPREHENSIVE FIXES FOR EXISTING DATABASES
-- ============================================================================
-- This migration applies all fixes from the new bootstrap to databases
-- that already ran the old 001-004 migrations.
--
-- Safe to run multiple times (idempotent).
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '🔧 Applying comprehensive fixes to existing database...';
END $$;

-- ============================================================================
-- FIX 1: Add missing columns to company_documents (for legacy schemas)
-- Then drop NOT NULL constraints that break n8n inserts
-- ============================================================================

DO $$
BEGIN
  -- Add title column if missing
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'title') THEN
    ALTER TABLE company_documents ADD COLUMN title TEXT;
    RAISE NOTICE '➕ Added title column to company_documents';
  END IF;

  -- Add document_type column if missing
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'document_type') THEN
    ALTER TABLE company_documents ADD COLUMN document_type TEXT;
    RAISE NOTICE '➕ Added document_type column to company_documents';
  END IF;

  -- Add other potentially missing columns
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'google_drive_file_id') THEN
    ALTER TABLE company_documents ADD COLUMN google_drive_file_id TEXT UNIQUE;
    RAISE NOTICE '➕ Added google_drive_file_id column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'google_drive_url') THEN
    ALTER TABLE company_documents ADD COLUMN google_drive_url TEXT;
    RAISE NOTICE '➕ Added google_drive_url column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'file_name') THEN
    ALTER TABLE company_documents ADD COLUMN file_name TEXT;
    RAISE NOTICE '➕ Added file_name column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'mime_type') THEN
    ALTER TABLE company_documents ADD COLUMN mime_type TEXT;
    RAISE NOTICE '➕ Added mime_type column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'last_synced') THEN
    ALTER TABLE company_documents ADD COLUMN last_synced TIMESTAMP;
    RAISE NOTICE '➕ Added last_synced column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'voice_description') THEN
    ALTER TABLE company_documents ADD COLUMN voice_description TEXT;
    RAISE NOTICE '➕ Added voice_description column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'do_list') THEN
    ALTER TABLE company_documents ADD COLUMN do_list TEXT[];
    RAISE NOTICE '➕ Added do_list column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'dont_list') THEN
    ALTER TABLE company_documents ADD COLUMN dont_list TEXT[];
    RAISE NOTICE '➕ Added dont_list column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'signature_phrases') THEN
    ALTER TABLE company_documents ADD COLUMN signature_phrases TEXT[];
    RAISE NOTICE '➕ Added signature_phrases column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'forbidden_words') THEN
    ALTER TABLE company_documents ADD COLUMN forbidden_words TEXT[];
    RAISE NOTICE '➕ Added forbidden_words column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'tone') THEN
    ALTER TABLE company_documents ADD COLUMN tone TEXT;
    RAISE NOTICE '➕ Added tone column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'user_id') THEN
    ALTER TABLE company_documents ADD COLUMN user_id TEXT;
    RAISE NOTICE '➕ Added user_id column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'team_id') THEN
    ALTER TABLE company_documents ADD COLUMN team_id TEXT;
    RAISE NOTICE '➕ Added team_id column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'searchable') THEN
    ALTER TABLE company_documents ADD COLUMN searchable BOOLEAN DEFAULT true;
    RAISE NOTICE '➕ Added searchable column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'status') THEN
    ALTER TABLE company_documents ADD COLUMN status TEXT DEFAULT 'active';
    RAISE NOTICE '➕ Added status column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'embedding') THEN
    ALTER TABLE company_documents ADD COLUMN embedding VECTOR(1536);
    RAISE NOTICE '➕ Added embedding column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'metadata') THEN
    ALTER TABLE company_documents ADD COLUMN metadata JSONB;
    RAISE NOTICE '➕ Added metadata column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'created_at') THEN
    ALTER TABLE company_documents ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
    RAISE NOTICE '➕ Added created_at column to company_documents';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'updated_at') THEN
    ALTER TABLE company_documents ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
    RAISE NOTICE '➕ Added updated_at column to company_documents';
  END IF;

  RAISE NOTICE '✅ company_documents columns verified';
END $$;

-- Now safe to drop NOT NULL constraints (columns exist)
-- Use DO block to handle case where columns don't have NOT NULL constraint
DO $$
BEGIN
  -- Only drop NOT NULL if the constraint exists
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'company_documents'
    AND column_name = 'title'
    AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE company_documents ALTER COLUMN title DROP NOT NULL;
    RAISE NOTICE '➕ Dropped NOT NULL from title column';
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'company_documents'
    AND column_name = 'document_type'
    AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE company_documents ALTER COLUMN document_type DROP NOT NULL;
    RAISE NOTICE '➕ Dropped NOT NULL from document_type column';
  END IF;
END $$;

-- ============================================================================
-- FIX 2: Add missing indexes for n8n
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_company_docs_metadata ON company_documents USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_company_docs_metadata_file_id ON company_documents((metadata->>'file_id'));

-- ============================================================================
-- FIX 3: Add missing tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflow_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform TEXT NOT NULL,
  user_id TEXT NOT NULL,
  thread_ts TEXT,
  initial_brief TEXT,
  final_draft TEXT,
  final_score INTEGER,
  iterations INTEGER DEFAULT 1,
  revision_history JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_executions_user ON workflow_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_platform ON workflow_executions(platform);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_created ON workflow_executions(created_at DESC);

CREATE TABLE IF NOT EXISTS slack_reactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_ts TEXT NOT NULL,
  reaction_emoji TEXT NOT NULL,
  user_id TEXT NOT NULL,
  action_taken TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slack_reactions_thread ON slack_reactions(thread_ts);
CREATE INDEX IF NOT EXISTS idx_slack_reactions_user ON slack_reactions(user_id);
CREATE INDEX IF NOT EXISTS idx_slack_reactions_created ON slack_reactions(created_at DESC);

CREATE TABLE IF NOT EXISTS brand_voice (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT,
  team_id TEXT,
  brand_name TEXT,
  voice_description TEXT,
  do_list TEXT[],
  dont_list TEXT[],
  tone TEXT,
  example_content TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_brand_voice_user ON brand_voice(user_id);
CREATE INDEX IF NOT EXISTS idx_brand_voice_team ON brand_voice(team_id);

-- ============================================================================
-- FIX 4: Add SECURITY DEFINER to all functions
-- Must DROP first because return types may have changed
-- ============================================================================

-- Function 1: match_content_examples
DROP FUNCTION IF EXISTS match_content_examples(vector, text, float, int);
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
  engagement_rate decimal,
  content_type text,
  creator text,
  hook_line text,
  tags text[],
  similarity float
)
LANGUAGE sql STABLE SECURITY DEFINER
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

-- Function 2: match_research
DROP FUNCTION IF EXISTS match_research(vector, float, int, int);
CREATE OR REPLACE FUNCTION match_research(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5,
  min_credibility int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  topic text,
  summary text,
  key_stats text[],
  source_names text[],
  credibility_score integer,
  research_date date,
  similarity float
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    research.id,
    research.topic,
    research.summary,
    research.key_stats,
    research.source_names,
    research.credibility_score,
    research.research_date,
    1 - (research.embedding <=> query_embedding) as similarity
  FROM research
  WHERE research.embedding IS NOT NULL
    AND 1 - (research.embedding <=> query_embedding) > match_threshold
    AND research.status = 'active'
    AND research.credibility_score >= min_credibility
  ORDER BY research.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Function 3: match_company_documents
DROP FUNCTION IF EXISTS match_company_documents(vector, text, float, int);
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
  created_at timestamp,
  similarity float
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    company_documents.id,
    company_documents.title,
    company_documents.content,
    company_documents.document_type,
    company_documents.voice_description,
    company_documents.signature_phrases,
    company_documents.created_at,
    1 - (company_documents.embedding <=> query_embedding) as similarity
  FROM company_documents
  WHERE company_documents.embedding IS NOT NULL
    AND 1 - (company_documents.embedding <=> query_embedding) > match_threshold
    AND company_documents.searchable = true
    AND company_documents.status = 'active'
    AND (filter_type IS NULL OR LOWER(company_documents.document_type) = LOWER(filter_type))
  ORDER BY company_documents.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Function 4: match_documents (n8n vectorstore compatibility)
DROP FUNCTION IF EXISTS match_documents(vector, int, jsonb);
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_count int DEFAULT NULL,
  filter jsonb DEFAULT '{}'
)
RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql STABLE SECURITY DEFINER
AS $$
#variable_conflict use_column
BEGIN
  RETURN QUERY
  SELECT
    ('x' || substr(md5(company_documents.id::text), 1, 16))::bit(64)::bigint as id,
    company_documents.content,
    company_documents.metadata,
    1 - (company_documents.embedding <=> query_embedding) as similarity
  FROM company_documents
  WHERE company_documents.metadata @> filter OR filter = '{}'::jsonb
  ORDER BY company_documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Function 5: match_knowledge (backward compatibility)
DROP FUNCTION IF EXISTS match_knowledge(vector, float, int);
CREATE OR REPLACE FUNCTION match_knowledge(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    company_documents.id,
    company_documents.content,
    jsonb_build_object(
      'title', company_documents.title,
      'document_type', company_documents.document_type
    ) as metadata,
    1 - (company_documents.embedding <=> query_embedding) as similarity
  FROM company_documents
  WHERE company_documents.embedding IS NOT NULL
    AND 1 - (company_documents.embedding <=> query_embedding) > match_threshold
    AND company_documents.searchable = true
    AND company_documents.status = 'active'
  ORDER BY company_documents.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Function 6: search_generated_posts
DROP FUNCTION IF EXISTS search_generated_posts(vector, text, text, float, int);
CREATE OR REPLACE FUNCTION search_generated_posts(
  query_embedding vector(1536),
  filter_platform text DEFAULT NULL,
  filter_status text DEFAULT NULL,
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  platform text,
  post_hook text,
  body_content text,
  status text,
  published_at timestamp,
  engagement_rate decimal,
  airtable_record_id text,
  similarity float
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    generated_posts.id,
    generated_posts.platform,
    generated_posts.post_hook,
    generated_posts.body_content,
    generated_posts.status,
    generated_posts.published_at,
    generated_posts.engagement_rate,
    generated_posts.airtable_record_id,
    1 - (generated_posts.embedding <=> query_embedding) as similarity
  FROM generated_posts
  WHERE generated_posts.embedding IS NOT NULL
    AND 1 - (generated_posts.embedding <=> query_embedding) > match_threshold
    AND (filter_platform IS NULL OR LOWER(generated_posts.platform) = LOWER(filter_platform))
    AND (filter_status IS NULL OR generated_posts.status = filter_status)
  ORDER BY generated_posts.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Function 7: search_top_performing_posts
DROP FUNCTION IF EXISTS search_top_performing_posts(vector, text, float, float, int);
CREATE OR REPLACE FUNCTION search_top_performing_posts(
  query_embedding vector(1536),
  filter_platform text DEFAULT NULL,
  min_engagement_rate float DEFAULT 0.05,
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  platform text,
  post_hook text,
  body_content text,
  content_type text,
  engagement_rate decimal,
  impressions integer,
  engagements integer,
  published_at timestamp,
  similarity float
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    generated_posts.id,
    generated_posts.platform,
    generated_posts.post_hook,
    generated_posts.body_content,
    generated_posts.content_type,
    generated_posts.engagement_rate,
    generated_posts.impressions,
    generated_posts.engagements,
    generated_posts.published_at,
    1 - (generated_posts.embedding <=> query_embedding) as similarity
  FROM generated_posts
  WHERE generated_posts.embedding IS NOT NULL
    AND 1 - (generated_posts.embedding <=> query_embedding) > match_threshold
    AND generated_posts.status = 'published'
    AND generated_posts.engagement_rate >= min_engagement_rate
    AND (filter_platform IS NULL OR LOWER(generated_posts.platform) = LOWER(filter_platform))
  ORDER BY generated_posts.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- Function 8: match_generated_posts (MISSING - called in analytics_tools.py)
DROP FUNCTION IF EXISTS match_generated_posts(vector, float, int);
CREATE OR REPLACE FUNCTION match_generated_posts(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  platform text,
  post_hook text,
  body_content text,
  quality_score integer,
  engagement_rate decimal,
  similarity float
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    generated_posts.id,
    generated_posts.platform,
    generated_posts.post_hook,
    generated_posts.body_content,
    generated_posts.quality_score,
    generated_posts.engagement_rate,
    1 - (generated_posts.embedding <=> query_embedding) as similarity
  FROM generated_posts
  WHERE generated_posts.embedding IS NOT NULL
    AND 1 - (generated_posts.embedding <=> query_embedding) > match_threshold
  ORDER BY generated_posts.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- ============================================================================
-- FIX 5: Add missing views
-- Must DROP first because Postgres can't change column names with CREATE OR REPLACE
-- ============================================================================

DROP VIEW IF EXISTS top_performing_content;
CREATE OR REPLACE VIEW top_performing_content AS
SELECT
  id,
  platform,
  post_hook,
  body_content,
  engagement_rate,
  impressions,
  engagements,
  published_at
FROM generated_posts
WHERE status = 'published'
  AND engagement_rate > 0.05;

DROP VIEW IF EXISTS generated_posts_analytics;
CREATE OR REPLACE VIEW generated_posts_analytics AS
SELECT
  id,
  platform,
  status,
  quality_score,
  engagement_rate,
  impressions,
  engagements,
  created_at,
  published_at
FROM generated_posts
WHERE created_at > NOW() - INTERVAL '90 days';

-- ============================================================================
-- FIX 6: Enable RLS and set correct policies
-- ============================================================================

ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE slack_reactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_voice ENABLE ROW LEVEL SECURITY;

-- Fix all RLS policies to allow full access
DROP POLICY IF EXISTS "Service role can manage content_examples" ON content_examples;
DROP POLICY IF EXISTS "Enable read access for all users" ON content_examples;
DROP POLICY IF EXISTS "Allow all on content_examples" ON content_examples;
CREATE POLICY "Allow all on content_examples" ON content_examples FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage conversation_history" ON conversation_history;
DROP POLICY IF EXISTS "Allow all on conversation_history" ON conversation_history;
CREATE POLICY "Allow all on conversation_history" ON conversation_history FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage research" ON research;
DROP POLICY IF EXISTS "Enable read access to research" ON research;
DROP POLICY IF EXISTS "Allow all on research" ON research;
CREATE POLICY "Allow all on research" ON research FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage company_documents" ON company_documents;
DROP POLICY IF EXISTS "Enable read access to company documents" ON company_documents;
DROP POLICY IF EXISTS "Allow all on company_documents" ON company_documents;
CREATE POLICY "Allow all on company_documents" ON company_documents FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage performance_analytics" ON performance_analytics;
DROP POLICY IF EXISTS "Allow all on performance_analytics" ON performance_analytics;
CREATE POLICY "Allow all on performance_analytics" ON performance_analytics FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage generated_posts" ON generated_posts;
DROP POLICY IF EXISTS "Enable read access to generated_posts" ON generated_posts;
DROP POLICY IF EXISTS "Allow all on generated_posts" ON generated_posts;
CREATE POLICY "Allow all on generated_posts" ON generated_posts FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage slack_threads" ON slack_threads;
DROP POLICY IF EXISTS "Allow all on slack_threads" ON slack_threads;
CREATE POLICY "Allow all on slack_threads" ON slack_threads FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage document_metadata" ON document_metadata;
DROP POLICY IF EXISTS "Users can manage their own document metadata" ON document_metadata;
DROP POLICY IF EXISTS "Allow all on document_metadata" ON document_metadata;
CREATE POLICY "Allow all on document_metadata" ON document_metadata FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage document_rows" ON document_rows;
DROP POLICY IF EXISTS "Users can manage their own document rows" ON document_rows;
DROP POLICY IF EXISTS "Allow all on document_rows" ON document_rows;
CREATE POLICY "Allow all on document_rows" ON document_rows FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all on workflow_executions" ON workflow_executions;
CREATE POLICY "Allow all on workflow_executions" ON workflow_executions FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all on slack_reactions" ON slack_reactions;
CREATE POLICY "Allow all on slack_reactions" ON slack_reactions FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all on brand_voice" ON brand_voice;
CREATE POLICY "Allow all on brand_voice" ON brand_voice FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- FIX 7: Grant all permissions
-- ============================================================================

GRANT EXECUTE ON FUNCTION match_content_examples TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_research TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_company_documents TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_documents TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_knowledge TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION search_generated_posts TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION search_top_performing_posts TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_generated_posts TO authenticated, anon, service_role;

GRANT USAGE, SELECT ON SEQUENCE document_rows_id_seq TO authenticated, anon, service_role;

GRANT ALL ON content_examples TO authenticated, anon, service_role;
GRANT ALL ON conversation_history TO authenticated, anon, service_role;
GRANT ALL ON research TO authenticated, anon, service_role;
GRANT ALL ON company_documents TO authenticated, anon, service_role;
GRANT ALL ON performance_analytics TO authenticated, anon, service_role;
GRANT ALL ON generated_posts TO authenticated, anon, service_role;
GRANT ALL ON slack_threads TO authenticated, anon, service_role;
GRANT ALL ON document_metadata TO authenticated, anon, service_role;
GRANT ALL ON document_rows TO authenticated, anon, service_role;
GRANT ALL ON workflow_executions TO authenticated, anon, service_role;
GRANT ALL ON slack_reactions TO authenticated, anon, service_role;
GRANT ALL ON brand_voice TO authenticated, anon, service_role;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '✅ Comprehensive fixes applied!';
  RAISE NOTICE '';
  RAISE NOTICE '🔧 Fixes:';
  RAISE NOTICE '   - Removed NOT NULL constraints from title/document_type';
  RAISE NOTICE '   - Added metadata indexes for n8n';
  RAISE NOTICE '   - Added missing tables (workflow_executions, slack_reactions, brand_voice)';
  RAISE NOTICE '   - Added SECURITY DEFINER to all functions';
  RAISE NOTICE '   - Added missing match_generated_posts function';
  RAISE NOTICE '   - Fixed case-insensitive platform matching';
  RAISE NOTICE '   - Set RLS policies to allow all operations';
  RAISE NOTICE '   - Granted all permissions';
  RAISE NOTICE '';
END $$;

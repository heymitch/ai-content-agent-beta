-- ============================================================================
-- COMPREHENSIVE SUPABASE BOOTSTRAP SCRIPT
-- ============================================================================
-- This script creates/fixes ALL tables, functions, policies, and indexes.
--
-- SAFE TO RUN ON EXISTING DATABASES:
--   - Uses IF NOT EXISTS for tables/indexes
--   - Uses CREATE OR REPLACE for functions/views
--   - Uses DROP POLICY IF EXISTS before CREATE POLICY
--   - Preserves existing data
--
-- Run this to fix:
--   - n8n "not indexed" errors
--   - Missing functions
--   - Wrong RLS policies
--   - Permission issues
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

DO $$
BEGIN
  RAISE NOTICE '🚀 Starting Comprehensive Supabase Bootstrap...';
END $$;

-- ============================================================================
-- TABLE 1: content_examples
-- Purpose: Proven content (90-100% human scores) for RAG retrieval
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_examples (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform TEXT NOT NULL,
  content TEXT NOT NULL,
  human_score INTEGER,
  engagement_rate DECIMAL,
  impressions INTEGER,
  clicks INTEGER,
  content_type TEXT,
  creator TEXT,
  hook_line TEXT,
  main_points TEXT[],
  cta_line TEXT,
  tags TEXT[],
  topics TEXT[],
  embedding VECTOR(1536),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'approved'
);

CREATE INDEX IF NOT EXISTS idx_content_examples_platform ON content_examples(platform);
CREATE INDEX IF NOT EXISTS idx_content_examples_creator ON content_examples(creator);
CREATE INDEX IF NOT EXISTS idx_content_examples_tags ON content_examples USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_content_examples_status ON content_examples(status);
CREATE INDEX IF NOT EXISTS idx_content_examples_embedding ON content_examples USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- TABLE 2: conversation_history
-- Purpose: CMO agent extracts rich context from Slack conversations
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversation_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_ts TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_thread ON conversation_history(thread_ts);
CREATE INDEX IF NOT EXISTS idx_conversation_user ON conversation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_created ON conversation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_channel ON conversation_history(channel_id);

-- ============================================================================
-- TABLE 3: research
-- Purpose: Digests and research reports from Tavily web search
-- ============================================================================

CREATE TABLE IF NOT EXISTS research (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic TEXT NOT NULL,
  summary TEXT NOT NULL,
  full_report TEXT,
  key_stats TEXT[],
  source_urls TEXT[],
  source_names TEXT[],
  primary_source TEXT,
  credibility_score INTEGER DEFAULT 5,
  research_date DATE NOT NULL,
  last_verified DATE,
  used_in_content_ids UUID[],
  usage_count INTEGER DEFAULT 0,
  topics TEXT[],
  embedding VECTOR(1536),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_research_topic ON research(topic);
CREATE INDEX IF NOT EXISTS idx_research_topics ON research USING GIN(topics);
CREATE INDEX IF NOT EXISTS idx_research_date ON research(research_date DESC);
CREATE INDEX IF NOT EXISTS idx_research_status ON research(status);
CREATE INDEX IF NOT EXISTS idx_research_credibility ON research(credibility_score DESC);
CREATE INDEX IF NOT EXISTS idx_research_embedding ON research USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- TABLE 4: company_documents
-- Purpose: Brand guides, case studies, product docs synced from Google Drive
-- This table is used by BOTH the main agent AND n8n Google Drive workflow
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT,
  content TEXT NOT NULL,
  document_type TEXT,
  google_drive_file_id TEXT UNIQUE,
  google_drive_url TEXT,
  file_name TEXT,
  mime_type TEXT,
  last_synced TIMESTAMP,
  voice_description TEXT,
  do_list TEXT[],
  dont_list TEXT[],
  signature_phrases TEXT[],
  forbidden_words TEXT[],
  tone TEXT,
  user_id TEXT,
  team_id TEXT,
  searchable BOOLEAN DEFAULT true,
  embedding VECTOR(1536),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_company_docs_type ON company_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_company_docs_user ON company_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_company_docs_team ON company_documents(team_id);
CREATE INDEX IF NOT EXISTS idx_company_docs_drive_id ON company_documents(google_drive_file_id);
CREATE INDEX IF NOT EXISTS idx_company_docs_status ON company_documents(status);
CREATE INDEX IF NOT EXISTS idx_company_docs_searchable ON company_documents(searchable) WHERE searchable = true;
CREATE INDEX IF NOT EXISTS idx_company_docs_metadata ON company_documents USING GIN(metadata);
-- CRITICAL: This index fixes n8n "not indexed" errors when filtering by metadata->>file_id
CREATE INDEX IF NOT EXISTS idx_company_docs_metadata_file_id ON company_documents((metadata->>'file_id'));
CREATE INDEX IF NOT EXISTS idx_company_docs_embedding ON company_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- TABLE 5: performance_analytics
-- Purpose: Track quality during creation AND real-world performance post-publish
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_id UUID,
  platform TEXT NOT NULL,
  content TEXT NOT NULL,
  content_type TEXT,
  quality_score INTEGER NOT NULL,
  quality_breakdown JSONB,
  human_score INTEGER,
  iterations INTEGER DEFAULT 1,
  time_to_create INTEGER,
  tools_used TEXT[],
  published BOOLEAN DEFAULT FALSE,
  published_at TIMESTAMP,
  published_url TEXT,
  impressions INTEGER,
  clicks INTEGER,
  likes INTEGER,
  comments INTEGER,
  shares INTEGER,
  engagement_rate DECIMAL,
  conversions INTEGER,
  revenue_generated DECIMAL,
  user_id TEXT NOT NULL,
  thread_ts TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_performance_user ON performance_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_platform ON performance_analytics(platform);
CREATE INDEX IF NOT EXISTS idx_performance_score ON performance_analytics(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_performance_published ON performance_analytics(published, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_performance_engagement ON performance_analytics(engagement_rate DESC) WHERE engagement_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_performance_thread ON performance_analytics(thread_ts);

-- ============================================================================
-- TABLE 6: generated_posts
-- Purpose: AI-generated content with Airtable + Ayrshare publishing workflow
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform TEXT NOT NULL CHECK (platform IN ('linkedin', 'twitter', 'email', 'youtube', 'blog', 'instagram')),
  post_hook TEXT,
  body_content TEXT NOT NULL,
  content_type TEXT,
  platform_metadata JSONB DEFAULT '{}',
  airtable_record_id TEXT UNIQUE,
  airtable_url TEXT,
  airtable_status TEXT,
  ayrshare_post_id TEXT UNIQUE,
  ayrshare_platform_ids JSONB,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'archived')),
  scheduled_for TIMESTAMP,
  published_at TIMESTAMP,
  published_url TEXT,
  impressions INTEGER DEFAULT 0,
  engagements INTEGER DEFAULT 0,
  clicks INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  shares INTEGER DEFAULT 0,
  saves INTEGER DEFAULT 0,
  engagement_rate DECIMAL,
  click_through_rate DECIMAL,
  conversions INTEGER DEFAULT 0,
  revenue_attributed DECIMAL DEFAULT 0,
  last_analytics_sync TIMESTAMP,
  quality_score INTEGER,
  quality_breakdown JSONB,
  human_score INTEGER,
  iterations INTEGER DEFAULT 1,
  slack_thread_ts TEXT,
  slack_channel_id TEXT,
  user_id TEXT NOT NULL,
  created_by_agent TEXT,
  embedding VECTOR(1536),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generated_posts_platform ON generated_posts(platform);
CREATE INDEX IF NOT EXISTS idx_generated_posts_status ON generated_posts(status);
CREATE INDEX IF NOT EXISTS idx_generated_posts_user ON generated_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_posts_airtable ON generated_posts(airtable_record_id) WHERE airtable_record_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_posts_ayrshare ON generated_posts(ayrshare_post_id) WHERE ayrshare_post_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_posts_published ON generated_posts(published_at DESC) WHERE status = 'published';
CREATE INDEX IF NOT EXISTS idx_generated_posts_thread ON generated_posts(slack_thread_ts) WHERE slack_thread_ts IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_posts_engagement ON generated_posts(engagement_rate DESC) WHERE engagement_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_posts_embedding ON generated_posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- TABLE 7: slack_threads
-- Purpose: Track Slack thread-level state for content creation
-- ============================================================================

CREATE TABLE IF NOT EXISTS slack_threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  thread_ts TEXT UNIQUE NOT NULL,
  channel_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  latest_draft TEXT,
  latest_score INTEGER DEFAULT 0,
  status TEXT DEFAULT 'drafting',
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slack_threads_thread_ts ON slack_threads(thread_ts);
CREATE INDEX IF NOT EXISTS idx_slack_threads_user_id ON slack_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_slack_threads_status ON slack_threads(status);
CREATE INDEX IF NOT EXISTS idx_slack_threads_platform ON slack_threads(platform);
CREATE INDEX IF NOT EXISTS idx_slack_threads_created_at ON slack_threads(created_at DESC);

-- ============================================================================
-- TABLE 8: document_metadata
-- Purpose: n8n Google Drive workflow - stores metadata about uploaded documents
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_metadata (
    id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    schema TEXT
);

CREATE INDEX IF NOT EXISTS idx_document_metadata_created_at ON document_metadata(created_at DESC);

-- ============================================================================
-- TABLE 9: document_rows
-- Purpose: n8n Google Drive workflow - stores individual rows from spreadsheets
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_rows (
    id SERIAL PRIMARY KEY,
    dataset_id TEXT REFERENCES document_metadata(id) ON DELETE CASCADE,
    row_data JSONB
);

CREATE INDEX IF NOT EXISTS idx_document_rows_dataset_id ON document_rows(dataset_id);
CREATE INDEX IF NOT EXISTS idx_document_rows_data ON document_rows USING GIN (row_data);

-- ============================================================================
-- TABLE 10: workflow_executions (MISSING - referenced in code)
-- Purpose: Log workflow execution results
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

-- ============================================================================
-- TABLE 11: slack_reactions (MISSING - referenced in code)
-- Purpose: Log reaction events for analytics
-- ============================================================================

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

-- ============================================================================
-- TABLE 12: brand_voice (Legacy - for backward compatibility)
-- Purpose: Legacy brand voice table
-- ============================================================================

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
-- TRIGGER FUNCTIONS
-- ============================================================================

-- Auto-populate title and document_type from metadata (for n8n compatibility)
CREATE OR REPLACE FUNCTION sync_company_documents_fields()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.title IS NULL AND NEW.metadata ? 'title' THEN
    NEW.title := NEW.metadata->>'title';
  END IF;
  IF NEW.document_type IS NULL THEN
    NEW.document_type := COALESCE(NEW.metadata->>'document_type', 'document');
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_sync_company_documents_fields ON company_documents;
CREATE TRIGGER trigger_sync_company_documents_fields
  BEFORE INSERT OR UPDATE ON company_documents
  FOR EACH ROW
  EXECUTE FUNCTION sync_company_documents_fields();

-- Auto-update timestamp for generated_posts
CREATE OR REPLACE FUNCTION update_generated_posts_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS generated_posts_updated_at ON generated_posts;
CREATE TRIGGER generated_posts_updated_at
  BEFORE UPDATE ON generated_posts
  FOR EACH ROW
  EXECUTE FUNCTION update_generated_posts_timestamp();

-- Auto-update timestamp for slack_threads
CREATE OR REPLACE FUNCTION update_slack_threads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_slack_threads_updated_at ON slack_threads;
CREATE TRIGGER trigger_update_slack_threads_updated_at
  BEFORE UPDATE ON slack_threads
  FOR EACH ROW
  EXECUTE FUNCTION update_slack_threads_updated_at();

-- ============================================================================
-- RAG SEARCH FUNCTIONS
-- All with SECURITY DEFINER for n8n compatibility
-- ============================================================================

-- Function 1: match_content_examples
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
-- VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW knowledge_base AS
SELECT
  id,
  content,
  embedding,
  jsonb_build_object(
    'title', title,
    'document_type', document_type,
    'searchable', searchable
  ) as metadata,
  document_type as source,
  user_id,
  created_at
FROM company_documents
WHERE status = 'active';

CREATE OR REPLACE VIEW content_performance AS
SELECT
  id,
  thread_ts,
  platform,
  content,
  quality_score,
  quality_breakdown as validation_details,
  iterations,
  time_to_create as time_to_complete,
  user_id,
  published,
  published_at,
  created_at
FROM performance_analytics;

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
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE content_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE research ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE slack_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE slack_reactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_voice ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES
-- Using FOR ALL USING (true) WITH CHECK (true) for maximum compatibility
-- This allows all operations when using service_role or anon key
-- ============================================================================

-- content_examples
DROP POLICY IF EXISTS "Service role can manage content_examples" ON content_examples;
DROP POLICY IF EXISTS "Enable read access for all users" ON content_examples;
DROP POLICY IF EXISTS "Allow all on content_examples" ON content_examples;
CREATE POLICY "Allow all on content_examples" ON content_examples FOR ALL USING (true) WITH CHECK (true);

-- conversation_history
DROP POLICY IF EXISTS "Service role can manage conversation_history" ON conversation_history;
DROP POLICY IF EXISTS "Allow all on conversation_history" ON conversation_history;
CREATE POLICY "Allow all on conversation_history" ON conversation_history FOR ALL USING (true) WITH CHECK (true);

-- research
DROP POLICY IF EXISTS "Service role can manage research" ON research;
DROP POLICY IF EXISTS "Enable read access to research" ON research;
DROP POLICY IF EXISTS "Allow all on research" ON research;
CREATE POLICY "Allow all on research" ON research FOR ALL USING (true) WITH CHECK (true);

-- company_documents (CRITICAL for n8n)
DROP POLICY IF EXISTS "Service role can manage company_documents" ON company_documents;
DROP POLICY IF EXISTS "Enable read access to company documents" ON company_documents;
DROP POLICY IF EXISTS "Allow all on company_documents" ON company_documents;
CREATE POLICY "Allow all on company_documents" ON company_documents FOR ALL USING (true) WITH CHECK (true);

-- performance_analytics
DROP POLICY IF EXISTS "Service role can manage performance_analytics" ON performance_analytics;
DROP POLICY IF EXISTS "Allow all on performance_analytics" ON performance_analytics;
CREATE POLICY "Allow all on performance_analytics" ON performance_analytics FOR ALL USING (true) WITH CHECK (true);

-- generated_posts
DROP POLICY IF EXISTS "Service role can manage generated_posts" ON generated_posts;
DROP POLICY IF EXISTS "Enable read access to generated_posts" ON generated_posts;
DROP POLICY IF EXISTS "Allow all on generated_posts" ON generated_posts;
CREATE POLICY "Allow all on generated_posts" ON generated_posts FOR ALL USING (true) WITH CHECK (true);

-- slack_threads
DROP POLICY IF EXISTS "Service role can manage slack_threads" ON slack_threads;
DROP POLICY IF EXISTS "Allow all on slack_threads" ON slack_threads;
CREATE POLICY "Allow all on slack_threads" ON slack_threads FOR ALL USING (true) WITH CHECK (true);

-- document_metadata (CRITICAL for n8n)
DROP POLICY IF EXISTS "Service role can manage document_metadata" ON document_metadata;
DROP POLICY IF EXISTS "Users can manage their own document metadata" ON document_metadata;
DROP POLICY IF EXISTS "Allow all on document_metadata" ON document_metadata;
CREATE POLICY "Allow all on document_metadata" ON document_metadata FOR ALL USING (true) WITH CHECK (true);

-- document_rows (CRITICAL for n8n)
DROP POLICY IF EXISTS "Service role can manage document_rows" ON document_rows;
DROP POLICY IF EXISTS "Users can manage their own document rows" ON document_rows;
DROP POLICY IF EXISTS "Allow all on document_rows" ON document_rows;
CREATE POLICY "Allow all on document_rows" ON document_rows FOR ALL USING (true) WITH CHECK (true);

-- workflow_executions
DROP POLICY IF EXISTS "Allow all on workflow_executions" ON workflow_executions;
CREATE POLICY "Allow all on workflow_executions" ON workflow_executions FOR ALL USING (true) WITH CHECK (true);

-- slack_reactions
DROP POLICY IF EXISTS "Allow all on slack_reactions" ON slack_reactions;
CREATE POLICY "Allow all on slack_reactions" ON slack_reactions FOR ALL USING (true) WITH CHECK (true);

-- brand_voice
DROP POLICY IF EXISTS "Allow all on brand_voice" ON brand_voice;
CREATE POLICY "Allow all on brand_voice" ON brand_voice FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant execute on all functions
GRANT EXECUTE ON FUNCTION match_content_examples TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_research TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_company_documents TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_documents TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_knowledge TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION search_generated_posts TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION search_top_performing_posts TO authenticated, anon, service_role;
GRANT EXECUTE ON FUNCTION match_generated_posts TO authenticated, anon, service_role;

-- Grant on sequences
GRANT USAGE, SELECT ON SEQUENCE document_rows_id_seq TO authenticated, anon, service_role;

-- Grant on tables
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
  RAISE NOTICE '✅ ============================================';
  RAISE NOTICE '✅ Comprehensive Bootstrap Complete!';
  RAISE NOTICE '✅ ============================================';
  RAISE NOTICE '';
  RAISE NOTICE '📋 Tables (12):';
  RAISE NOTICE '   Core: content_examples, conversation_history, research,';
  RAISE NOTICE '         company_documents, performance_analytics, generated_posts,';
  RAISE NOTICE '         slack_threads, document_metadata, document_rows';
  RAISE NOTICE '   Added: workflow_executions, slack_reactions, brand_voice';
  RAISE NOTICE '';
  RAISE NOTICE '🔍 Functions (8):';
  RAISE NOTICE '   match_content_examples, match_research, match_company_documents,';
  RAISE NOTICE '   match_documents, match_knowledge, search_generated_posts,';
  RAISE NOTICE '   search_top_performing_posts, match_generated_posts';
  RAISE NOTICE '';
  RAISE NOTICE '🔐 Security:';
  RAISE NOTICE '   - RLS enabled on all tables';
  RAISE NOTICE '   - Full access policies for all roles';
  RAISE NOTICE '   - SECURITY DEFINER on all functions';
  RAISE NOTICE '   - GRANT permissions set';
  RAISE NOTICE '';
  RAISE NOTICE '🔧 Fixes Applied:';
  RAISE NOTICE '   - n8n "not indexed" errors (metadata index)';
  RAISE NOTICE '   - n8n DELETE/INSERT operations (RLS policies)';
  RAISE NOTICE '   - Missing match_generated_posts function';
  RAISE NOTICE '   - Case-insensitive platform matching';
  RAISE NOTICE '';
  RAISE NOTICE '🚀 Ready for use!';
  RAISE NOTICE '';
END $$;

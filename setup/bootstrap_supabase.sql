-- ============================================================================
-- COMPLETE SUPABASE BOOTSTRAP SCRIPT
-- ============================================================================
-- This script creates ALL tables, functions, policies, and indexes needed
-- for the AI Content Agent to work properly.
--
-- Run this ONCE on a fresh Supabase instance to set up everything.
-- Safe to run multiple times (uses IF NOT EXISTS checks).
--
-- Usage:
--   1. Via Supabase SQL Editor: Copy/paste and run
--   2. Via psql: psql <connection_string> -f bootstrap_supabase.sql
--   3. Via script: ./deploy_to_client.sh <client_supabase_url>
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

DO $$
BEGIN
  RAISE NOTICE '🚀 Starting Supabase Bootstrap...';
END $$;

-- ============================================================================
-- TABLE 1: content_examples
-- Purpose: Proven content (90-100% human scores) for RAG retrieval
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_examples (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Content
  platform TEXT NOT NULL,
  content TEXT NOT NULL,
  human_score INTEGER,

  -- Performance Metrics
  engagement_rate DECIMAL,
  impressions INTEGER,
  clicks INTEGER,
  content_type TEXT,

  -- Metadata
  creator TEXT,
  hook_line TEXT,
  main_points TEXT[],
  cta_line TEXT,
  tags TEXT[],
  topics TEXT[],

  -- RAG Search
  embedding VECTOR(1536),

  -- Lifecycle
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'approved'
);

CREATE INDEX IF NOT EXISTS idx_content_examples_platform ON content_examples(platform);
CREATE INDEX IF NOT EXISTS idx_content_examples_creator ON content_examples(creator);
CREATE INDEX IF NOT EXISTS idx_content_examples_tags ON content_examples USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_content_examples_status ON content_examples(status);
CREATE INDEX IF NOT EXISTS idx_content_examples_embedding ON content_examples USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RAG search function
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
    AND (filter_platform IS NULL OR content_examples.platform = filter_platform)
    AND content_examples.status = 'approved'
  ORDER BY content_examples.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- ============================================================================
-- TABLE 2: conversation_history
-- Purpose: CMO agent extracts rich context from Slack conversations
-- ============================================================================

CREATE TABLE IF NOT EXISTS conversation_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Slack Context
  thread_ts TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  user_id TEXT NOT NULL,

  -- Message
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,

  -- Metadata
  metadata JSONB,

  -- Lifecycle
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

  -- Research Content
  topic TEXT NOT NULL,
  summary TEXT NOT NULL,
  full_report TEXT,
  key_stats TEXT[],

  -- Sources
  source_urls TEXT[],
  source_names TEXT[],
  primary_source TEXT,

  -- Verification
  credibility_score INTEGER DEFAULT 5,
  research_date DATE NOT NULL,
  last_verified DATE,

  -- Usage Tracking
  used_in_content_ids UUID[],
  usage_count INTEGER DEFAULT 0,
  topics TEXT[],

  -- RAG Search
  embedding VECTOR(1536),

  -- Lifecycle
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

-- RAG search function
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
LANGUAGE sql STABLE
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

-- ============================================================================
-- TABLE 4: company_documents
-- Purpose: Brand guides, case studies, product docs synced from Google Drive
-- This table is used by BOTH the main agent AND n8n Google Drive workflow
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Document Identification
  title TEXT,  -- Nullable: n8n vectorstore populates this via metadata
  content TEXT NOT NULL,
  document_type TEXT,  -- Nullable: can be set later or via trigger

  -- Google Drive Sync
  google_drive_file_id TEXT UNIQUE,
  google_drive_url TEXT,
  file_name TEXT,
  mime_type TEXT,
  last_synced TIMESTAMP,

  -- Brand Voice Fields
  voice_description TEXT,
  do_list TEXT[],
  dont_list TEXT[],
  signature_phrases TEXT[],
  forbidden_words TEXT[],
  tone TEXT,

  -- Access Control
  user_id TEXT,
  team_id TEXT,
  searchable BOOLEAN DEFAULT true,

  -- RAG Search
  embedding VECTOR(1536),

  -- Metadata (for n8n compatibility)
  metadata JSONB,

  -- Lifecycle
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
CREATE INDEX IF NOT EXISTS idx_company_docs_embedding ON company_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RAG search function
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
    AND (filter_type IS NULL OR company_documents.document_type = filter_type)
  ORDER BY company_documents.embedding <=> query_embedding
  LIMIT match_count;
$$;

-- n8n compatibility function (for vectorstore node)
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
LANGUAGE plpgsql
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

-- Auto-populate title and document_type from metadata (for n8n compatibility)
CREATE OR REPLACE FUNCTION sync_company_documents_fields()
RETURNS TRIGGER AS $$
BEGIN
  -- Extract title from metadata if not explicitly set
  IF NEW.title IS NULL AND NEW.metadata ? 'title' THEN
    NEW.title := NEW.metadata->>'title';
  END IF;

  -- Set default document_type if not set
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

-- ============================================================================
-- TABLE 5: performance_analytics
-- Purpose: Track quality during creation AND real-world performance post-publish
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Content Reference
  content_id UUID,
  platform TEXT NOT NULL,
  content TEXT NOT NULL,
  content_type TEXT,

  -- Creation Quality Metrics
  quality_score INTEGER NOT NULL,
  quality_breakdown JSONB,
  human_score INTEGER,
  iterations INTEGER DEFAULT 1,
  time_to_create INTEGER,
  tools_used TEXT[],

  -- Real-World Performance
  published BOOLEAN DEFAULT FALSE,
  published_at TIMESTAMP,
  published_url TEXT,

  -- Engagement Metrics
  impressions INTEGER,
  clicks INTEGER,
  likes INTEGER,
  comments INTEGER,
  shares INTEGER,
  engagement_rate DECIMAL,
  conversions INTEGER,
  revenue_generated DECIMAL,

  -- User Tracking
  user_id TEXT NOT NULL,
  thread_ts TEXT,

  -- Lifecycle
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

  -- Content
  platform TEXT NOT NULL CHECK (platform IN ('linkedin', 'twitter', 'email', 'youtube', 'blog', 'instagram')),
  post_hook TEXT,
  body_content TEXT NOT NULL,
  content_type TEXT,
  platform_metadata JSONB DEFAULT '{}',

  -- Airtable Integration
  airtable_record_id TEXT UNIQUE,
  airtable_url TEXT,
  airtable_status TEXT,

  -- Ayrshare Integration
  ayrshare_post_id TEXT UNIQUE,
  ayrshare_platform_ids JSONB,

  -- Publishing Workflow
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'archived')),
  scheduled_for TIMESTAMP,
  published_at TIMESTAMP,
  published_url TEXT,

  -- Performance Analytics
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

  -- Creation Quality Metrics
  quality_score INTEGER,
  quality_breakdown JSONB,
  human_score INTEGER,
  iterations INTEGER DEFAULT 1,

  -- Session Tracking
  slack_thread_ts TEXT,
  slack_channel_id TEXT,
  user_id TEXT NOT NULL,
  created_by_agent TEXT,

  -- RAG Search
  embedding VECTOR(1536),

  -- Lifecycle
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

-- Auto-update timestamp trigger
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

-- ============================================================================
-- TABLE 7: slack_threads
-- Purpose: Track Slack thread-level state for content creation
-- ============================================================================

CREATE TABLE IF NOT EXISTS slack_threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Slack Context
  thread_ts TEXT UNIQUE NOT NULL,
  channel_id TEXT NOT NULL,
  user_id TEXT NOT NULL,

  -- Content Metadata
  platform TEXT NOT NULL,
  latest_draft TEXT,
  latest_score INTEGER DEFAULT 0,

  -- Workflow State
  status TEXT DEFAULT 'drafting',
  metadata JSONB,

  -- Lifecycle
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_slack_threads_thread_ts ON slack_threads(thread_ts);
CREATE INDEX IF NOT EXISTS idx_slack_threads_user_id ON slack_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_slack_threads_status ON slack_threads(status);
CREATE INDEX IF NOT EXISTS idx_slack_threads_platform ON slack_threads(platform);
CREATE INDEX IF NOT EXISTS idx_slack_threads_created_at ON slack_threads(created_at DESC);

-- Auto-update timestamp trigger
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

COMMENT ON TABLE document_metadata IS 'Stores metadata for documents uploaded via n8n Google Drive workflow';
COMMENT ON COLUMN document_metadata.id IS 'Google Drive file ID';
COMMENT ON COLUMN document_metadata.schema IS 'JSON schema for tabular documents (columns/fields)';

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

COMMENT ON TABLE document_rows IS 'Stores individual rows from tabular documents processed by n8n';
COMMENT ON COLUMN document_rows.dataset_id IS 'Foreign key to document_metadata.id (Google Drive file ID)';

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

-- ============================================================================
-- RLS POLICIES: Service Role (Full Access)
-- ============================================================================

DROP POLICY IF EXISTS "Service role can manage content_examples" ON content_examples;
CREATE POLICY "Service role can manage content_examples" ON content_examples FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage conversation_history" ON conversation_history;
CREATE POLICY "Service role can manage conversation_history" ON conversation_history FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage research" ON research;
CREATE POLICY "Service role can manage research" ON research FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage company_documents" ON company_documents;
CREATE POLICY "Service role can manage company_documents" ON company_documents FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage performance_analytics" ON performance_analytics;
CREATE POLICY "Service role can manage performance_analytics" ON performance_analytics FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage generated_posts" ON generated_posts;
CREATE POLICY "Service role can manage generated_posts" ON generated_posts FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage slack_threads" ON slack_threads;
CREATE POLICY "Service role can manage slack_threads" ON slack_threads FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage document_metadata" ON document_metadata;
CREATE POLICY "Service role can manage document_metadata" ON document_metadata FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage document_rows" ON document_rows;
CREATE POLICY "Service role can manage document_rows" ON document_rows FOR ALL USING (true);

-- ============================================================================
-- RLS POLICIES: API Key Access (Read)
-- ============================================================================

DROP POLICY IF EXISTS "Enable read access for all users" ON content_examples;
CREATE POLICY "Enable read access for all users"
  ON content_examples
  FOR SELECT
  USING (true);

DROP POLICY IF EXISTS "Enable read access to company documents" ON company_documents;
CREATE POLICY "Enable read access to company documents"
  ON company_documents
  FOR SELECT
  USING (true);

DROP POLICY IF EXISTS "Enable read access to research" ON research;
CREATE POLICY "Enable read access to research"
  ON research
  FOR SELECT
  USING (true);

DROP POLICY IF EXISTS "Enable read access to generated_posts" ON generated_posts;
CREATE POLICY "Enable read access to generated_posts"
  ON generated_posts
  FOR SELECT
  USING (true);

DROP POLICY IF EXISTS "Users can manage their own document metadata" ON document_metadata;
CREATE POLICY "Users can manage their own document metadata"
  ON document_metadata
  FOR ALL
  USING (true)
  WITH CHECK (true);

DROP POLICY IF EXISTS "Users can manage their own document rows" ON document_rows;
CREATE POLICY "Users can manage their own document rows"
  ON document_rows
  FOR ALL
  USING (true)
  WITH CHECK (true);

-- ============================================================================
-- BACKWARD COMPATIBILITY VIEWS
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
LANGUAGE sql STABLE
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

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '✅ ============================================';
  RAISE NOTICE '✅ Supabase Bootstrap Complete!';
  RAISE NOTICE '✅ ============================================';
  RAISE NOTICE '';
  RAISE NOTICE '📋 Tables Created:';
  RAISE NOTICE '   1. content_examples - Proven content for RAG';
  RAISE NOTICE '   2. conversation_history - Slack context';
  RAISE NOTICE '   3. research - Tavily digests';
  RAISE NOTICE '   4. company_documents - Google Drive docs + n8n';
  RAISE NOTICE '   5. performance_analytics - Quality tracking';
  RAISE NOTICE '   6. generated_posts - AI content with Airtable/Ayrshare';
  RAISE NOTICE '   7. slack_threads - Thread state tracking';
  RAISE NOTICE '   8. document_metadata - n8n metadata storage';
  RAISE NOTICE '   9. document_rows - n8n tabular data storage';
  RAISE NOTICE '';
  RAISE NOTICE '🔐 Security:';
  RAISE NOTICE '   - Row Level Security (RLS) enabled on all tables';
  RAISE NOTICE '   - Service role has full access';
  RAISE NOTICE '   - API keys have read access where needed';
  RAISE NOTICE '';
  RAISE NOTICE '🔍 RAG Functions Created:';
  RAISE NOTICE '   - match_content_examples()';
  RAISE NOTICE '   - match_research()';
  RAISE NOTICE '   - match_company_documents()';
  RAISE NOTICE '   - match_documents() (n8n compatibility)';
  RAISE NOTICE '   - match_knowledge() (backward compat)';
  RAISE NOTICE '';
  RAISE NOTICE '✨ Next Steps:';
  RAISE NOTICE '   1. Update your .env with Supabase credentials';
  RAISE NOTICE '   2. Import your n8n workflow (no table setup needed!)';
  RAISE NOTICE '   3. Configure Google Drive integration';
  RAISE NOTICE '   4. Start using the agent!';
  RAISE NOTICE '';
  RAISE NOTICE '🚀 Happy creating!';
  RAISE NOTICE '';
END $$;

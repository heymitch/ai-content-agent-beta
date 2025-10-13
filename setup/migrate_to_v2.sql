-- Migration Script: Database Schema V1 → V2
-- Run this in Supabase SQL Editor for EXISTING installations
-- IMPORTANT: Backup your database first!

-- This script:
-- 1. Creates new tables (research, updates content_examples structure)
-- 2. Renames content_performance → performance_analytics
-- 3. Migrates brand_voice → company_documents
-- 4. Preserves ALL existing data
-- 5. Maintains backward compatibility

-- ============================================================================
-- STEP 1: Create new tables
-- ============================================================================

-- Enable required extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

DO $$
BEGIN
  RAISE NOTICE '🔄 Starting migration to Database Schema V2...';
END $$;

-- Create research table (NEW)
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

DO $$
BEGIN
  RAISE NOTICE '✅ Created research table';
END $$;

-- Create company_documents table (replaces knowledge_base + brand_voice)
CREATE TABLE IF NOT EXISTS company_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  document_type TEXT NOT NULL,
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
CREATE INDEX IF NOT EXISTS idx_company_docs_embedding ON company_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

DO $$
BEGIN
  RAISE NOTICE '✅ Created company_documents table';
END $$;

-- ============================================================================
-- STEP 2: Migrate data from old tables to new structure
-- ============================================================================

-- Migrate brand_voice → company_documents (type='brand_guide')
DO $$
DECLARE
  migrated_count INTEGER;
BEGIN
  IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'brand_voice') THEN
    INSERT INTO company_documents (
      id,
      title,
      content,
      document_type,
      voice_description,
      do_list,
      dont_list,
      tone,
      user_id,
      team_id,
      searchable,
      created_at,
      updated_at,
      status
    )
    SELECT
      id,
      COALESCE(brand_name, 'Brand Voice Guide') as title,
      COALESCE(voice_description, example_content, 'Brand voice guidelines') as content,
      'brand_guide' as document_type,
      voice_description,
      do_list,
      dont_list,
      tone,
      user_id,
      team_id,
      true as searchable,
      created_at,
      updated_at,
      'active' as status
    FROM brand_voice
    WHERE id NOT IN (SELECT id FROM company_documents);

    GET DIAGNOSTICS migrated_count = ROW_COUNT;
    RAISE NOTICE '✅ Migrated % brand_voice records to company_documents', migrated_count;
  END IF;
END $$;

-- Migrate knowledge_base → company_documents (determine type from metadata)
DO $$
DECLARE
  migrated_count INTEGER;
BEGIN
  IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'knowledge_base') THEN
    INSERT INTO company_documents (
      id,
      title,
      content,
      document_type,
      user_id,
      searchable,
      embedding,
      created_at,
      status
    )
    SELECT
      id,
      COALESCE(metadata->>'title', source, 'Document') as title,
      content,
      COALESCE(metadata->>'document_type', source, 'product_doc') as document_type,
      user_id,
      true as searchable,
      embedding,
      created_at,
      'active' as status
    FROM knowledge_base
    WHERE id NOT IN (SELECT id FROM company_documents);

    GET DIAGNOSTICS migrated_count = ROW_COUNT;
    RAISE NOTICE '✅ Migrated % knowledge_base records to company_documents', migrated_count;
  END IF;
END $$;

-- ============================================================================
-- STEP 3: Rename content_performance → performance_analytics (if needed)
-- ============================================================================

DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.tables WHERE table_name = 'content_performance'
  ) AND NOT EXISTS (
    SELECT FROM information_schema.tables WHERE table_name = 'performance_analytics'
  ) THEN
    -- Rename table
    ALTER TABLE content_performance RENAME TO performance_analytics;

    -- Rename columns to match new schema
    ALTER TABLE performance_analytics RENAME COLUMN validation_details TO quality_breakdown;
    ALTER TABLE performance_analytics RENAME COLUMN time_to_complete TO time_to_create;

    -- Add new columns with defaults
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS content_id UUID;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS content_type TEXT;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS human_score INTEGER;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS tools_used TEXT[];
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS published_url TEXT;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS clicks INTEGER;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS likes INTEGER;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS comments INTEGER;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS shares INTEGER;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS engagement_rate DECIMAL;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS conversions INTEGER;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS revenue_generated DECIMAL;
    ALTER TABLE performance_analytics ADD COLUMN IF NOT EXISTS last_updated TIMESTAMP DEFAULT NOW();

    -- Create new indexes
    CREATE INDEX IF NOT EXISTS idx_performance_engagement ON performance_analytics(engagement_rate DESC) WHERE engagement_rate IS NOT NULL;

    RAISE NOTICE '✅ Renamed content_performance → performance_analytics and added new columns';
  ELSE
    RAISE NOTICE 'ℹ️  performance_analytics already exists or content_performance not found';
  END IF;
END $$;

-- ============================================================================
-- STEP 4: Update content_examples structure (if it exists)
-- ============================================================================

DO $$
BEGIN
  IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'content_examples') THEN
    -- Add new columns if they don't exist
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS clicks INTEGER;
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS content_type TEXT;
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS creator TEXT;
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS hook_line TEXT;
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS main_points TEXT[];
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS cta_line TEXT;
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS tags TEXT[];
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS topics TEXT[];
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
    ALTER TABLE content_examples ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'approved';

    -- Create new indexes
    CREATE INDEX IF NOT EXISTS idx_content_examples_tags ON content_examples USING GIN(tags);
    CREATE INDEX IF NOT EXISTS idx_content_examples_status ON content_examples(status);

    RAISE NOTICE '✅ Updated content_examples with new columns';
  ELSE
    -- Create from scratch if doesn't exist
    CREATE TABLE content_examples (
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

    RAISE NOTICE '✅ Created content_examples table';
  END IF;
END $$;

-- ============================================================================
-- STEP 5: Create generated_posts table (NEW in V2.1)
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Content
  platform TEXT NOT NULL CHECK (platform IN ('linkedin', 'twitter', 'email', 'youtube', 'blog')),
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_generated_posts_platform ON generated_posts(platform);
CREATE INDEX IF NOT EXISTS idx_generated_posts_status ON generated_posts(status);
CREATE INDEX IF NOT EXISTS idx_generated_posts_user ON generated_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_generated_posts_airtable ON generated_posts(airtable_record_id) WHERE airtable_record_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_posts_ayrshare ON generated_posts(ayrshare_post_id) WHERE ayrshare_post_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_posts_published ON generated_posts(published_at DESC) WHERE status = 'published';
CREATE INDEX IF NOT EXISTS idx_generated_posts_thread ON generated_posts(slack_thread_ts) WHERE slack_thread_ts IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_posts_engagement ON generated_posts(engagement_rate DESC) WHERE engagement_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_generated_posts_embedding ON generated_posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION update_generated_posts_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generated_posts_updated_at
BEFORE UPDATE ON generated_posts
FOR EACH ROW
EXECUTE FUNCTION update_generated_posts_timestamp();

DO $$
BEGIN
  RAISE NOTICE '✅ Created generated_posts table';
END $$;

-- ============================================================================
-- STEP 6: Create/Update RAG search functions
-- ============================================================================

-- match_content_examples
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

-- match_research
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

-- match_company_documents
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

-- search_generated_posts
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
LANGUAGE sql STABLE
AS $$
  SELECT
    id, platform, post_hook, body_content, status, published_at,
    engagement_rate, airtable_record_id,
    1 - (embedding <=> query_embedding) as similarity
  FROM generated_posts
  WHERE embedding IS NOT NULL
    AND 1 - (embedding <=> query_embedding) > match_threshold
    AND (filter_platform IS NULL OR platform = filter_platform)
    AND (filter_status IS NULL OR status = filter_status)
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;

-- search_top_performing_posts
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
LANGUAGE sql STABLE
AS $$
  SELECT
    id, platform, post_hook, body_content, content_type,
    engagement_rate, impressions, engagements, published_at,
    1 - (embedding <=> query_embedding) as similarity
  FROM generated_posts
  WHERE status = 'published'
    AND engagement_rate IS NOT NULL
    AND engagement_rate >= min_engagement_rate
    AND embedding IS NOT NULL
    AND 1 - (embedding <=> query_embedding) > match_threshold
    AND (filter_platform IS NULL OR platform = filter_platform)
  ORDER BY engagement_rate DESC, embedding <=> query_embedding
  LIMIT match_count;
$$;

DO $$
BEGIN
  RAISE NOTICE '✅ Created/updated RAG search functions';
END $$;

-- ============================================================================
-- STEP 7: Create backward compatibility views
-- ============================================================================

-- Map old knowledge_base to company_documents
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

-- Map old content_performance to performance_analytics (if needed)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'content_performance') THEN
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

    RAISE NOTICE '✅ Created content_performance compatibility view';
  END IF;
END $$;

-- Old match_knowledge function → company_documents
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

DO $$
BEGIN
  RAISE NOTICE '✅ Created backward compatibility views and functions';
END $$;

-- ============================================================================
-- STEP 7: Update RLS policies
-- ============================================================================

ALTER TABLE research ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_posts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role can manage research" ON research;
CREATE POLICY "Service role can manage research" ON research FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage company_documents" ON company_documents;
CREATE POLICY "Service role can manage company_documents" ON company_documents FOR ALL USING (true);

DROP POLICY IF EXISTS "Service role can manage generated_posts" ON generated_posts;
CREATE POLICY "Service role can manage generated_posts" ON generated_posts FOR ALL USING (true);

-- Update performance_analytics RLS (in case it was renamed)
DO $$
BEGIN
  IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'performance_analytics') THEN
    ALTER TABLE performance_analytics ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS "Service role can manage content_performance" ON performance_analytics;
    DROP POLICY IF EXISTS "Service role can manage performance_analytics" ON performance_analytics;
    CREATE POLICY "Service role can manage performance_analytics" ON performance_analytics FOR ALL USING (true);
  END IF;
END $$;

DO $$
BEGIN
  RAISE NOTICE '✅ Updated RLS policies';
END $$;

-- ============================================================================
-- STEP 8: Create analytics view
-- ============================================================================

CREATE OR REPLACE VIEW top_performing_content AS
SELECT
  platform,
  content_type,
  AVG(quality_score) as avg_quality_score,
  AVG(human_score) as avg_human_score,
  AVG(engagement_rate) as avg_engagement_rate,
  COUNT(*) as content_count
FROM performance_analytics
WHERE published = true
  AND engagement_rate IS NOT NULL
GROUP BY platform, content_type
ORDER BY avg_engagement_rate DESC;

-- Analytics view for generated_posts
CREATE OR REPLACE VIEW generated_posts_analytics AS
SELECT
  platform,
  content_type,
  status,
  COUNT(*) as total_posts,
  AVG(quality_score) as avg_quality_score,
  AVG(engagement_rate) as avg_engagement_rate,
  AVG(impressions) as avg_impressions,
  SUM(engagements) as total_engagements,
  AVG(iterations) as avg_iterations
FROM generated_posts
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY platform, content_type, status
ORDER BY avg_engagement_rate DESC NULLS LAST;

DO $$
BEGIN
  RAISE NOTICE '✅ Created analytics views';
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '════════════════════════════════════════════════════════════';
  RAISE NOTICE '✅ Migration to Database Schema V2 complete!';
  RAISE NOTICE '════════════════════════════════════════════════════════════';
  RAISE NOTICE '';
  RAISE NOTICE 'Tables updated:';
  RAISE NOTICE '  ✓ content_examples - Updated with new fields';
  RAISE NOTICE '  ✓ conversation_history - No changes needed';
  RAISE NOTICE '  ✓ research - Created (NEW)';
  RAISE NOTICE '  ✓ company_documents - Created and migrated data';
  RAISE NOTICE '  ✓ performance_analytics - Renamed and enhanced';
  RAISE NOTICE '  ✓ generated_posts - Created (NEW in V2.1)';
  RAISE NOTICE '';
  RAISE NOTICE 'Data migrated:';
  RAISE NOTICE '  ✓ brand_voice → company_documents';
  RAISE NOTICE '  ✓ knowledge_base → company_documents';
  RAISE NOTICE '  ✓ content_performance → performance_analytics';
  RAISE NOTICE '';
  RAISE NOTICE 'Backward compatibility:';
  RAISE NOTICE '  ✓ Old table/function names still work';
  RAISE NOTICE '  ✓ Existing code continues to function';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '  1. Verify data in new tables';
  RAISE NOTICE '  2. Configure Google Drive in config/integrations.yaml';
  RAISE NOTICE '  3. Run: python tools/google_drive_sync.py';
  RAISE NOTICE '  4. Configure Airtable + Ayrshare (optional)';
  RAISE NOTICE '  5. Update code to use new table names (optional)';
  RAISE NOTICE '';
  RAISE NOTICE 'Happy creating! 🚀';
  RAISE NOTICE '';
END $$;

-- Database Schema V2: Future-Proof Distribution Architecture
-- Run this in Supabase SQL Editor for NEW installations
-- For existing databases, use migrate_to_v2.sql instead

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- TABLE 1: content_examples
-- Purpose: Dickie & Cole's proven content (90-100% human scores)
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_examples (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Content
  platform TEXT NOT NULL, -- 'LinkedIn', 'Twitter', 'Email', 'Blog'
  content TEXT NOT NULL,
  human_score INTEGER, -- 0-100 from GPTZero/Originality.ai

  -- Performance Metrics
  engagement_rate DECIMAL,
  impressions INTEGER,
  clicks INTEGER,
  content_type TEXT, -- 'framework_post', 'hot_take', 'list', 'story', 'comparison'

  -- Metadata
  creator TEXT, -- 'Cole', 'Dickie', 'Daniel'
  hook_line TEXT,
  main_points TEXT[],
  cta_line TEXT,
  tags TEXT[], -- ['productivity', 'writing', 'AI']
  topics TEXT[], -- For filtering by topic

  -- RAG Search
  embedding VECTOR(1536),

  -- Lifecycle
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'approved' -- 'approved', 'archived'
);

-- Indexes for performance
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
  metadata JSONB, -- Store tool calls, reactions, etc.

  -- Lifecycle
  created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
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
  summary TEXT NOT NULL, -- Executive summary of research
  full_report TEXT, -- Full digest/report if applicable
  key_stats TEXT[], -- ["60% of users prefer X", "Market grew 40% YoY"]

  -- Sources
  source_urls TEXT[], -- Array of URLs researched
  source_names TEXT[], -- ["Harvard Business Review", "McKinsey", "TechCrunch"]
  primary_source TEXT, -- Main/best source

  -- Verification
  credibility_score INTEGER DEFAULT 5, -- 1-10 (HBR=10, random blog=3)
  research_date DATE NOT NULL, -- When research was conducted
  last_verified DATE,

  -- Usage Tracking
  used_in_content_ids UUID[], -- Links to content that used this research
  usage_count INTEGER DEFAULT 0,
  topics TEXT[], -- ['retention', 'growth', 'AI']

  -- RAG Search
  embedding VECTOR(1536),

  -- Lifecycle
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'active' -- 'active', 'outdated', 'disputed'
);

-- Indexes
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
-- ============================================================================

CREATE TABLE IF NOT EXISTS company_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Document Identification
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  document_type TEXT NOT NULL, -- 'brand_guide', 'case_study', 'product_doc', 'voice_example', 'about_us'

  -- Google Drive Sync
  google_drive_file_id TEXT UNIQUE, -- For tracking updates
  google_drive_url TEXT,
  file_name TEXT,
  mime_type TEXT,
  last_synced TIMESTAMP,

  -- Brand Voice Fields (when document_type='brand_guide')
  voice_description TEXT,
  do_list TEXT[],
  dont_list TEXT[],
  signature_phrases TEXT[],
  forbidden_words TEXT[],
  tone TEXT,

  -- Access Control
  user_id TEXT, -- Owner
  team_id TEXT,
  searchable BOOLEAN DEFAULT true, -- Can RAG search this?

  -- RAG Search
  embedding VECTOR(1536),

  -- Lifecycle
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'active' -- 'active', 'archived', 'needs_sync'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_company_docs_type ON company_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_company_docs_user ON company_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_company_docs_team ON company_documents(team_id);
CREATE INDEX IF NOT EXISTS idx_company_docs_drive_id ON company_documents(google_drive_file_id);
CREATE INDEX IF NOT EXISTS idx_company_docs_status ON company_documents(status);
CREATE INDEX IF NOT EXISTS idx_company_docs_searchable ON company_documents(searchable) WHERE searchable = true;
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

-- ============================================================================
-- TABLE 5: performance_analytics
-- Purpose: Track quality during creation AND real-world performance post-publish
-- ============================================================================

CREATE TABLE IF NOT EXISTS performance_analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Content Reference
  content_id UUID, -- Links to content_examples if promoted to "proven"
  platform TEXT NOT NULL,
  content TEXT NOT NULL,
  content_type TEXT, -- 'framework_post', 'hot_take', etc.

  -- Creation Quality Metrics
  quality_score INTEGER NOT NULL, -- 0-25 from quality_check tool
  quality_breakdown JSONB, -- {hook: 5, clarity: 4, proof: 5, voice: 4, engagement: 5}
  human_score INTEGER, -- 0-100 from GPTZero (if tested)
  iterations INTEGER DEFAULT 1,
  time_to_create INTEGER, -- seconds
  tools_used TEXT[], -- ['generate_hooks', 'inject_proof', 'quality_check']

  -- Real-World Performance (Post-Publish)
  published BOOLEAN DEFAULT FALSE,
  published_at TIMESTAMP,
  published_url TEXT,

  -- Engagement Metrics (updated manually or via API)
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
  thread_ts TEXT, -- Slack thread where this was created

  -- Lifecycle
  created_at TIMESTAMP DEFAULT NOW(),
  last_updated TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_performance_user ON performance_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_platform ON performance_analytics(platform);
CREATE INDEX IF NOT EXISTS idx_performance_score ON performance_analytics(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_performance_published ON performance_analytics(published, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_performance_engagement ON performance_analytics(engagement_rate DESC) WHERE engagement_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_performance_thread ON performance_analytics(thread_ts);

-- Analytics View: Top Performers
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

-- ============================================================================
-- BACKWARD COMPATIBILITY VIEWS
-- Keep old table/function names working for existing code
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

-- Map old content_performance to performance_analytics
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

-- ============================================================================
-- TABLE 6: generated_posts
-- Purpose: AI-generated content with Airtable + Ayrshare publishing workflow
-- ============================================================================

CREATE TABLE IF NOT EXISTS generated_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Content
  platform TEXT NOT NULL CHECK (platform IN ('linkedin', 'twitter', 'email', 'youtube', 'blog')),
  post_hook TEXT,
  body_content TEXT NOT NULL,
  content_type TEXT,
  platform_metadata JSONB DEFAULT '{}',

  -- Airtable Integration (Content Calendar)
  airtable_record_id TEXT UNIQUE,
  airtable_url TEXT,
  airtable_status TEXT,

  -- Ayrshare Integration (Publishing Platform)
  ayrshare_post_id TEXT UNIQUE,
  ayrshare_platform_ids JSONB,

  -- Publishing Workflow
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'published', 'failed', 'archived')),
  scheduled_for TIMESTAMP,
  published_at TIMESTAMP,
  published_url TEXT,

  -- Performance Analytics (synced from Ayrshare)
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

-- Search past generated posts
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

-- Find top-performing posts
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

-- Analytics view
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

-- ============================================================================
-- ROW LEVEL SECURITY (Optional but recommended)
-- ============================================================================

ALTER TABLE content_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE research ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_posts ENABLE ROW LEVEL SECURITY;

-- Service role full access policies
CREATE POLICY "Service role can manage content_examples" ON content_examples FOR ALL USING (true);
CREATE POLICY "Service role can manage conversation_history" ON conversation_history FOR ALL USING (true);
CREATE POLICY "Service role can manage research" ON research FOR ALL USING (true);
CREATE POLICY "Service role can manage company_documents" ON company_documents FOR ALL USING (true);
CREATE POLICY "Service role can manage performance_analytics" ON performance_analytics FOR ALL USING (true);
CREATE POLICY "Service role can manage generated_posts" ON generated_posts FOR ALL USING (true);

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '✅ Database Schema V2 setup complete!';
  RAISE NOTICE '';
  RAISE NOTICE 'Tables created:';
  RAISE NOTICE '  1. content_examples - Proven content for RAG';
  RAISE NOTICE '  2. conversation_history - Slack context extraction';
  RAISE NOTICE '  3. research - Tavily digests and proof points';
  RAISE NOTICE '  4. company_documents - Google Drive synced docs';
  RAISE NOTICE '  5. performance_analytics - Quality and engagement tracking';
  RAISE NOTICE '  6. generated_posts - AI content with Airtable + Ayrshare sync';
  RAISE NOTICE '';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '  1. Configure Google Drive in config/integrations.yaml';
  RAISE NOTICE '  2. Run: python tools/google_drive_sync.py';
  RAISE NOTICE '  3. Load proven content examples (optional)';
  RAISE NOTICE '  4. Configure Airtable + Ayrshare for publishing (optional)';
  RAISE NOTICE '';
  RAISE NOTICE 'Happy creating! 🚀';
END $$;

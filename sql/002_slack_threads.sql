-- =====================================================
-- Migration: Add slack_threads table
-- =====================================================
-- Purpose: Track Slack thread-level state for content creation
-- This table stores metadata about ongoing content creation sessions

CREATE TABLE IF NOT EXISTS slack_threads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Slack Context
  thread_ts TEXT UNIQUE NOT NULL,      -- Slack thread timestamp (unique identifier)
  channel_id TEXT NOT NULL,            -- Slack channel ID
  user_id TEXT NOT NULL,               -- Slack user ID who created the thread

  -- Content Metadata
  platform TEXT NOT NULL,              -- linkedin, twitter, email, youtube
  latest_draft TEXT,                   -- Most recent content draft
  latest_score INTEGER DEFAULT 0,      -- Quality score (0-100)

  -- Workflow State
  status TEXT DEFAULT 'drafting',      -- drafting, approved, scheduled, published
  metadata JSONB,                      -- Store workflow results, hooks, etc.

  -- Lifecycle
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_slack_threads_thread_ts ON slack_threads(thread_ts);
CREATE INDEX IF NOT EXISTS idx_slack_threads_user_id ON slack_threads(user_id);
CREATE INDEX IF NOT EXISTS idx_slack_threads_status ON slack_threads(status);
CREATE INDEX IF NOT EXISTS idx_slack_threads_platform ON slack_threads(platform);
CREATE INDEX IF NOT EXISTS idx_slack_threads_created_at ON slack_threads(created_at DESC);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_slack_threads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_slack_threads_updated_at
  BEFORE UPDATE ON slack_threads
  FOR EACH ROW
  EXECUTE FUNCTION update_slack_threads_updated_at();

-- Comment for documentation
COMMENT ON TABLE slack_threads IS 'Tracks Slack conversation threads for content creation workflows';
COMMENT ON COLUMN slack_threads.thread_ts IS 'Slack thread timestamp - primary identifier for thread';
COMMENT ON COLUMN slack_threads.latest_draft IS 'Most recent version of content being drafted';
COMMENT ON COLUMN slack_threads.latest_score IS 'Quality score from validators (0-100)';
COMMENT ON COLUMN slack_threads.status IS 'Current state: drafting, approved, scheduled, or published';
COMMENT ON COLUMN slack_threads.metadata IS 'Additional workflow data (hooks tested, iterations, etc.)';

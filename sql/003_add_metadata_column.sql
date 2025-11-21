-- ============================================================================
-- MIGRATION 003: Add metadata column to company_documents
-- ============================================================================
-- This migration adds the missing metadata JSONB column to company_documents
-- Safe to run multiple times (uses IF NOT EXISTS logic)
--
-- Auto-runs on: npm start (via bootstrap_database.js)
-- ============================================================================

DO $$
BEGIN
  -- Check if metadata column exists
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'company_documents'
    AND column_name = 'metadata'
  ) THEN
    RAISE NOTICE '➕ Adding metadata column to company_documents...';
    ALTER TABLE company_documents ADD COLUMN metadata JSONB;
    RAISE NOTICE '✅ metadata column added';
  ELSE
    RAISE NOTICE '✅ metadata column already exists';
  END IF;
END $$;

-- Create index on metadata column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_indexes
    WHERE tablename = 'company_documents'
    AND indexname = 'idx_company_docs_metadata'
  ) THEN
    RAISE NOTICE '➕ Creating index on metadata column...';
    CREATE INDEX idx_company_docs_metadata ON company_documents USING GIN(metadata);
    RAISE NOTICE '✅ Index created';
  ELSE
    RAISE NOTICE '✅ Index already exists';
  END IF;
END $$;

-- Populate metadata column with google_drive_file_id for existing rows
-- Only if google_drive_file_id column exists
DO $$
DECLARE
  updated_count INTEGER;
BEGIN
  -- Check if google_drive_file_id column exists before using it
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'company_documents'
    AND column_name = 'google_drive_file_id'
  ) THEN
    UPDATE company_documents
    SET metadata = jsonb_build_object('google_drive_file_id', google_drive_file_id)
    WHERE google_drive_file_id IS NOT NULL
      AND (metadata IS NULL OR NOT metadata ? 'google_drive_file_id');

    GET DIAGNOSTICS updated_count = ROW_COUNT;

    IF updated_count > 0 THEN
      RAISE NOTICE '✅ Updated % rows with google_drive_file_id in metadata', updated_count;
    END IF;
  ELSE
    RAISE NOTICE '⏭️ google_drive_file_id column not present, skipping metadata population';
  END IF;

  RAISE NOTICE '✅ Migration 003 complete: metadata column';
END $$;

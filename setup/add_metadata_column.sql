-- ============================================================================
-- MIGRATION: Add metadata column to company_documents
-- ============================================================================
-- This migration adds the missing metadata JSONB column to company_documents
-- Safe to run multiple times (uses IF NOT EXISTS logic)
--
-- Run this if you get error: "column company_documents.metadata does not exist"
-- ============================================================================

DO $$
BEGIN
  RAISE NOTICE '🔧 Checking company_documents table for metadata column...';
END $$;

-- Add metadata column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'company_documents'
    AND column_name = 'metadata'
  ) THEN
    RAISE NOTICE '➕ Adding metadata column to company_documents...';
    ALTER TABLE company_documents ADD COLUMN metadata JSONB;
    RAISE NOTICE '✅ metadata column added successfully';
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
    RAISE NOTICE '✅ Index created successfully';
  ELSE
    RAISE NOTICE '✅ Index already exists';
  END IF;
END $$;

-- Populate metadata column with google_drive_file_id for existing rows
DO $$
DECLARE
  updated_count INTEGER;
BEGIN
  RAISE NOTICE '🔄 Populating metadata column for existing rows...';

  UPDATE company_documents
  SET metadata = jsonb_build_object('google_drive_file_id', google_drive_file_id)
  WHERE google_drive_file_id IS NOT NULL
    AND (metadata IS NULL OR NOT metadata ? 'google_drive_file_id');

  GET DIAGNOSTICS updated_count = ROW_COUNT;

  IF updated_count > 0 THEN
    RAISE NOTICE '✅ Updated % rows with google_drive_file_id in metadata', updated_count;
  ELSE
    RAISE NOTICE '✅ No rows needed updating';
  END IF;
END $$;

-- Verify the migration
DO $$
DECLARE
  column_exists BOOLEAN;
  index_exists BOOLEAN;
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '🔍 Verifying migration...';

  SELECT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'company_documents'
    AND column_name = 'metadata'
  ) INTO column_exists;

  SELECT EXISTS (
    SELECT 1
    FROM pg_indexes
    WHERE tablename = 'company_documents'
    AND indexname = 'idx_company_docs_metadata'
  ) INTO index_exists;

  IF column_exists AND index_exists THEN
    RAISE NOTICE '';
    RAISE NOTICE '✅ ============================================';
    RAISE NOTICE '✅ Migration Complete!';
    RAISE NOTICE '✅ ============================================';
    RAISE NOTICE '';
    RAISE NOTICE '✓ metadata column exists';
    RAISE NOTICE '✓ metadata index exists';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Your n8n workflow should now work without errors!';
    RAISE NOTICE '';
  ELSE
    RAISE NOTICE '❌ Migration verification failed!';
    IF NOT column_exists THEN
      RAISE NOTICE '  Missing: metadata column';
    END IF;
    IF NOT index_exists THEN
      RAISE NOTICE '  Missing: metadata index';
    END IF;
  END IF;
END $$;

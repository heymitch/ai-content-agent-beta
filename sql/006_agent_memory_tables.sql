-- Agent Memory Tables Migration
-- Based on n8n Agent Memory Template
-- Creates tables for storing document metadata and tabular data rows

-- 1. Create Documents Table and Match Function (if not exists)
-- This enables vector search on company_documents table
-- Note: If company_documents already exists, this will be skipped

DO $$
BEGIN
  -- Check if company_documents table already exists
  IF NOT EXISTS (
    SELECT FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename = 'company_documents'
  ) THEN
    -- Enable the pgvector extension to work with embedding vectors
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Create a table to store your documents
    CREATE TABLE company_documents (
      id bigserial primary key,
      content text, -- corresponds to Document.pageContent
      metadata jsonb, -- corresponds to Document.metadata
      embedding vector(1536) -- 1536 works for OpenAI embeddings, change if needed
    );

    -- Create a function to search for documents
    CREATE FUNCTION match_documents (
      query_embedding vector(1536),
      match_count int default null,
      filter jsonb DEFAULT '{}'
    ) RETURNS table (
      id bigint,
      content text,
      metadata jsonb,
      similarity float
    )
    LANGUAGE plpgsql
    AS $func$
    #variable_conflict use_column
    BEGIN
      RETURN QUERY
      SELECT
        id,
        content,
        metadata,
        1 - (company_documents.embedding <=> query_embedding) as similarity
      FROM company_documents
      WHERE metadata @> filter
      ORDER BY company_documents.embedding <=> query_embedding
      LIMIT match_count;
    END;
    $func$;

    RAISE NOTICE 'Created company_documents table and match_documents function';
  ELSE
    RAISE NOTICE 'company_documents table already exists, skipping creation';
  END IF;
END $$;

-- 2. Create Document Metadata Table
-- Stores metadata about uploaded documents (title, url, schema, etc.)
CREATE TABLE IF NOT EXISTS document_metadata (
    id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    schema TEXT
);

COMMENT ON TABLE document_metadata IS 'Stores metadata for documents uploaded to the agent memory system';
COMMENT ON COLUMN document_metadata.id IS 'Unique identifier for the document (e.g., Google Drive file ID)';
COMMENT ON COLUMN document_metadata.title IS 'Human-readable title of the document';
COMMENT ON COLUMN document_metadata.url IS 'URL to access the document';
COMMENT ON COLUMN document_metadata.schema IS 'JSON schema for tabular documents (columns/fields)';

-- 3. Create Document Rows Table (for Tabular Data)
-- Stores individual rows from spreadsheets, CSVs, etc.
CREATE TABLE IF NOT EXISTS document_rows (
    id SERIAL PRIMARY KEY,
    dataset_id TEXT REFERENCES document_metadata(id) ON DELETE CASCADE,
    row_data JSONB  -- Store the actual row data
);

COMMENT ON TABLE document_rows IS 'Stores individual rows from tabular documents (spreadsheets, CSVs)';
COMMENT ON COLUMN document_rows.dataset_id IS 'Foreign key to document_metadata.id';
COMMENT ON COLUMN document_rows.row_data IS 'JSONB representation of a single row from the document';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_document_rows_dataset_id ON document_rows(dataset_id);
CREATE INDEX IF NOT EXISTS idx_document_rows_data ON document_rows USING GIN (row_data);
CREATE INDEX IF NOT EXISTS idx_document_metadata_created_at ON document_metadata(created_at DESC);

-- Grant permissions (adjust based on your RLS policies)
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_rows ENABLE ROW LEVEL SECURITY;

-- Create basic RLS policies (customize based on your auth setup)
-- These allow authenticated users to read/write their own documents
DO $$
BEGIN
  -- Policy for document_metadata
  IF NOT EXISTS (
    SELECT FROM pg_policies
    WHERE tablename = 'document_metadata'
    AND policyname = 'Users can manage their own document metadata'
  ) THEN
    CREATE POLICY "Users can manage their own document metadata"
      ON document_metadata
      FOR ALL
      USING (true)
      WITH CHECK (true);
  END IF;

  -- Policy for document_rows
  IF NOT EXISTS (
    SELECT FROM pg_policies
    WHERE tablename = 'document_rows'
    AND policyname = 'Users can manage their own document rows'
  ) THEN
    CREATE POLICY "Users can manage their own document rows"
      ON document_rows
      FOR ALL
      USING (true)
      WITH CHECK (true);
  END IF;
END $$;

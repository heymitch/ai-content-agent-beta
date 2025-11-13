# 🚨 Quick Fix: "Delete Old Data Rows" Error

**If your n8n workflow is failing at the "Delete Old Data Rows" or "Delete Old Doc Rows" node**, follow these steps:

---

## The Problem

Your Supabase database is missing the `document_metadata` and `document_rows` tables because the "run once" setup nodes weren't completed.

## The Fix (5 Minutes)

### Step 1: Run This SQL in Supabase

1. Go to your Supabase Dashboard
2. Click **SQL Editor** (left sidebar)
3. Click **New Query**
4. Paste this entire SQL script:

```sql
-- Create missing tables for n8n Google Drive workflow

-- Table 1: document_metadata
CREATE TABLE IF NOT EXISTS document_metadata (
    id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    schema TEXT
);

-- Table 2: document_rows
CREATE TABLE IF NOT EXISTS document_rows (
    id SERIAL PRIMARY KEY,
    dataset_id TEXT REFERENCES document_metadata(id) ON DELETE CASCADE,
    row_data JSONB
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_document_metadata_created_at ON document_metadata(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_rows_dataset_id ON document_rows(dataset_id);
CREATE INDEX IF NOT EXISTS idx_document_rows_data ON document_rows USING GIN (row_data);

-- Enable Row Level Security
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_rows ENABLE ROW LEVEL SECURITY;

-- Add policies (allow all operations)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'document_metadata'
    AND policyname = 'Users can manage their own document metadata'
  ) THEN
    CREATE POLICY "Users can manage their own document metadata"
      ON document_metadata FOR ALL
      USING (true) WITH CHECK (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'document_rows'
    AND policyname = 'Users can manage their own document rows'
  ) THEN
    CREATE POLICY "Users can manage their own document rows"
      ON document_rows FOR ALL
      USING (true) WITH CHECK (true);
  END IF;
END $$;

-- Success message
DO $$
BEGIN
  RAISE NOTICE '✅ Tables created successfully!';
  RAISE NOTICE 'You can now re-run your n8n workflow.';
END $$;
```

5. Click **Run** (or press `Cmd+Enter` / `Ctrl+Enter`)
6. Look for success message: "✅ Tables created successfully!"

### Step 2: Verify Tables Exist

Run this query in Supabase SQL Editor:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('document_metadata', 'document_rows', 'company_documents')
ORDER BY table_name;
```

You should see all 3 tables listed.

### Step 3: Test n8n Workflow

1. Go back to n8n
2. Open your "Google Drive → Vector DB" workflow
3. Add a test file to your monitored Google Drive folder
4. Watch the workflow execute
5. It should now complete without errors! ✅

---

## Still Having Issues?

### Error: "column metadata->>file_id does not exist"

Your "Delete Old Doc Rows" node has the wrong filter syntax.

**Fix:**

1. Open the "Delete Old Doc Rows" node in n8n
2. Find the **Filter String** field
3. Change it from:
   ```
   metadata->>file_id=like.*{{ $json.file_id }}*
   ```
   To:
   ```
   metadata->>'google_drive_file_id'=eq.{{ $('Set File ID').item.json.file_id }}
   ```
4. Save and re-test

### Error: "relation company_documents does not exist"

You need to run the full bootstrap script. Contact Mitch for the complete setup.

---

## For Future Deployments

The 3 "Run Once" PostgreSQL nodes at the top of your workflow are no longer needed. Mitch is creating an automated setup script so you won't have to click them manually anymore.

For now, just make sure the SQL above is run once, and you're good to go!

---

## Questions?

Message in Slack or reach out to Mitch directly.

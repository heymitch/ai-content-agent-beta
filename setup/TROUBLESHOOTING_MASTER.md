# 🔧 Master Troubleshooting Guide - n8n Google Drive Workflow

Complete troubleshooting guide for all common errors in the n8n Google Drive → Vector DB workflow.

---

## Error 1: "permission denied for table company_documents"

### Symptoms
```
403 - permission denied for table company_documents
Node: "Delete Old Doc Rows"
```

### Root Cause
**You're using the wrong Supabase API key in n8n** (using `anon` key instead of `service_role` key)

### Fix (5 minutes)

#### Step 1: Get the Correct Key

1. Go to **Supabase Dashboard** → **Settings** → **API**
2. Scroll to "Project API keys"
3. Look for two keys:
   - ❌ `anon public` - shorter key
   - ✅ `service_role secret` - **USE THIS ONE**

#### Step 2: Update n8n Credential

1. In n8n: **Settings** → **Credentials**
2. Find your **"Supabase API"** credential
3. Click to edit
4. Update **Supabase Key** field:
   - Replace with the full `service_role` key
   - Should be 300+ characters
   - Should start with `eyJ`
   - No "Bearer" prefix
5. **Save**

#### Step 3: Test

Re-run your workflow. The "permission denied" error should be gone.

### How to Verify You Have the Right Key

Decode your key at https://jwt.io - it should show:
```json
{
  "role": "service_role"  ← Should say this
}
```

NOT:
```json
{
  "role": "anon"  ← Wrong!
}
```

See [diagnose_n8n_credentials.md](./diagnose_n8n_credentials.md) for detailed guide.

---

## Error 2: "relation document_rows does not exist" / "table does not exist"

### Symptoms
```
ERROR: relation "document_rows" does not exist
ERROR: relation "document_metadata" does not exist
Node: "Delete Old Data Rows" or "Insert Document Metadata"
```

### Root Cause
Missing tables in your Supabase database.

### Fix (2 minutes)

Run this SQL in **Supabase SQL Editor**:

```sql
-- Create missing tables
CREATE TABLE IF NOT EXISTS document_metadata (
    id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    schema TEXT
);

CREATE TABLE IF NOT EXISTS document_rows (
    id SERIAL PRIMARY KEY,
    dataset_id TEXT REFERENCES document_metadata(id) ON DELETE CASCADE,
    row_data JSONB
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_document_metadata_created_at ON document_metadata(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_rows_dataset_id ON document_rows(dataset_id);
CREATE INDEX IF NOT EXISTS idx_document_rows_data ON document_rows USING GIN (row_data);

-- Enable RLS
ALTER TABLE document_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_rows ENABLE ROW LEVEL SECURITY;

-- Add permissive policies
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'document_metadata'
  ) THEN
    CREATE POLICY "Allow all on document_metadata"
      ON document_metadata FOR ALL USING (true) WITH CHECK (true);
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'document_rows'
  ) THEN
    CREATE POLICY "Allow all on document_rows"
      ON document_rows FOR ALL USING (true) WITH CHECK (true);
  END IF;
END $$;
```

### Verify

Run this query to confirm tables exist:
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('document_metadata', 'document_rows')
ORDER BY table_name;
```

Should return both tables.

---

## Error 3: "invalid filter syntax" / "metadata->>file_id does not exist"

### Symptoms
```
ERROR: column "metadata->>file_id" does not exist
ERROR: invalid filter syntax
Node: "Delete Old Doc Rows"
```

### Root Cause
Incorrect filter syntax in the Supabase delete node.

### Fix

Update the **"Delete Old Doc Rows"** node in n8n:

**Current (broken):**
```
Filter Type: string
Filter String: metadata->>file_id=like.*{{ $json.file_id }}*
```

**Fixed:**
```
Filter Type: string
Filter String: metadata->>'google_drive_file_id'=eq.{{ $('Set File ID').item.json.file_id }}
```

**Changes:**
- `file_id` → `google_drive_file_id` (correct key name)
- `like.*` → `=eq.` (correct Supabase PostgREST syntax)
- Correct node reference: `$('Set File ID').item.json.file_id`

---

## Error 4: Workflow Never Triggers

### Symptoms
- Workflow never runs automatically
- Files added to Google Drive don't trigger workflow

### Root Causes & Fixes

#### Cause 1: Wrong Google Drive Folder ID

**Fix:**
1. Open your Google Drive folder in browser
2. Check URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
3. In n8n, open **"File Created"** or **"File Updated"** trigger node
4. Verify **Folder to Watch** matches the correct folder ID

#### Cause 2: OAuth Token Expired

**Fix:**
1. In n8n: **Settings** → **Credentials**
2. Find **"Google Drive OAuth2"** credential
3. Click **Reconnect**
4. Authorize again

#### Cause 3: Trigger Not Active

**Fix:**
1. Open workflow in n8n
2. Make sure workflow is **Active** (toggle in top-right)
3. Check trigger nodes have green "active" indicator

---

## Error 5: "vector extension does not exist"

### Symptoms
```
ERROR: type "vector" does not exist
ERROR: extension "vector" does not exist
```

### Root Cause
pgvector extension not enabled in Supabase.

### Fix

Run this SQL in **Supabase SQL Editor**:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Then verify:
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

Should return 1 row.

---

## Error 6: "match_documents function does not exist"

### Symptoms
```
ERROR: function match_documents does not exist
Node: "Insert into Supabase Vectorstore"
```

### Root Cause
Missing RAG search function.

### Fix

Run this SQL in **Supabase SQL Editor**:

```sql
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(1536),
  match_count int DEFAULT NULL,
  filter jsonb DEFAULT '{}'
) RETURNS TABLE (
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
```

---

## Error 7: OpenAI Embeddings Fail

### Symptoms
```
ERROR: Invalid API key
Node: "Embeddings OpenAI1"
```

### Fix

1. Verify your OpenAI API key is valid
2. In n8n: **Settings** → **Credentials**
3. Find **"OpenAi account"** credential
4. Update with correct API key from https://platform.openai.com/api-keys
5. Make sure key has `text-embedding-3-small` model access

---

## Error 8: PostgreSQL Connection Fails

### Symptoms
```
ERROR: connection refused
ERROR: password authentication failed
Node: "Insert Document Metadata" (PostgreSQL nodes)
```

### Root Cause
**You shouldn't be using PostgreSQL nodes at all!**

### Fix

1. **Delete** these three nodes from your workflow:
   - ❌ "Create Documents Table and Match Function"
   - ❌ "Create Document Metadata Table"
   - ❌ "Create Document Rows Table"

2. Run the bootstrap script instead: `./deploy_to_client.sh "[DB-URL]"`

Tables should be created by the bootstrap script, not by workflow nodes.

---

## Complete Fix Checklist

### For Fresh Deployments

- [ ] Run `bootstrap_supabase.sql` (creates all tables automatically)
- [ ] Remove 3 PostgreSQL "Create Table" nodes from workflow
- [ ] Use **service_role** key (not anon key) in n8n Supabase credential
- [ ] Verify OpenAI API key is valid
- [ ] Configure Google Drive OAuth2
- [ ] Set correct Google Drive folder ID
- [ ] Activate workflow
- [ ] Test with sample file

### For Existing Deployments (Fixing Errors)

1. **Fix permission errors:**
   - [ ] Update n8n Supabase credential with `service_role` key
   - [ ] Run RLS policy fix SQL (see Error 1)

2. **Fix missing tables:**
   - [ ] Run table creation SQL (see Error 2)
   - [ ] Or run full bootstrap script

3. **Fix filter syntax:**
   - [ ] Update "Delete Old Doc Rows" node filter (see Error 3)

4. **Test workflow:**
   - [ ] Add test file to Google Drive
   - [ ] Verify workflow completes successfully
   - [ ] Check data in Supabase tables

---

## Quick Diagnosis Flow

```
Is workflow erroring?
│
├─ "permission denied"
│  └─ Check: Using service_role key? (Error 1)
│
├─ "table does not exist"
│  └─ Run: Table creation SQL (Error 2)
│
├─ "invalid filter syntax"
│  └─ Fix: Update delete node filter (Error 3)
│
├─ Workflow never runs
│  └─ Check: Folder ID, OAuth, Active toggle (Error 4)
│
├─ "vector extension"
│  └─ Run: CREATE EXTENSION vector (Error 5)
│
├─ "function does not exist"
│  └─ Run: CREATE FUNCTION match_documents (Error 6)
│
└─ "OpenAI API error"
   └─ Fix: Update OpenAI credential (Error 7)
```

---

## Still Stuck?

1. **Check n8n execution logs:**
   - Workflow → Executions
   - Click failed execution
   - Expand error node to see full error message

2. **Check Supabase logs:**
   - Supabase Dashboard → Logs
   - Look for recent errors

3. **Verify database state:**
   ```sql
   -- Check tables exist
   SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

   -- Check RLS policies
   SELECT tablename, policyname, cmd FROM pg_policies;

   -- Check vector extension
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

4. **Run full bootstrap script:**
   - This fixes most issues
   - Safe to run multiple times
   - See [bootstrap_supabase.sql](./bootstrap_supabase.sql)

---

## Prevention

To avoid these issues in future deployments:

1. **Always run bootstrap script first** before importing workflow
2. **Always use service_role key** in n8n (never anon key)
3. **Remove manual setup nodes** from workflow (3 PostgreSQL nodes)
4. **Test with one file** before going live

See [CLIENT_DEPLOYMENT_GUIDE.md](./CLIENT_DEPLOYMENT_GUIDE.md) for complete setup process.

# n8n Google Drive Workflow - Fixes for Client Deployments

## Problem

Clients are experiencing failures at the **"Delete Old Doc Rows"** Supabase node with errors like:
- `ERROR: column "metadata" does not exist`
- `ERROR: invalid filter syntax`
- Workflow stops at first Supabase delete operation

## Root Cause: Why It Works for You But Not Clients

**Your Working Setup:**
- The n8n workflow stores `google_drive_file_id` in the `metadata` JSONB column
- The filter `metadata->>file_id=like.*{{ $json.file_id }}*` works (kind of)
- Your actual data shows `google_drive_file_id` is stored in metadata, not the direct column

**Client Deployments (Broken):**
- Fresh installs start with empty tables
- The Supabase node's filter syntax `metadata->>file_id=like.*...` is **not valid** in the n8n Supabase node UI
- The n8n vectorstore writes to `metadata` JSONB, but the key name is wrong (`google_drive_file_id` not `file_id`)

**The Core Issue:**
1. The filter queries `metadata->>file_id` (wrong key name)
2. But n8n stores it as `metadata->>'google_drive_file_id'` (correct key name)
3. The syntax with `like.*` regex is invalid in Supabase node
4. Fresh databases have no data, so the broken filter causes immediate failure

## Solution: Two Options

### Option A: Use JSONB Metadata Column (Recommended - Matches Current Behavior)

This keeps your existing data structure and fixes the filter syntax.

#### 1. Fix "Delete Old Doc Rows" Node

**Current (BROKEN):**
```
Operation: delete
Table: company_documents
Filter Type: string
Filter String: metadata->>file_id=like.*{{ $json.file_id }}*
```

**Fixed Configuration:**
```
Operation: delete
Table: company_documents
Filter Type: string
Filter String: metadata->>'google_drive_file_id'=eq.{{ $('Set File ID').item.json.file_id }}
```

**Why this works:**
- Uses correct JSONB operator `->>` (returns text)
- Uses correct key name `google_drive_file_id` (not `file_id`)
- Uses Supabase PostgREST syntax `=eq.` (not `like.*`)
- References the correct upstream node

---

### Option B: Use Direct Column (Cleaner Schema)

This populates the dedicated `google_drive_file_id` column instead of JSONB.

#### Changes Needed:

1. **Remove the file_id from metadata in "Default Data Loader"**
   - Currently adds `google_drive_file_id` to metadata
   - This is fine, keep as is for backward compatibility

2. **Add "Set google_drive_file_id Column" node** after vectorstore insert
   - Use Supabase "Update" node
   - Update `company_documents` table
   - Set `google_drive_file_id = {{ $('Set File ID').item.json.file_id }}`
   - Filter: where `id` equals the inserted record ID

3. **Fix "Delete Old Doc Rows" Node**
   ```
   Operation: delete
   Table: company_documents
   Filter Type: Manual
   Filters:
     - Key Name: google_drive_file_id
     - Condition: eq
     - Key Value: ={{ $('Set File ID').item.json.file_id }}
   ```

---

## Recommended: Use Option A (JSONB Metadata)

**Why?**
- Matches your current working setup
- Minimal changes to workflow
- n8n vectorstore naturally writes to metadata
- One simple filter fix

Only use Option B if you want cleaner SQL queries in the future.

### 2. Delete "Delete Old Data Rows" Node Configuration

**Current (BROKEN):**
- Operation: `delete`
- Table: `document_rows`
- Filter on `dataset_id` with `eq` condition

**This one is actually CORRECT** - keep as is:
- Operation: `delete`
- Table: `document_rows`
- Filters → Condition:
  - Key Name: `dataset_id`
  - Condition: `eq`
  - Key Value: `={{ $('Set File ID').item.json.file_id }}`

---

## Nodes to REMOVE (No Longer Needed)

Delete these three "Run Once" PostgreSQL nodes:
1. ❌ **"Create Documents Table and Match Function"**
2. ❌ **"Create Document Metadata Table"**
3. ❌ **"Create Document Rows Table (for Tabular Data)"**

**Why?** The bootstrap script (`bootstrap_supabase.sql`) now creates ALL tables automatically. Clients don't need to manually run setup nodes anymore.

---

## Step-by-Step Fix Instructions for n8n

### Step 1: Run Bootstrap Script First

**Before importing the workflow**, run the bootstrap script to create all tables:

```bash
cd setup
./deploy_to_client.sh "postgresql://postgres.[CLIENT-PROJECT]:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
```

This creates:
- `company_documents` (with `google_drive_file_id` column)
- `document_metadata`
- `document_rows`
- All other required tables

### Step 2: Import Updated Workflow

Import the n8n workflow JSON with these changes already applied.

### Step 3: Update Credentials

Update these credentials in n8n:
1. **Supabase API** - Client's Supabase URL + Service Key
2. **Google Drive OAuth** - Client's Google Drive credentials
3. **PostgreSQL** - Client's Supabase database connection string
4. **OpenAI API** - Client's OpenAI API key

### Step 4: Test the Workflow

1. **Create a test file** in the monitored Google Drive folder
2. **Wait for trigger** or click "Test Workflow"
3. **Verify**:
   - No errors on "Delete Old Doc Rows" node ✅
   - Document metadata inserted ✅
   - Embeddings created in `company_documents` ✅

---

## Technical Details: Why the Old Filter Failed

### Old Filter (BROKEN)
```
metadata->>file_id=like.*{{ $json.file_id }}*
```

**Problems:**
1. Uses PostgreSQL JSONB operator (`->>`) which Supabase node doesn't support directly
2. Assumes `metadata` column exists with nested `file_id`
3. Uses regex `like.*` syntax which isn't valid in Supabase node filters

### New Filter (WORKING)
```javascript
Filters:
  - Key Name: google_drive_file_id
  - Condition: eq
  - Key Value: ={{ $('Set File ID').item.json.file_id }}
```

**Why it works:**
1. Uses the actual column name from our schema
2. Uses Supabase node's built-in filter UI (not raw SQL)
3. Simple equality check (exact match on file ID)

---

## Database Schema Reference

The `company_documents` table structure (relevant columns):

```sql
CREATE TABLE company_documents (
  id UUID PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  document_type TEXT NOT NULL,

  -- Google Drive Sync (THIS IS WHAT WE FILTER ON)
  google_drive_file_id TEXT UNIQUE,  -- ⭐ Use this for filtering!
  google_drive_url TEXT,
  file_name TEXT,
  mime_type TEXT,
  last_synced TIMESTAMP,

  -- RAG Search
  embedding VECTOR(1536),

  -- Also has metadata JSONB, but we don't use it for file_id
  metadata JSONB,

  -- Lifecycle
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'active'
);
```

**Key Point:** The `google_drive_file_id` is a **direct TEXT column**, not nested in JSONB. That's why `metadata->>file_id` fails.

---

## Quick Checklist for Client Deployments

- [ ] Run `bootstrap_supabase.sql` on client's Supabase instance
- [ ] Verify tables exist in Supabase SQL Editor:
  - [ ] `company_documents`
  - [ ] `document_metadata`
  - [ ] `document_rows`
  - [ ] `content_examples`
  - [ ] `research`
  - [ ] `generated_posts`
  - [ ] `slack_threads`
  - [ ] `conversation_history`
  - [ ] `performance_analytics`
- [ ] Import n8n workflow with fixed delete nodes
- [ ] Remove the three "Create Table" PostgreSQL nodes
- [ ] Update all credentials (Supabase, Google Drive, PostgreSQL, OpenAI)
- [ ] Test workflow with a sample Google Drive file
- [ ] Verify no errors on Supabase nodes

---

## Support

If clients still experience issues after these fixes:

1. **Check Supabase connection**: Verify their IP is whitelisted
2. **Check table existence**: Run this in Supabase SQL Editor:
   ```sql
   SELECT table_name
   FROM information_schema.tables
   WHERE table_schema = 'public'
   AND table_name IN ('company_documents', 'document_metadata', 'document_rows');
   ```
3. **Check column names**: Run this to verify `google_drive_file_id` exists:
   ```sql
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'company_documents';
   ```
4. **Re-run bootstrap script** to ensure all migrations applied correctly

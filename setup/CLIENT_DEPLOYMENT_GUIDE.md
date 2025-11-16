# Client Deployment Guide - AI Content Agent

Complete step-by-step guide to deploy the AI Content Agent to a client's infrastructure.

---

## Prerequisites

### Client Must Provide:
- [ ] Supabase project URL
- [ ] Supabase service role key (from Settings → API)
- [ ] Supabase database connection string (from Settings → Database → Connection String → URI)
- [ ] n8n instance (cloud or self-hosted)
- [ ] Google Drive account for document sync (optional)
- [ ] OpenAI API key
- [ ] Slack workspace (if using Slack agent)

### Tools You Need:
- [ ] PostgreSQL client (`psql`) installed
- [ ] Terminal access
- [ ] This repository cloned

---

## Step 1: Deploy Database Schema

### 1.1. Get Client's Database Connection String

Ask client to navigate to:
```
Supabase Dashboard → Settings → Database → Connection String → URI
```

Example format:
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:5432/postgres
```

### 1.2. Run Bootstrap Script

```bash
cd setup
./deploy_to_client.sh "postgresql://postgres.[CLIENT-PROJECT]:[PASSWORD]@[HOST]:5432/postgres"
```

**What this creates:**
- 9 database tables (content_examples, research, company_documents, etc.)
- RAG search functions with vector embeddings
- Row Level Security policies
- Indexes for performance
- Backward compatibility views

**Expected output:**
```
✅ Deployment Successful!
📋 What was created:
  • 9 tables (content_examples, research, etc.)
  • RAG search functions
  ...
```

### 1.3. Verify Tables Created

Have client check their Supabase SQL Editor:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Expected tables:**
- `company_documents`
- `content_examples`
- `conversation_history`
- `document_metadata`
- `document_rows`
- `generated_posts`
- `performance_analytics`
- `research`
- `slack_threads`

### 1.4. Run Migration (If Upgrading Existing Database)

If the client already has an older database and gets error: **"column company_documents.metadata does not exist"**, run this migration:

```bash
cd setup
psql "postgresql://postgres.[CLIENT-PROJECT]:[PASSWORD]@[HOST]:5432/postgres" -f add_metadata_column.sql
```

**OR** have client run this in Supabase SQL Editor:

```sql
-- Copy and paste the contents of setup/add_metadata_column.sql
```

**What this adds:**
- `metadata` JSONB column to `company_documents` table
- Index on metadata column for performance
- Populates metadata with existing `google_drive_file_id` values

**When to run this:**
- If n8n workflow fails with "column metadata does not exist"
- If upgrading from a database created before metadata column was added
- Safe to run multiple times (idempotent)

---

## Step 2: Configure Environment Variables

### 2.1. Create Client's .env File

Copy the template and fill in client's credentials:

```bash
# Supabase
SUPABASE_URL="https://[CLIENT-PROJECT].supabase.co"
SUPABASE_KEY="[CLIENT-SERVICE-ROLE-KEY]"
SUPABASE_DB_URL="postgresql://postgres.[CLIENT-PROJECT]:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

# OpenAI
OPENAI_API_KEY="sk-proj-..."

# Tavily (for research)
TAVILY_API_KEY="tvly-..."

# Slack (if using Slack agent)
SLACK_BOT_TOKEN="xoxb-..."
SLACK_SIGNING_SECRET="..."

# Optional: Airtable + Ayrshare for publishing
AIRTABLE_ACCESS_TOKEN="pat..."
AIRTABLE_BASE_ID="app..."
AIRTABLE_TABLE_NAME="tbl..."
AYRSHARE_API_KEY="..."

# Session Secret (generate with: openssl rand -base64 64)
SESSION_SECRET="[GENERATED-SECRET]"
```

### 2.2. Generate Session Secret

```bash
openssl rand -base64 64
```

---

## Step 3: Deploy n8n Workflow (Google Drive Sync)

### 3.1. Fix the Workflow JSON

Before importing, update the "Delete Old Doc Rows" node in the workflow JSON.

**Find this node:**
```json
{
  "name": "Delete Old Doc Rows",
  "type": "n8n-nodes-base.supabase",
  "parameters": {
    "operation": "delete",
    "tableId": "company_documents",
    "filterType": "string",
    "filterString": "=metadata->>file_id=like.*{{ $json.file_id }}*"
  }
}
```

**Replace `filterString` with:**
```json
"filterString": "metadata->>'google_drive_file_id'=eq.{{ $('Set File ID').item.json.file_id }}"
```

### 3.2. Remove "Run Once" Setup Nodes

Delete these three PostgreSQL nodes from the workflow:
1. ❌ "Create Documents Table and Match Function"
2. ❌ "Create Document Metadata Table"
3. ❌ "Create Document Rows Table (for Tabular Data)"
4. ❌ Delete the sticky note that says "Run Each Node Once to Set Up Database Tables"

**Why?** The bootstrap script already created all tables.

### 3.3. Import Workflow to Client's n8n

1. Open client's n8n instance
2. Click **Workflows** → **Add Workflow** → **Import from File**
3. Upload the fixed workflow JSON
4. Rename to "Google Drive → Vector DB Sync"

### 3.4. Configure Credentials

Update these credentials in the workflow:

#### Supabase API Credential:
- **Supabase URL:** `https://[CLIENT-PROJECT].supabase.co`
- **Supabase Key:** `[CLIENT-SERVICE-ROLE-KEY]`

#### PostgreSQL Credential:
- **Host:** `aws-1-us-east-1.pooler.supabase.com`
- **Database:** `postgres`
- **User:** `postgres.[CLIENT-PROJECT]`
- **Password:** `[CLIENT-DB-PASSWORD]`
- **Port:** `5432`
- **SSL:** `require`

#### Google Drive OAuth2:
- Client must authorize their Google account
- Set up OAuth2 app in Google Cloud Console
- Grant Drive read permissions

#### OpenAI API:
- **API Key:** `[CLIENT-OPENAI-KEY]`

### 3.5. Test the Workflow

1. Create a test Google Doc in the monitored folder
2. Wait for trigger (or click "Test Workflow")
3. Verify:
   - ✅ No errors on "Delete Old Doc Rows"
   - ✅ Document inserted into `company_documents`
   - ✅ Embeddings created
   - ✅ Metadata saved to `document_metadata`

---

## Step 4: Deploy the Agent (Python SDK)

### 4.1. Clone Repository on Client's Server

```bash
git clone [YOUR-REPO-URL]
cd ai-content-agent-template
```

### 4.2. Install Dependencies

```bash
# Python 3.11+ required
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4.3. Copy Environment Variables

```bash
cp .env.example .env
# Edit .env with client's credentials
nano .env
```

### 4.4. Test Agent Connection

```bash
python test_connection.py
```

**Expected output:**
```
✅ Supabase connection successful
✅ OpenAI API working
✅ Found X content examples
✅ Agent ready to use
```

### 4.5. Start Agent

For **Slack agent**:
```bash
python agents/slack_agent.py
```

For **standalone CLI**:
```bash
python agents/cli_agent.py
```

For **Replit deployment**:
```bash
# Configure Replit secrets with .env values
# Run the main.py file
```

---

## Step 5: Verify Everything Works

### 5.1. Test Database Access

```bash
psql "[CLIENT-DB-URL]" -c "SELECT COUNT(*) FROM company_documents;"
```

Should return `0` (empty table) or show existing documents.

### 5.2. Test RAG Search

In Python:
```python
from supabase import create_client
import openai

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

# Create test embedding
response = openai.embeddings.create(
    model="text-embedding-3-small",
    input="test query"
)
embedding = response.data[0].embedding

# Test RAG search
result = supabase.rpc('match_content_examples', {
    'query_embedding': embedding,
    'match_count': 5
}).execute()

print(f"Found {len(result.data)} results")
```

### 5.3. Test Content Generation

Via Slack:
```
@Agent create a LinkedIn post about [topic]
```

Via CLI:
```python
python -c "from agents.content_generator import generate_content; \
print(generate_content(platform='linkedin', topic='AI in marketing'))"
```

---

## Step 6: Load Initial Data (Optional)

### 6.1. Import Proven Content Examples

If you have a CSV of proven high-performing content:

```bash
python scripts/import_content_examples.py --file proven_content.csv
```

### 6.2. Import Company Documents

Manually upload to Google Drive folder → n8n workflow syncs automatically

Or use direct upload:

```bash
python scripts/import_documents.py --folder path/to/brand_guides/
```

---

## Troubleshooting

### Issue: "Delete Old Doc Rows" node fails

**Solution:** Verify filter syntax in n8n node:
```
metadata->>'google_drive_file_id'=eq.{{ $('Set File ID').item.json.file_id }}
```

NOT:
```
metadata->>file_id=like.*{{ $json.file_id }}*
```

### Issue: "Table does not exist"

**Solution:** Re-run bootstrap script:
```bash
./deploy_to_client.sh "[CLIENT-DB-URL]"
```

### Issue: RLS blocking queries

**Solution:** Verify policies exist:
```sql
SELECT * FROM pg_policies WHERE tablename = 'company_documents';
```

Should show both service role and read policies.

### Issue: Vector embeddings not creating

**Solution:** Check OpenAI API key is valid:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Issue: n8n workflow never triggers

**Solution:**
1. Check Google Drive folder ID is correct
2. Verify OAuth2 token is active
3. Test manual execution first

---

## Post-Deployment Checklist

- [ ] All 9 database tables exist
- [ ] RLS policies enabled on all tables
- [ ] n8n workflow runs without errors
- [ ] Google Drive sync working
- [ ] Agent can generate content
- [ ] RAG search returns relevant results
- [ ] Environment variables secured (not committed to git)
- [ ] Client has access to Supabase dashboard
- [ ] Client has access to n8n dashboard
- [ ] Documentation provided to client

---

## Maintenance

### Weekly:
- Check n8n workflow execution history for errors
- Monitor Supabase table sizes
- Review generated content quality scores

### Monthly:
- Update proven content examples with high performers
- Archive outdated research entries
- Review and optimize database indexes

### As Needed:
- Add new proven content examples
- Update brand voice documents
- Sync new documents from Google Drive

---

## Support

For issues:
1. Check logs in n8n workflow executions
2. Check Supabase logs in Dashboard → Logs
3. Run verification SQL queries (see Step 5)
4. Contact support with error messages + logs

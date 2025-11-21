# Bootstrap Troubleshooting Guide

## Error: "return type mismatch in function declared to return record"

This error occurs when trying to apply SQL migrations that create or modify PostgreSQL functions. Here's how to fix it.

### Quick Diagnosis

Run the diagnostic script to identify the root cause:

```bash
node scripts/diagnose_supabase.js
```

This will check:
- ✅ Database connection
- ✅ Required extensions (uuid-ossp, vector)
- ✅ Tables exist (company_documents, content_examples, etc.)
- ✅ RPC functions are created correctly
- ✅ Migration history

### Common Causes & Fixes

#### 1. Vector Extension Not Enabled

**Symptom:** Diagnostic shows "No required extensions found"

**Fix:** Run this in Supabase SQL Editor:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
```

Then retry bootstrap:
```bash
npm run bootstrap
```

#### 2. Migration 001 Never Applied

**Symptom:** Diagnostic shows "No tables found" or "No RPC functions found"

**Fix:** Manually apply the base migration:

1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `sql/001_full_database.sql`
3. Paste and run
4. Check for errors in output
5. Retry bootstrap: `npm run bootstrap`

#### 3. Permissions Issue (Client Setup)

**Symptom:** Client's Supabase account can't create extensions or functions

**Fix:** Check their role permissions:

```sql
-- Check current role
SELECT current_user;

-- Check if user can create extensions
SELECT * FROM pg_roles WHERE rolname = current_user;
```

For client setups, they may need:
- **Supabase Owner** role (not just Member)
- **Database password** (not just anon/service keys)
- **Direct PostgreSQL access** enabled

**Alternative:** Have them apply migrations via Supabase Dashboard SQL Editor as the `postgres` user.

#### 4. Type Mismatch in Existing Function

**Symptom:** Function exists but with wrong signature

**Fix:** Drop and recreate using the defensive migration:

```bash
# In Supabase SQL Editor, run:
sql/003_fix_company_documents_filter_v2.sql
```

This version:
- Checks prerequisites first
- Drops all possible function signature variants
- Casts types explicitly (`::float`)
- Verifies function works after creation

#### 5. Stale Migration Tracking

**Symptom:** Bootstrap says "Already applied" but function doesn't work

**Fix:** Clear migration history and reapply:

```sql
-- Check what's marked as applied
SELECT * FROM schema_migrations ORDER BY applied_at DESC;

-- Option A: Remove specific migration
DELETE FROM schema_migrations WHERE migration_name = '003_fix_company_documents_filter.sql';

-- Option B: Start fresh (DANGER: only if safe)
TRUNCATE schema_migrations;
```

Then run: `npm run bootstrap`

### Client Setup Checklist

When setting up for a client, ensure:

- [ ] They have **Supabase Owner** role on the project
- [ ] Extensions are enabled: `uuid-ossp`, `vector`
- [ ] You have the **database connection string** (not just API keys)
  - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`
  - Get from: Supabase Dashboard → Project Settings → Database → Connection String
- [ ] Their firewall/network allows PostgreSQL connections (port 5432)
- [ ] You're using `SUPABASE_DB_URL` (not `SUPABASE_URL` which is for REST API)

### Testing the Fix

After applying fixes, verify everything works:

```bash
# Run diagnostic
node scripts/diagnose_supabase.js

# Should show:
# ✅ Connection successful
# ✅ uuid-ossp, vector extensions
# ✅ All tables exist
# ✅ RPC functions created

# Run bootstrap (should skip already-applied migrations)
npm run bootstrap

# Test the search function
node -e "
const { createClient } = require('@supabase/supabase-js');
const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_KEY);
supabase.rpc('match_company_documents', {
  query_embedding: Array(1536).fill(0),
  match_count: 1
}).then(r => console.log('✅ RPC works:', r.data));
"
```

### Still Stuck?

1. **Export the error logs:** Copy full error from bootstrap output
2. **Check Supabase logs:** Dashboard → Logs → Postgres Logs
3. **Try manual migration:** Apply SQL files one-by-one in SQL Editor
4. **Verify schema:** Compare your `company_documents` table to migration 001

### Reference: Function Signature

The correct signature for `match_company_documents`:

```sql
CREATE OR REPLACE FUNCTION match_company_documents(
  query_embedding vector(1536),     -- Must be vector(1536)
  filter_type text DEFAULT NULL,    -- text, not varchar
  match_threshold float DEFAULT 0.7,-- float, not double precision
  match_count int DEFAULT 5         -- int, not integer
)
RETURNS TABLE (
  id uuid,
  title text,
  content text,
  document_type text,
  voice_description text,
  signature_phrases jsonb,          -- jsonb, not json
  similarity float                   -- float, not double precision
)
```

Any mismatch will cause "return type mismatch" error.
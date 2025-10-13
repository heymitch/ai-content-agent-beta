# Export Database via Supabase SQL Editor

Since `pg_dump` can't connect from your machine, use this method instead:

## Step 1: Enable pg_dump in Supabase

Unfortunately, Supabase SQL Editor can't directly export to a file. We need to use a workaround.

## Best Solution: Use Supabase CLI

### Install Supabase CLI:

```bash
brew install supabase/tap/supabase
```

### Login to Supabase:

```bash
supabase login
```

### Link to your project:

```bash
supabase link --project-ref sdsracrbpwbdtaaghwqq
```

### Dump the database:

```bash
supabase db dump -f sql/001_full_database.sql --data-only=false
```

This will export:
- ✅ Schema (tables, indexes, functions)
- ✅ Data (all rows)
- ✅ Extensions (uuid-ossp, vector)

---

## Alternative: Manual SQL Export (If CLI doesn't work)

Go to: https://supabase.com/dashboard/project/sdsracrbpwbdtaaghwqq/sql/new

Run these queries one by one and save each output:

### 1. Export Extensions
```sql
SELECT 'CREATE EXTENSION IF NOT EXISTS "' || extname || '";'
FROM pg_extension
WHERE extname IN ('uuid-ossp', 'vector');
```

### 2. Export Table Schemas
```sql
SELECT
  'CREATE TABLE IF NOT EXISTS ' || schemaname || '.' || tablename || ' (...);'
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

### 3. Export Functions
```sql
SELECT pg_get_functiondef(oid) || ';'
FROM pg_proc
WHERE pronamespace = 'public'::regnamespace;
```

But honestly, **the Supabase CLI is WAY easier**. Try that first.

---

## Why pg_dump Fails

Your Mac can't resolve `db.sdsracrbpwbdtaaghwqq.supabase.co` - likely:
- Corporate VPN/firewall blocking
- DNS servers not propagating Supabase domains
- Network restrictions

The Supabase CLI uses the Management API instead of direct Postgres connection, so it should work even if pg_dump doesn't.

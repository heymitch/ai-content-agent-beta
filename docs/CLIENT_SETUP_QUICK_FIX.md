# Client Setup Quick Fix: "Tenant or user not found"

## Error Meaning

This error means the database connection string is incorrect or the database doesn't exist yet.

## Fix Steps

### Step 1: Get the Correct Connection String

Have the client go to their Supabase Dashboard:

1. **Navigate to:** Project Settings → Database → Connection String
2. **Select:** Connection pooling → Transaction mode
3. **Copy the string** - it looks like:
   ```
   postgresql://postgres.PROJECT:[PASSWORD]@aws-1-us-east-1.pooler.supabase.com:5432/postgres
   ```
4. **Replace `[PASSWORD]`** with their actual database password (NOT the API keys)

### Step 2: Find Their Database Password

If they don't have the password:

1. **Go to:** Project Settings → Database → Database password
2. **Click:** "Reset database password"
3. **Copy the new password** immediately (it won't be shown again)
4. **Update the connection string** with this password

### Step 3: Update .env File

Replace `SUPABASE_DB_URL` in their `.env`:

```bash
# OLD (wrong project):
SUPABASE_DB_URL="postgresql://postgres.thvterlpkksdwhfcpbcm:..."

# NEW (correct format):
SUPABASE_DB_URL="postgresql://postgres.PROJECT:ACTUAL_PASSWORD@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
```

**IMPORTANT:**
- `PROJECT` should match their Supabase project reference
- `ACTUAL_PASSWORD` is the database password (not anon/service_role keys)
- Use **Transaction mode** pooler (not Session mode)

### Step 4: Verify Connection

```bash
npm run diagnose
```

Should now show:
```
✅ Connection successful
📦 Checking extensions:
   ⚠️ No required extensions found
```

### Step 5: Enable Extensions (If Missing)

If diagnostic shows "No required extensions found":

1. **Go to:** Supabase Dashboard → SQL Editor
2. **Run this:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. **Verify:** Run `npm run diagnose` again

### Step 6: Run Bootstrap

```bash
npm run bootstrap
```

This will create all tables, functions, and set up the database schema.

## Common Mistakes

❌ **Using API keys instead of database password**
- `SUPABASE_KEY` = API key for REST API (starts with `eyJ...`)
- Database password = Different, used for PostgreSQL connection

❌ **Using wrong project reference**
- Each Supabase project has unique reference (e.g., `thvterlpkksdwhfcpbcm`)
- Must match the project you're setting up

❌ **Using Session mode instead of Transaction mode**
- Use: `@aws-1-us-east-1.pooler.supabase.com` (Transaction)
- Not: `@db.PROJECT.supabase.co` (Session - has connection limits)

## Verification Checklist

After fixing:

- [ ] `npm run diagnose` shows "Connection successful"
- [ ] Extensions `uuid-ossp` and `vector` are installed
- [ ] `npm run bootstrap` completes without errors
- [ ] Tables created: `company_documents`, `content_examples`, etc.
- [ ] RPC functions created: `match_company_documents`, etc.

## Still Not Working?

Check these:

1. **Network/Firewall:** Can the server reach `aws-1-us-east-1.pooler.supabase.com:5432`?
2. **Supabase Plan:** Free tier has connection limits (check project settings)
3. **Project Status:** Is the Supabase project active/not paused?

## Contact Info for Support

If client is still stuck, have them send:
1. Screenshot of Supabase Project Settings → Database → Connection String section
2. Error output from `npm run diagnose`
3. Their Supabase project URL (e.g., `https://PROJECT.supabase.co`)
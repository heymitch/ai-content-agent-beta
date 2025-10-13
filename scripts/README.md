# Database Setup Scripts

## For Template Maintainers

### Export Database

Export your current Supabase database to share with users:

```bash
./scripts/export_database.sh
```

This creates `sql/001_full_database.sql` with your exact database (schema + data + embeddings).

**What gets exported:**
- ✅ All tables with data
- ✅ All embeddings (vector columns)
- ✅ All functions/RPCs
- ✅ All RLS policies
- ✅ All indexes (including IVFFlat)
- ✅ Extensions (uuid-ossp, pgvector)

**What doesn't get exported:**
- ❌ auth/storage schemas (Supabase managed)
- ❌ Secrets/API keys

## For Template Users

### Automatic Setup (Replit)

When you fork this template on Replit:

1. Add `SUPABASE_DB_URL` to Replit Secrets:
   ```
   postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
   ```

2. Click "Run" - the database will automatically set up! 🎉

The `prestart` hook runs `scripts/bootstrap_database.js` which loads the entire database.

### Manual Setup (Local Development)

1. Create a `.env` file:
   ```bash
   SUPABASE_DB_URL=postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres
   ```

2. Run the bootstrap:
   ```bash
   npm install
   node scripts/bootstrap_database.js
   ```

### What You Get

After bootstrap completes, your Supabase database will have:

- **content_examples** - Proven high-performing content with embeddings
- **research** - Industry research and stats with semantic search
- **company_documents** - Brand voice guidelines and product docs
- **generated_posts** - Post history with analytics tracking
- **conversation_history** - Slack conversation memory
- **performance_analytics** - Content performance tracking

Plus all the functions for semantic search:
- `match_content_examples()` - Find similar content
- `match_research()` - Search research by topic
- `search_generated_posts()` - Search your post history
- `search_top_performing_posts()` - Find what works

### Troubleshooting

**"SUPABASE_DB_URL not set"**
- Add it to Replit Secrets or .env file
- Get it from: Supabase Dashboard → Project Settings → Database → Connection String (Direct)

**"could not translate host name"**
- Check your internet connection
- Verify the DB URL format is correct

**"permission denied for extension"**
- Enable extensions in Supabase SQL Editor first:
  ```sql
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

**"table already exists"**
- Bootstrap is idempotent - it won't re-apply migrations
- Check `_migrations` table to see what's been applied

## How It Works

1. **Export** (`export_database.sh`):
   - Runs `pg_dump` on your Supabase database
   - Strips ownership/privileges for portability
   - Saves to `sql/001_full_database.sql`

2. **Bootstrap** (`bootstrap_database.js`):
   - Runs on `npm start` (via prestart hook)
   - Connects to user's Supabase database
   - Applies SQL files in order (001_*.sql, 002_*.sql, etc.)
   - Tracks applied migrations in `_migrations` table
   - Safe to run multiple times (idempotent)

## Architecture

```
scripts/
├── export_database.sh       # Maintainer: export your DB
├── bootstrap_database.js    # User: auto-load DB on fork
└── README.md               # This file

sql/
└── 001_full_database.sql   # Your exact database snapshot
```

The bootstrap runs automatically when users fork on Replit, giving them your EXACT database with zero manual setup.

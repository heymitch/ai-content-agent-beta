# Database Export

## File: 001_full_database.sql

**Size:** 16MB (27,687 lines)
**Generated:** October 12, 2025
**Export Method:** Combined schema + REST API data export

### What's Included

**Schema (lines 1-654):**
- ✅ Extensions (uuid-ossp, pgvector)
- ✅ All table definitions
- ✅ All indexes (including IVFFlat for vector search)
- ✅ All RLS policies
- ✅ All functions/RPCs for semantic search
- ✅ All views

**Data (lines 655-27,687):**
- ✅ **741 content_examples** - Proven high-performing content with embeddings
- ✅ **14 conversation_history** - Example conversations
- ✅ **1 generated_post** - Sample generated content
- ✅ All embeddings (1536-dimension vectors)

### Tables Included

| Table | Rows | Purpose |
|-------|------|---------|
| content_examples | 741 | High-performing content with GPTZero scores & embeddings |
| research | 0 | Industry research (empty, ready for data) |
| company_documents | 0 | Brand voice & product docs (empty, ready for data) |
| generated_posts | 1 | Generated content history |
| conversation_history | 14 | Slack conversation memory |
| performance_analytics | 0 | Content performance tracking (empty, ready for data) |

### How Users Get This Database

When users fork the template on Replit:

1. They add `SUPABASE_DB_URL` to Replit Secrets
2. Click "Run"
3. `scripts/bootstrap_database.js` automatically runs
4. This SQL file loads into their Supabase
5. They get your EXACT database with all content & embeddings

### Semantic Search Functions

The export includes these RAG functions:

- `match_content_examples()` - Find similar content
- `match_research()` - Search research by topic
- `search_generated_posts()` - Search post history
- `search_top_performing_posts()` - Find what works
- `match_company_documents()` - Search brand/product docs

### Re-Exporting

To update this file with new data:

```bash
# Export data via REST API
python3 scripts/export_database.py

# Schema is already in setup/database_schema_v2.sql
# They get combined automatically
```

### File Size Notes

**16MB is fine for:**
- ✅ Git (under GitHub's 100MB limit)
- ✅ Replit (loads in ~2-3 seconds)
- ✅ Supabase import (processes in ~5-10 seconds)

The bulk of the size is:
- Embeddings (741 × 1536 floats = ~4.5MB)
- Content text (741 posts = ~8MB)
- SQL formatting (~3.5MB)

### Bootstrap Safety

The bootstrap script is idempotent:
- Uses `CREATE TABLE IF NOT EXISTS`
- Uses `INSERT ... ON CONFLICT DO NOTHING`
- Tracks applied migrations in `_migrations` table
- Safe to run multiple times

### What Users Get

After bootstrap, users have:
- 🎯 741 proven content examples to learn from
- 🔍 Semantic search to find similar content
- 📊 Empty tables ready for their data
- 🤖 All agent tools working out of the box
- 💾 Full conversation memory
- 📈 Performance tracking ready

**This is your exact production database, ready to clone.**

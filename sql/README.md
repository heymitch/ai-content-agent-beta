# SQL Migrations

This folder contains database migration files that are automatically applied when you run `npm start`.

## Current Migrations

**001_full_database.sql** - Complete bootstrap (creates all 9 tables, functions, policies)
**002_seed_data.sql** - Seed data with 700+ content examples and research
**003_add_metadata_column.sql** - Add metadata JSONB column to company_documents (for n8n compatibility)
**004_fix_title_nullable.sql** - Remove NOT NULL constraint from title column (for n8n vectorstore)

## How It Works

1. On `npm start`, `bootstrap_database.js` runs automatically (via prestart hook)
2. It reads all `*.sql` files from this directory in lexical order (001, 002, 003, etc.)
3. Each migration is tracked in the `_migrations` table
4. Already-applied migrations are skipped
5. Safe to run multiple times (idempotent)

## For Clients

Just set `SUPABASE_DB_URL` and run `npm start` - everything is created automatically.

The auto-migration system ensures all databases are kept up-to-date with the latest schema changes.

See `setup/CLIENT_DEPLOYMENT_GUIDE.md` for full documentation.

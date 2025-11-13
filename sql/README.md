# SQL Migrations

This folder contains database migration files that are automatically applied when you run `npm start`.

## Current Setup

**001_full_database.sql** - Complete bootstrap (creates all 9 tables, functions, policies)

All other migration files have been archived since 001 is now a complete bootstrap.

## For Clients

Just set `SUPABASE_DB_URL` and run `npm start` - everything is created automatically.

See `setup/CLIENT_DEPLOYMENT_GUIDE.md` for full documentation.

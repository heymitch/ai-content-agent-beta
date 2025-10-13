#!/bin/bash
#
# Export your Supabase database to sql/001_full_database.sql
#
# Usage:
#   ./scripts/export_database.sh
#
# Requirements:
#   - PostgreSQL client tools (pg_dump) installed
#   - SUPABASE_DB_URL set in environment or .env

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
SQL_DIR="$PROJECT_ROOT/sql"
OUTPUT_FILE="$SQL_DIR/001_full_database.sql"

# Load .env if exists
if [ -f "$PROJECT_ROOT/.env" ]; then
  export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Check for DB URL
if [ -z "$SUPABASE_DB_URL" ]; then
  echo "❌ Error: SUPABASE_DB_URL not set"
  echo ""
  echo "Set it in your .env file or run:"
  echo "  export SUPABASE_DB_URL='postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres'"
  echo ""
  exit 1
fi

# Create sql directory
mkdir -p "$SQL_DIR"

echo ""
echo "🔄 Exporting Supabase database..."
echo "📁 Output: $OUTPUT_FILE"
echo ""

# Run pg_dump
pg_dump "$SUPABASE_DB_URL" \
  --schema=public \
  --format=plain \
  --no-owner \
  --no-privileges \
  --file="$OUTPUT_FILE"

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Export complete!"
  echo ""
  echo "📊 File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
  echo "📝 Lines: $(wc -l < "$OUTPUT_FILE")"
  echo ""
  echo "What was exported:"
  echo "  ✅ All tables with data"
  echo "  ✅ All embeddings (vector columns)"
  echo "  ✅ All functions/RPCs"
  echo "  ✅ All RLS policies"
  echo "  ✅ All indexes (including IVFFlat)"
  echo "  ✅ Extensions (uuid-ossp, vector)"
  echo ""
  echo "Next step:"
  echo "  Commit sql/001_full_database.sql to the repo"
  echo "  Users will get this exact database when they fork"
  echo ""
else
  echo ""
  echo "❌ Export failed"
  exit 1
fi

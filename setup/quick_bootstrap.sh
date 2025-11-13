#!/bin/bash
# Quick Bootstrap - Uses the clean bootstrap_supabase.sql instead of huge 001_full_database.sql

set -e

# Get database URL from .env or argument
if [ -n "$1" ]; then
    DB_URL="$1"
elif [ -n "$SUPABASE_DB_URL" ]; then
    DB_URL="$SUPABASE_DB_URL"
else
    echo "❌ Error: No database URL provided"
    echo "Usage: ./quick_bootstrap.sh \"postgresql://...\""
    exit 1
fi

echo "🚀 Running clean bootstrap..."
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Use the clean bootstrap script (not the huge 001_full_database.sql)
if command -v psql &> /dev/null; then
    psql "$DB_URL" -f "$SCRIPT_DIR/bootstrap_supabase.sql"
else
    echo "⚠️  psql not found, trying with Node.js..."
    # Fallback for systems without psql
    node -e "
    const { Client } = require('pg');
    const fs = require('fs');
    const client = new Client({ connectionString: process.env.DB_URL });

    (async () => {
      await client.connect();
      const sql = fs.readFileSync('$SCRIPT_DIR/bootstrap_supabase.sql', 'utf8');
      await client.query(sql);
      await client.end();
      console.log('✅ Bootstrap complete!');
    })();
    " DB_URL="$DB_URL"
fi

echo ""
echo "✅ Bootstrap complete!"
echo ""
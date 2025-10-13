#!/usr/bin/env python3
"""
Export Supabase Database via REST API

Exports your entire Supabase database (schema + data) to sql/001_full_database.sql
Uses Supabase REST API instead of direct Postgres connection.

Requirements:
- SUPABASE_URL in environment
- SUPABASE_KEY (service role key) in environment

Usage:
    python scripts/export_database.py
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  # Service role key

# Output file
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
SQL_DIR = PROJECT_ROOT / 'sql'
OUTPUT_FILE = SQL_DIR / '001_full_database.sql'

# Tables to export (in order)
TABLES = [
    'content_examples',
    'research',
    'company_documents',
    'generated_posts',
    'conversation_history',
    'performance_analytics'
]

def check_env():
    """Check required environment variables"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print('\n❌ Error: Missing environment variables\n')
        print('Required:')
        print('  SUPABASE_URL     - Your project URL (https://xxx.supabase.co)')
        print('  SUPABASE_KEY     - Service role key (from API settings)')
        print('\nGet these from: https://supabase.com/dashboard/project/_/settings/api')
        print('')
        sys.exit(1)

def generate_schema_sql(table_name: str, supabase: Client) -> str:
    """
    Generate CREATE TABLE statement by introspecting table structure.
    Note: This is a simplified version. For full fidelity, use pg_dump.
    """
    # Get a sample row to infer columns
    try:
        result = supabase.table(table_name).select('*').limit(1).execute()
        if not result.data:
            print(f'  ⚠️  Table {table_name} is empty, skipping schema...')
            return ''

        # This is a placeholder - actual schema would need pg_dump or manual definition
        return f'-- Schema for {table_name} (placeholder - use actual schema)\n'
    except Exception as e:
        print(f'  ⚠️  Could not access {table_name}: {e}')
        return ''

def export_table_data(table_name: str, supabase: Client) -> str:
    """Export all data from a table as INSERT statements"""
    print(f'  📊 Exporting {table_name}...')

    sql_lines = []
    offset = 0
    batch_size = 1000
    total_rows = 0

    while True:
        try:
            # Fetch batch
            result = supabase.table(table_name) \
                .select('*') \
                .range(offset, offset + batch_size - 1) \
                .execute()

            if not result.data:
                break

            # Generate INSERT statements
            for row in result.data:
                columns = ', '.join(row.keys())

                # Format values
                values = []
                for val in row.values():
                    if val is None:
                        values.append('NULL')
                    elif isinstance(val, str):
                        # Escape single quotes
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    elif isinstance(val, (list, dict)):
                        # JSON columns
                        import json
                        escaped = json.dumps(val).replace("'", "''")
                        values.append(f"'{escaped}'::jsonb")
                    elif isinstance(val, bool):
                        values.append('TRUE' if val else 'FALSE')
                    else:
                        values.append(str(val))

                values_str = ', '.join(values)
                sql_lines.append(f'INSERT INTO {table_name} ({columns}) VALUES ({values_str}) ON CONFLICT DO NOTHING;')

            total_rows += len(result.data)

            # Check if we got less than batch_size (last batch)
            if len(result.data) < batch_size:
                break

            offset += batch_size

        except Exception as e:
            print(f'  ❌ Error exporting {table_name}: {e}')
            break

    print(f'  ✅ Exported {total_rows} rows from {table_name}')
    return '\n'.join(sql_lines) + '\n\n'

def main():
    print('\n🔄 Exporting Supabase database via REST API...')
    print(f'📁 Output: {OUTPUT_FILE}\n')

    # Check environment
    check_env()

    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Create output directory
    SQL_DIR.mkdir(exist_ok=True)

    # Start building SQL file
    sql_content = []

    # Header
    sql_content.append(f'''-- Supabase Database Export
-- Generated: {datetime.now().isoformat()}
-- Exported via REST API
--
-- WARNING: This export uses the REST API and may not include:
-- - Full schema details (constraints, indexes, triggers)
-- - RLS policies
-- - Functions/RPCs
--
-- For production use, export with: pg_dump or Supabase CLI
-- This is a data-only export for quick database replication.

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

''')

    # Note about schemas
    sql_content.append('''-- Schemas (add your actual CREATE TABLE statements here)
-- This export focuses on data. For full schema, use pg_dump.

''')

    # Export each table's data
    for table in TABLES:
        sql_content.append(f'\n-- Data for {table}\n')
        sql_content.append(export_table_data(table, supabase))

    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(''.join(sql_content))

    # Summary
    file_size = OUTPUT_FILE.stat().st_size / 1024  # KB
    line_count = len(''.join(sql_content).split('\n'))

    print('\n✅ Export complete!\n')
    print(f'📊 File size: {file_size:.1f} KB')
    print(f'📝 Lines: {line_count:,}')
    print(f'📁 Location: {OUTPUT_FILE}\n')
    print('⚠️  Note: This is a DATA-ONLY export via REST API.')
    print('   For full schema (indexes, RLS, functions), you need:')
    print('   - pg_dump (requires network access to Postgres)')
    print('   - OR manually copy schema from database_schema_v2.sql\n')
    print('💡 Recommended: Combine this data export with database_schema_v2.sql\n')

if __name__ == '__main__':
    main()

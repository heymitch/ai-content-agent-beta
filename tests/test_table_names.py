#!/usr/bin/env python3
"""Check for alternative table names or schemas"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_table_variants():
    """Try different table name variations"""

    print("=" * 80)
    print("CHECKING FOR ALTERNATIVE TABLE NAMES")
    print("=" * 80)

    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    # Try different variations
    table_variations = [
        'company_documents',
        'companydocuments',
        'company-documents',
        'documents',
        'company_docs',
        'user_documents',
        'uploaded_documents',
        'rag_documents',
    ]

    print("\n1. Testing different table name variations:\n")
    for table_name in table_variations:
        try:
            result = supabase.table(table_name).select('id, title').limit(1).execute()
            if result.data:
                print(f"   ✅ {table_name}: {len(result.data)} rows found")
            else:
                print(f"   ⚪ {table_name}: exists but empty (0 rows)")
        except Exception as e:
            error_msg = str(e)
            if 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
                print(f"   ❌ {table_name}: table does not exist")
            else:
                print(f"   ⚠️  {table_name}: error - {error_msg[:50]}")

    print("\n2. Checking if documents were inserted with different column names:\n")
    try:
        # Get full structure of company_documents if it exists
        result = supabase.table('company_documents').select('*').limit(1).execute()
        if result.data:
            print(f"   Columns in first row: {list(result.data[0].keys())}")
        else:
            print(f"   Table exists but is empty - no column structure to show")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n3. Checking PostgREST API directly for table list:\n")
    print(f"   Your Supabase URL: {os.getenv('SUPABASE_URL')}")
    print(f"   Try visiting: {os.getenv('SUPABASE_URL')}/rest/v1/")
    print(f"   (in browser with auth header to see available tables)")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_table_variants()

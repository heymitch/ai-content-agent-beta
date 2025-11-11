#!/usr/bin/env python3
"""Test if RLS (Row Level Security) is blocking queries"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def test_rls():
    """Check if RLS is blocking company_documents queries"""

    print("=" * 80)
    print("TESTING ROW LEVEL SECURITY (RLS)")
    print("=" * 80)

    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )

    print("\n1. Testing with service role key (bypasses RLS):")
    print(f"   Current key starts with: {os.getenv('SUPABASE_KEY')[:20]}...")

    # Check what type of key we're using
    key = os.getenv('SUPABASE_KEY')
    if key and key.startswith('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'):
        print(f"   ℹ️  Using JWT token (anon or service_role)")
        # Decode to check role
        import base64
        import json
        try:
            # JWT format: header.payload.signature
            parts = key.split('.')
            if len(parts) == 3:
                # Decode payload (add padding if needed)
                payload = parts[1]
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                token_data = json.loads(decoded)
                role = token_data.get('role', 'unknown')
                print(f"   Token role: {role}")

                if role == 'anon':
                    print(f"   ⚠️  WARNING: Using ANON key - RLS will apply!")
                    print(f"   Use SERVICE_ROLE key to bypass RLS")
                elif role == 'service_role':
                    print(f"   ✅ Using SERVICE_ROLE key - RLS bypassed")
        except:
            print(f"   Could not decode token")

    print("\n2. Checking all tables for diagnostics:")
    try:
        # Try to list tables (might not work with anon key)
        tables_to_check = [
            'company_documents',
            'generated_posts',
            'content_examples'
        ]

        for table_name in tables_to_check:
            try:
                result = supabase.table(table_name).select('id').limit(1).execute()
                print(f"   {table_name}: {len(result.data)} rows accessible")
            except Exception as e:
                print(f"   {table_name}: ❌ Error - {str(e)[:50]}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n3. Trying to check table info directly:")
    try:
        # Try getting count without RLS
        result = supabase.table('company_documents').select('id', count='exact').execute()
        print(f"   Total count in company_documents: {result.count}")
    except Exception as e:
        print(f"   ❌ Error getting count: {e}")

    print("\n" + "=" * 80)
    print("SOLUTION:")
    print("If RLS is the issue, either:")
    print("1. Use SUPABASE_SERVICE_ROLE_KEY instead of SUPABASE_KEY")
    print("2. Disable RLS on company_documents table")
    print("3. Add RLS policy that allows service_role to read all rows")
    print("=" * 80)

if __name__ == "__main__":
    test_rls()

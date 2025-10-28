#!/usr/bin/env python3
"""
Simple Airtable configuration test
Run this in your Replit to verify Airtable is working

Usage in Replit:
    python tests/test_airtable_simple.py
"""

import sys
import os

# Add parent directory to path to import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_airtable():
    import os
    print("🔍 Testing Airtable Configuration for LinkedIn Post\n")

    # Check env vars
    token = os.getenv('AIRTABLE_ACCESS_TOKEN')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_TABLE_NAME')

    print("1. Environment Variables:")
    print(f"   TOKEN: {'✅ Set (' + token[:8] + '...)' if token else '❌ Missing'}")
    print(f"   BASE:  {'✅ ' + base_id if base_id else '❌ Missing'}")
    print(f"   TABLE: {'✅ ' + table_name if table_name else '❌ Missing'}")

    if not all([token, base_id, table_name]):
        print("\n❌ Missing environment variables!")
        print("   Set these in Replit Secrets or .env file")
        return False

    # Format check
    print("\n2. Format Check:")
    base_ok = base_id.startswith('app')
    table_ok = table_name.startswith('tbl')
    print(f"   Base ID: {'✅ Valid (app...)' if base_ok else '❌ Should start with app'}")
    print(f"   Table:   {'✅ Valid (tbl...)' if table_ok else '❌ Should start with tbl'}")

    if not (base_ok and table_ok):
        print("\n❌ Format error!")
        return False

    # Test API connection
    print("\n3. Testing Airtable API Connection...")
    try:
        from integrations.airtable_client import AirtableContentCalendar

        airtable = AirtableContentCalendar()
        print(f"   ✅ Connected to Airtable")
        print(f"   Base: {airtable.base_id}")
        print(f"   Table: {airtable.table_name}")

        # Test creating a LinkedIn post
        print("\n4. Testing LinkedIn Post Creation...")
        test_content = "This is a test post from the Airtable diagnostic script. You can delete this."

        result = airtable.create_content_record(
            content=test_content,
            platform='linkedin',
            post_hook='Test Post - Delete Me',
            status='Draft'
        )

        if result.get('success'):
            print(f"   ✅ Successfully created test record!")
            print(f"   Record ID: {result.get('record_id')}")
            print(f"   URL: {result.get('url')}")
            print(f"\n   🗑️  You can delete this test record in Airtable")
            return True
        else:
            print(f"   ❌ Failed to create record")
            print(f"   Error: {result.get('error')}")

            # Diagnose common errors
            error_str = str(result.get('error', '')).lower()
            print(f"\n   💡 Diagnosis:")

            if 'platform' in error_str or 'linkedin' in error_str:
                print(f"   - Platform field issue:")
                print(f"     • Open your Airtable base")
                print(f"     • Find the 'Platform' column")
                print(f"     • Click dropdown → Customize field type")
                print(f"     • Make sure 'Linkedin' is in the options list")

            if 'status' in error_str or 'draft' in error_str:
                print(f"   - Status field issue:")
                print(f"     • Make sure 'Draft' is an option in Status field")

            if 'permission' in error_str or 'forbidden' in error_str:
                print(f"   - Permission issue:")
                print(f"     • Your PAT needs write access to this base")
                print(f"     • Check token permissions at airtable.com/create/tokens")

            if 'not found' in error_str:
                print(f"   - Not found issue:")
                print(f"     • Double-check your Base ID and Table Name")
                print(f"     • Base ID should be from the URL: airtable.com/app.../tbl...")

            return False

    except ValueError as e:
        print(f"   ❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    success = test_airtable()
    print("="*60)
    if success:
        print("\n✅ AIRTABLE IS WORKING!")
        print("Your client install can save LinkedIn posts to Airtable.\n")
    else:
        print("\n❌ AIRTABLE NEEDS FIXING")
        print("See errors above for what needs to be corrected.\n")

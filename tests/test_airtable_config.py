"""
Diagnostic script to test Airtable configuration
Run this to verify your PAT, Base ID, and Table Name are correct
"""
import os
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv()

def test_airtable_config():
    print("🔍 Testing Airtable Configuration\n")

    # Check environment variables
    api_key = os.getenv('AIRTABLE_ACCESS_TOKEN')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_TABLE_NAME')

    print("1. Environment Variables:")
    print(f"   AIRTABLE_ACCESS_TOKEN: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"   AIRTABLE_BASE_ID: {base_id if base_id else '❌ Missing'}")
    print(f"   AIRTABLE_TABLE_NAME: {table_name if table_name else '❌ Missing'}")
    print()

    if not all([api_key, base_id, table_name]):
        print("❌ Missing required environment variables")
        return False

    # Validate format
    print("2. Format Validation:")
    base_valid = base_id.startswith('app')
    table_valid = table_name.startswith('tbl')
    print(f"   Base ID format: {'✅ Valid (starts with app)' if base_valid else '❌ Invalid (should start with app)'}")
    print(f"   Table Name format: {'✅ Valid (starts with tbl)' if table_valid else '❌ Invalid (should start with tbl)'}")
    print()

    # Test connection
    print("3. Testing Connection:")
    try:
        api = Api(api_key)
        table = api.table(base_id, table_name)

        # Try to fetch schema
        print("   ✅ Successfully connected to Airtable")

        # Try to list records (limit 1 to minimize API usage)
        records = table.all(max_records=1)
        print(f"   ✅ Can read records (found {len(records)} record{'s' if len(records) != 1 else ''})")

        # Check field names
        if records:
            fields = list(records[0]['fields'].keys())
            print(f"\n4. Available Fields in Table:")
            for field in fields:
                print(f"   - {field}")

            # Check for required fields
            print(f"\n5. Required Field Check:")
            required_fields = ['Body Content', 'Platform', 'Status']
            for field in required_fields:
                if field in fields:
                    print(f"   ✅ {field}")
                else:
                    print(f"   ❌ {field} (missing)")

            # Check Platform options
            if 'Platform' in records[0]['fields']:
                platform_value = records[0]['fields']['Platform']
                print(f"\n6. Platform Field Example:")
                print(f"   Value: {platform_value}")
                print(f"   Type: {type(platform_value)}")

        # Try to create a test record
        print(f"\n7. Testing Write Permissions:")
        test_fields = {
            'Body Content': 'TEST - Delete this record',
            'Platform': ['Linkedin'],
            'Status': 'Draft'
        }

        try:
            test_record = table.create(test_fields)
            print(f"   ✅ Can create records (created {test_record['id']})")

            # Clean up test record
            table.delete(test_record['id'])
            print(f"   ✅ Can delete records (cleaned up test)")

            return True

        except Exception as e:
            print(f"   ❌ Cannot create records: {str(e)}")
            print(f"\n   Common issues:")
            print(f"   - PAT doesn't have write permission")
            print(f"   - Platform field doesn't have the option you're trying to use")
            print(f"   - Status field doesn't have 'Draft' option")
            return False

    except Exception as e:
        print(f"   ❌ Connection failed: {str(e)}")
        print(f"\n   Common issues:")
        print(f"   - Incorrect Base ID (should be app...)")
        print(f"   - Incorrect Table Name (should be tbl...)")
        print(f"   - PAT doesn't have access to this base")
        print(f"   - PAT expired or revoked")
        return False

if __name__ == "__main__":
    success = test_airtable_config()
    print(f"\n{'='*50}")
    if success:
        print("✅ Airtable configuration is working correctly!")
    else:
        print("❌ Airtable configuration has issues - see errors above")
    print('='*50)

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Try direct table query (should respect RLS)
result = supabase.table('content_examples').select('platform, content').limit(5).execute()

print(f"Direct table query results: {len(result.data)} rows")
print(f"Data: {result.data}")

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Create a dummy embedding (all zeros)
dummy_embedding = [0.0] * 1536

print("Test 1: RPC with threshold=0 (should match everything)")
result = supabase.rpc(
    'match_content_examples',
    {
        'query_embedding': dummy_embedding,
        'filter_platform': None,
        'match_threshold': 0.0,  # Match everything
        'match_count': 10
    }
).execute()
print(f"Results: {len(result.data)} matches")
print(f"Data: {result.data[:2] if result.data else 'None'}")

print("\nTest 2: Direct table count")
count = supabase.table('content_examples').select('id', count='exact').execute()
print(f"Total rows with API key: {count.count}")

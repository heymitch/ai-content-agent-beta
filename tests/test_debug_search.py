from tools.search_tools import search_content_examples
from openai import OpenAI
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Generate embedding
query = "writing tips advice"
response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=query
)
query_embedding = response.data[0].embedding

print(f"Query: {query}")
print(f"Embedding length: {len(query_embedding)}")
print(f"First 5 values: {query_embedding[:5]}")

# Call RPC directly
result = supabase.rpc(
    'match_content_examples',
    {
        'query_embedding': query_embedding,
        'filter_platform': None,
        'match_threshold': 0.7,
        'match_count': 10
    }
).execute()

print(f"\nRPC Result:")
print(f"Number of matches: {len(result.data)}")
print(f"Raw data: {result.data}")

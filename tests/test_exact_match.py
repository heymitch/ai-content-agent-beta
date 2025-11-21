#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

load_dotenv(override=True)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Get a real document's content
docs = supabase.table('company_documents').select('id, title, content, embedding').limit(1).execute()
doc_content = docs.data[0]['content']
doc_title = docs.data[0]['title']
stored_embedding_str = docs.data[0]['embedding']

print(f"Document: '{doc_title}'")
print(f"Content: '{doc_content}'")
print(f"\nSearching for the EXACT content...")

# Generate embedding for the exact same content
response = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=doc_content
)
query_embedding = response.data[0].embedding

print(f"Query embedding dimensions: {len(query_embedding)}")

# Parse stored embedding
import json
stored_embedding = json.loads(stored_embedding_str)
print(f"Stored embedding dimensions: {len(stored_embedding)}")

# Calculate cosine similarity manually
import numpy as np
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

manual_similarity = cosine_similarity(np.array(query_embedding), np.array(stored_embedding))
print(f"\nManual cosine similarity: {manual_similarity:.4f}")

# Search via RPC
result = supabase.rpc(
    'match_company_documents',
    {
        'query_embedding': query_embedding,
        'filter_type': None,
        'match_threshold': 0.3,
        'match_count': 5
    }
).execute()

print(f"\nRPC Results:")
for match in result.data:
    print(f"  - {match['title']}: similarity {match['similarity']:.4f}")

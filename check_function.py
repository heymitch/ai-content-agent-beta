import os
from supabase import create_client

supabase = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_ROLE_KEY']
)

# Query pg_catalog to see the actual function signature
query = """
SELECT 
    p.proname as function_name,
    pg_catalog.pg_get_function_result(p.oid) as return_type,
    pg_catalog.pg_get_function_arguments(p.oid) as arguments
FROM pg_catalog.pg_proc p
WHERE p.proname = 'match_content_examples';
"""

result = supabase.rpc('exec_sql', {'query': query}).execute()
print("Current function signature:")
print(result.data)

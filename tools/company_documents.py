"""
Company Documents RAG Tool
Search user-uploaded documents for context enrichment

Use for:
- Customer case studies
- Product documentation
- Testimonials and reviews
- Internal documentation
- Project reports

NOT for:
- Brand voice/guidelines (use .claude/CLAUDE.md)
- Style/format examples (use content_examples database)
- Past generated posts (use search_past_posts)
"""

import json
import os
from typing import Optional
from dotenv import load_dotenv

# Force override environment variables with .env file values
# (VSCode/IDE may set stale SUPABASE vars from other projects)
load_dotenv(override=True)


def search_company_documents(
    query: str,
    match_count: int = 3,
    document_type: Optional[str] = None
) -> str:
    """
    Search user-uploaded company documents using RAG (vector similarity)

    Args:
        query: Search query (e.g., "AI agents case studies", "product ROI metrics")
        match_count: Number of results to return (default 3)
        document_type: Filter by type ('case_study', 'testimonial', 'product_doc', 'internal_doc', etc.)

    Returns:
        JSON string with matched documents:
        {
            "success": true,
            "query": "...",
            "matches": [
                {
                    "title": "...",
                    "content": "...",
                    "document_type": "case_study",
                    "similarity": 0.85
                }
            ],
            "count": 3
        }

    Example:
        # Search for case studies about AI agents
        results = search_company_documents("AI agents customer success", match_count=5, document_type="case_study")

        # Search for any product documentation
        results = search_company_documents("new feature pricing", document_type="product_doc")

        # Broad search across all docs
        results = search_company_documents("remote work productivity")
    """
    try:
        from openai import OpenAI
        from supabase import create_client

        # Initialize clients
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        # Debug: Log which Supabase project we're connecting to
        print(f"🔗 Connecting to Supabase: {supabase_url}")
        print(f"   Key prefix: {supabase_key[:20] if supabase_key else 'MISSING'}...")

        supabase = create_client(supabase_url, supabase_key)

        # Generate embedding for query
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding

        # Convert to JSON string format to match how embeddings are stored in DB
        # (DB stores embeddings as JSON strings, not native vectors)
        import json as json_lib
        query_embedding_str = json_lib.dumps(query_embedding)

        # Search company_documents table using RPC function
        # Convert "all" to None for no filtering
        filter_value = None if document_type == "all" else document_type

        print(f"🔍 Searching company_documents:")
        print(f"   Query: {query}")
        print(f"   Filter: {filter_value}")
        print(f"   Threshold: 0.5")
        print(f"   Match count requested: {match_count}")
        print(f"   Embedding dimensions: {len(query_embedding)}")

        result = supabase.rpc(
            'match_company_documents',
            {
                'query_embedding': query_embedding,
                'filter_type': filter_value,
                'match_threshold': 0.5,  # 50% similarity threshold (lowered for broader matches)
                'match_count': match_count
            }
        ).execute()

        print(f"   ✅ RPC call completed")
        print(f"   Results: {len(result.data)} matches")
        if len(result.data) > 0:
            print(f"   Top match: {result.data[0].get('title')} (similarity: {result.data[0].get('similarity', 0):.3f})")
        print(f"   Raw result.data: {result.data}")

        # Debug: Try direct table query to see if ANY documents exist
        try:
            direct_query = supabase.table('company_documents').select('id, title, status, searchable').limit(5).execute()
            print(f"   Direct table query found: {len(direct_query.data)} documents")
            if direct_query.data:
                for doc in direct_query.data:
                    print(f"      - {doc}")
        except Exception as direct_err:
            print(f"   Direct query error: {direct_err}")
        if result.data:
            for item in result.data:
                print(f"   - {item.get('title')} (similarity: {item.get('similarity', 0):.2f})")

        # Format results
        matches = []
        for item in result.data:
            match_data = {
                'title': item.get('title', 'Untitled Document'),
                'content': item.get('content', ''),
                'document_type': item.get('document_type', 'unknown'),
                'similarity': round(item.get('similarity', 0), 2)
            }

            # Add optional fields if present
            if item.get('voice_description'):
                match_data['voice_description'] = item['voice_description']
            if item.get('signature_phrases'):
                match_data['signature_phrases'] = item['signature_phrases']

            matches.append(match_data)

        return json.dumps({
            'success': True,
            'query': query,
            'document_type_filter': document_type,
            'matches': matches,
            'count': len(matches)
        }, indent=2)

    except Exception as e:
        # Return error details for debugging
        return json.dumps({
            'success': False,
            'error': str(e),
            'query': query,
            'document_type_filter': document_type
        }, indent=2)


# Alias for backward compatibility
search_knowledge_base = search_company_documents

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

load_dotenv()


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
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Generate embedding for query
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding

        # Search company_documents table using RPC function
        # Convert "all" to None for no filtering
        filter_value = None if document_type == "all" else document_type

        result = supabase.rpc(
            'match_company_documents',
            {
                'query_embedding': query_embedding,
                'filter_type': filter_value,
                'match_threshold': 0.5,  # 50% similarity threshold (lowered for broader matches)
                'match_count': match_count
            }
        ).execute()

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

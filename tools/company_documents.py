"""
Company Documents RAG Tool
Search user-uploaded documents for context enrichment

Use for:
- Customer case studies
- Product documentation
- Testimonials and reviews
- Internal documentation
- Project reports
- Meeting transcripts (created_at = meeting date)

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
    document_type: Optional[str] = None,
    sort_by_date: bool = False
) -> str:
    """
    Search user-uploaded company documents using HYBRID search (keyword + semantic)

    Args:
        query: Search query (e.g., "Joel", "AI agents case studies", "product ROI metrics")
        match_count: Number of results to return (default 3)
        document_type: Filter by type ('case_study', 'testimonial', 'product_doc', 'internal_doc', 'transcript', etc.)
        sort_by_date: If True, sort by created_at DESC (most recent first) - useful for finding "last meeting"

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
                    "created_at": "2025-01-27T10:30:00",
                    "similarity": 0.85,
                    "match_type": "keyword" or "semantic"
                }
            ],
            "count": 3
        }

    Search Strategy:
        1. Extract keywords from query (single words, names)
        2. Try keyword matching on title first (fast, exact)
        3. Fall back to semantic search on content (slower, fuzzy)
        4. Combine and dedupe results
        5. If sort_by_date=True, sort by created_at DESC

    Example:
        # Simple name search
        results = search_company_documents("Joel")  # Finds "Joel lift-off OB"

        # Topic search
        results = search_company_documents("AI agents customer success", match_count=5)

        # Find last meeting transcript
        results = search_company_documents("", document_type="transcript", match_count=1, sort_by_date=True)
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

        # STRATEGY 1: Keyword matching on title
        # Extract simple keywords (remove common words)
        import re
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'about', 'meeting', 'notes', 'insights',
                     'takeaways', 'discussion', 'document', 'file'}

        # Split query into words, keep only meaningful keywords
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Limit to 3 most relevant keywords to reduce sequential HTTP requests
        # Prioritize: proper nouns (capitalized in original), then longer words (more specific)
        original_words = re.findall(r'\b\w+\b', query)

        def keyword_relevance(kw):
            # Find original casing
            for orig in original_words:
                if orig.lower() == kw:
                    # Capitalized words (likely names/proper nouns) get highest priority
                    if orig[0].isupper():
                        return (0, -len(kw))  # 0 = highest priority
            # Longer words are more specific/relevant
            return (1, -len(kw))

        keywords = sorted(keywords, key=keyword_relevance)[:3]

        print(f"🔍 HYBRID SEARCH for: '{query}'")
        print(f"   Top 3 keywords (from {len(words)} words): {keywords}")

        keyword_matches = []
        seen_ids = set()

        # Try keyword search on title for each keyword
        for keyword in keywords:
            try:
                # Use ilike for case-insensitive partial match
                kw_query = supabase.table('company_documents')\
                    .select('id, title, content, document_type, voice_description, signature_phrases, created_at')\
                    .eq('status', 'active')\
                    .eq('searchable', True)\
                    .ilike('title', f'%{keyword}%')

                if document_type and document_type != "all":
                    kw_query = kw_query.eq('document_type', document_type)

                # Sort by date if requested (for finding "last meeting")
                if sort_by_date:
                    kw_query = kw_query.order('created_at', desc=True)

                kw_query = kw_query.limit(match_count)

                kw_result = kw_query.execute()

                if kw_result.data:
                    print(f"   ✅ Keyword '{keyword}' matched {len(kw_result.data)} documents")
                    for doc in kw_result.data:
                        if doc['id'] not in seen_ids:
                            seen_ids.add(doc['id'])
                            keyword_matches.append({
                                **doc,
                                'similarity': 0.95,  # High score for keyword match
                                'match_type': 'keyword'
                            })
            except Exception as kw_err:
                print(f"   ⚠️ Keyword search error: {kw_err}")

        print(f"   Found {len(keyword_matches)} keyword matches")

        # STRATEGY 2: Semantic search (only if needed)
        semantic_matches = []
        remaining_slots = match_count - len(keyword_matches)

        if remaining_slots > 0:
            print(f"   Running semantic search for {remaining_slots} more matches...")

            # Generate embedding for query
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_embedding = response.data[0].embedding

            # Search company_documents table using RPC function
            filter_value = None if document_type == "all" else document_type

            result = supabase.rpc(
                'match_company_documents',
                {
                    'query_embedding': query_embedding,
                    'filter_type': filter_value,
                    'match_threshold': 0.3,  # LOWERED to 30% for broader semantic matches
                    'match_count': remaining_slots * 2  # Get more, then filter dupes
                }
            ).execute()

            print(f"   Semantic search returned {len(result.data)} matches")

            for item in result.data:
                if item['id'] not in seen_ids:
                    seen_ids.add(item['id'])
                    semantic_matches.append({
                        **item,
                        'match_type': 'semantic'
                    })
                    if len(semantic_matches) >= remaining_slots:
                        break

        # Combine results (keyword matches first, then semantic)
        all_matches = keyword_matches + semantic_matches

        print(f"   Total matches: {len(all_matches)} ({len(keyword_matches)} keyword + {len(semantic_matches)} semantic)")

        # Debug: Show what we found
        if all_matches:
            for match in all_matches[:3]:
                print(f"      - {match.get('title')} ({match.get('match_type')}, sim: {match.get('similarity', 0):.2f})")
        else:
            print(f"   ⚠️ No matches found for query: '{query}'")

        # Sort by date if requested (after combining keyword + semantic results)
        if sort_by_date:
            all_matches.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        # Format results from combined matches
        matches = []
        for item in all_matches:
            match_data = {
                'title': item.get('title', 'Untitled Document'),
                'content': item.get('content', ''),
                'document_type': item.get('document_type', 'unknown'),
                'created_at': item.get('created_at'),  # Include meeting date
                'similarity': round(item.get('similarity', 0), 2),
                'match_type': item.get('match_type', 'unknown')
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

"""
Search and research tools
"""
import json
import logging
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily API

    Args:
        query: Search query
        max_results: Maximum number of results (default 5)

    Returns:
        JSON string with search results
    """
    try:
        from tavily import TavilyClient

        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        # Perform search
        results = tavily.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"
        )

        # Format results
        formatted = []
        for result in results.get('results', []):
            formatted.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'content': result.get('content', '')[:500],  # First 500 chars
                'score': result.get('score', 0)
            })

        return json.dumps({
            'success': True,
            'query': query,
            'results': formatted,
            'count': len(formatted)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            'error': str(e),
            'query': query
        })


def perplexity_search(query: str, search_focus: str = "internet") -> str:
    """
    Enhanced research using Perplexity API with citations

    Best for: Deep research questions, fact-checking, finding recent data with sources

    Args:
        query: Research query (be specific for best results)
        search_focus: Focus area - "internet" (default), "news", "academic", "writing", "wolfram", "youtube", "reddit"

    Returns:
        JSON string with researched answer and citations
    """
    try:
        from openai import OpenAI

        # Initialize Perplexity client (OpenAI-compatible API)
        perplexity = OpenAI(
            api_key=os.getenv('PERPLEXITY_API_KEY'),
            base_url="https://api.perplexity.ai"
        )

        # Map search focus to model
        # sonar-pro: Most capable, best for complex queries
        # sonar: Balanced performance and cost
        model = "sonar-pro" if search_focus in ["academic", "research", "wolfram"] else "sonar"

        # Make request with search domain routing
        messages = [
            {
                "role": "system",
                "content": f"You are a research assistant. Focus on {search_focus} sources. Provide detailed, well-cited answers with specific data points and dates."
            },
            {
                "role": "user",
                "content": query
            }
        ]

        # Check for API key before making request
        api_key = os.getenv('PERPLEXITY_API_KEY')
        if not api_key:
            logger.error("PERPLEXITY_API_KEY not found in environment")
            return json.dumps({
                'error': 'PERPLEXITY_API_KEY not configured',
                'query': query,
                'note': 'Add PERPLEXITY_API_KEY to your environment variables'
            })

        response = perplexity.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.2  # Lower temp for factual accuracy
            # Note: citations are returned automatically in response
        )

        # Extract answer and citations (citations come automatically)
        answer = response.choices[0].message.content
        citations = getattr(response, 'citations', [])
        search_results = getattr(response, 'search_results', [])

        logger.info(f"Perplexity search success: query='{query[:50]}...', model={model}, citations={len(citations)}")

        return json.dumps({
            'success': True,
            'query': query,
            'answer': answer,
            'citations': citations,
            'search_results': search_results,
            'model': model,
            'search_focus': search_focus
        }, indent=2)

    except Exception as e:
        logger.error(f"Perplexity API error: {type(e).__name__}: {e}")
        return json.dumps({
            'error': str(e),
            'error_type': type(e).__name__,
            'query': query,
            'note': 'Check PERPLEXITY_API_KEY and API status'
        })


def search_knowledge_base(query: str, match_count: int = 5, document_type: str = None) -> str:
    """
    Search company documents using RAG (vector similarity)

    NEW: Searches company_documents table (brand guides, case studies, product docs)

    Args:
        query: Search query
        match_count: Number of results (default 5)
        document_type: Filter by type ('brand_guide', 'case_study', 'product_doc', etc.)

    Returns:
        JSON string with matched content
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

        # Search company_documents (V2 schema)
        result = supabase.rpc(
            'match_company_documents',
            {
                'query_embedding': query_embedding,
                'filter_type': document_type,
                'match_threshold': 0.3,
                'match_count': match_count
            }
        ).execute()

        # Format results
        matches = []
        for item in result.data:
            match_data = {
                'title': item['title'],
                'content': item['content'],
                'document_type': item['document_type'],
                'similarity': item['similarity']
            }

            # Add voice fields if it's a brand guide
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
        return json.dumps({
            'error': str(e),
            'query': query
        })


def analyze_past_content(platform: str = None, limit: int = 10) -> str:
    """
    Analyze high-performing content examples for patterns

    NEW: Searches content_examples table (proven 90-100% human posts)

    Args:
        platform: Filter by platform (optional)
        limit: Number of posts to analyze (default 10)

    Returns:
        JSON string with top performing content
    """
    try:
        from supabase import create_client

        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Query content_examples (V2 schema)
        query = supabase.table('content_examples').select('*').eq(
            'status', 'approved'
        ).order('engagement_rate', desc=True).limit(limit)

        if platform:
            query = query.eq('platform', platform)

        result = query.execute()

        # Format results
        content_list = []
        for item in result.data:
            content_list.append({
                'platform': item['platform'],
                'creator': item.get('creator', 'Unknown'),
                'content': item['content'][:300],  # First 300 chars
                'human_score': item.get('human_score'),
                'engagement_rate': item.get('engagement_rate'),
                'content_type': item.get('content_type'),
                'hook': item.get('hook_line', ''),
                'tags': item.get('tags', [])
            })

        return json.dumps({
            'success': True,
            'platform': platform or 'all',
            'content': content_list,
            'count': len(content_list)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            'error': str(e)
        })


def search_content_examples(query: str, platform: str = None, match_count: int = 5) -> str:
    """
    Search proven content examples using RAG

    NEW: Semantic search across content_examples table

    Args:
        query: Search query (topic or content style)
        platform: Filter by platform (optional)
        match_count: Number of results (default 5)

    Returns:
        JSON string with matched content examples
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

        # Search content_examples
        result = supabase.rpc(
            'match_content_examples',
            {
                'query_embedding': query_embedding,
                'filter_platform': platform,
                'match_threshold': 0.3,
                'match_count': match_count
            }
        ).execute()

        # Format results
        matches = []
        for item in result.data:
            matches.append({
                'platform': item['platform'],
                'content': item['content'],
                'human_score': item.get('human_score'),
                'engagement_rate': item.get('engagement_rate'),
                'content_type': item.get('content_type'),
                'creator': item.get('creator'),
                'hook': item.get('hook_line'),
                'tags': item.get('tags', []),
                'similarity': item['similarity']
            })

        return json.dumps({
            'success': True,
            'query': query,
            'platform_filter': platform,
            'matches': matches,
            'count': len(matches)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            'error': str(e),
            'query': query
        })


def search_research(query: str, min_credibility: int = 5, match_count: int = 5) -> str:
    """
    Search research database for proof points

    NEW: Searches research table (Tavily digests, industry reports)

    Args:
        query: Search query
        min_credibility: Minimum credibility score 1-10 (default 5)
        match_count: Number of results (default 5)

    Returns:
        JSON string with matched research
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

        # Search research
        result = supabase.rpc(
            'match_research',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.3,
                'match_count': match_count,
                'min_credibility': min_credibility
            }
        ).execute()

        # Format results
        matches = []
        for item in result.data:
            matches.append({
                'topic': item['topic'],
                'summary': item['summary'],
                'key_stats': item.get('key_stats', []),
                'sources': item.get('source_names', []),
                'credibility': item['credibility_score'],
                'research_date': item['research_date'],
                'similarity': item['similarity']
            })

        return json.dumps({
            'success': True,
            'query': query,
            'min_credibility': min_credibility,
            'matches': matches,
            'count': len(matches)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            'error': str(e),
            'query': query
        })

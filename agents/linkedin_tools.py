"""
Intelligent tools for LinkedIn content creation
Tools that enable autonomous research, validation, and optimization
"""
import os
from typing import Dict, List, Any
from tavily import TavilyClient


def web_search_linkedin_examples(query: str, max_results: int = 5) -> str:
    """
    Search web for LinkedIn post examples and best practices

    Args:
        query: Search query (e.g., "best LinkedIn posts about AI")
        max_results: Number of results to return

    Returns:
        Formatted search results with URLs and snippets
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        # Search specifically for LinkedIn content examples
        search_query = f"site:linkedin.com/posts {query} OR {query} LinkedIn post examples"

        results = tavily.search(
            query=search_query,
            max_results=max_results,
            include_answer=True,
            search_depth="advanced"
        )

        if not results or not results.get('results'):
            return f"No results found for: {query}"

        # Format results
        formatted = [f"Search: {query}\n"]

        # Add AI-generated answer if available
        if results.get('answer'):
            formatted.append(f"Summary: {results['answer']}\n")

        # Add individual results
        for i, result in enumerate(results['results'][:max_results], 1):
            title = result.get('title', 'No title')
            url = result.get('url', '')
            content = result.get('content', '')[:300]

            formatted.append(f"{i}. {title}")
            formatted.append(f"   {content}...")
            formatted.append(f"   Source: {url}\n")

        return "\n".join(formatted)

    except Exception as e:
        return f"Search error: {str(e)}"


def research_topic_data(topic: str, include_stats: bool = True) -> str:
    """
    Research topic to find statistics, trends, and data points

    Args:
        topic: Topic to research
        include_stats: Whether to focus on statistics and data

    Returns:
        Research findings with specific data points
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        # Optimize query for data/stats
        if include_stats:
            search_query = f"{topic} statistics data 2024 2025 trends metrics"
        else:
            search_query = f"{topic} latest news updates 2024 2025"

        results = tavily.search(
            query=search_query,
            max_results=5,
            include_answer=True,
            search_depth="advanced"
        )

        if not results:
            return f"No research data found for: {topic}"

        # Format as research brief
        formatted = [f"RESEARCH: {topic}\n"]

        if results.get('answer'):
            formatted.append(f"Key Findings:\n{results['answer']}\n")

        formatted.append("Sources:")
        for i, result in enumerate(results.get('results', [])[:3], 1):
            content = result.get('content', '')[:250]
            url = result.get('url', '')
            formatted.append(f"{i}. {content}...")
            formatted.append(f"   {url}\n")

        return "\n".join(formatted)

    except Exception as e:
        return f"Research error: {str(e)}"


def search_knowledge_base(query: str, category: str = None, limit: int = 3) -> str:
    """
    Search internal knowledge base for examples and guidelines

    Args:
        query: Search query
        category: Filter by category (optional)
        limit: Max results

    Returns:
        Relevant knowledge base content
    """
    try:
        from supabase import create_client
        import openai

        # Get embedding for query
        openai.api_key = os.getenv('OPENAI_API_KEY')
        embedding_response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = embedding_response.data[0].embedding

        # Search knowledge base
        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        results = client.rpc(
            'match_knowledge',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.7,
                'match_count': limit
            }
        ).execute()

        if not results.data:
            return f"No knowledge base results for: {query}"

        # Format results
        formatted = [f"KNOWLEDGE BASE: {query}\n"]
        for i, item in enumerate(results.data, 1):
            title = item.get('title', 'Untitled')
            content = item.get('content', '')[:300]
            similarity = item.get('similarity', 0)

            formatted.append(f"{i}. {title} (relevance: {similarity:.2f})")
            formatted.append(f"   {content}...\n")

        return "\n".join(formatted)

    except Exception as e:
        return f"Knowledge base error: {str(e)}"


def analyze_competitor_posts(topic: str, platform: str = "linkedin") -> str:
    """
    Analyze competitor posts on a topic for insights

    Args:
        topic: Topic to analyze
        platform: Social platform (linkedin, twitter, etc.)

    Returns:
        Analysis of competitor content patterns
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        # Search for competitor content
        search_query = f"site:{platform}.com/posts {topic} viral popular trending"

        results = tavily.search(
            query=search_query,
            max_results=5,
            include_answer=True
        )

        if not results or not results.get('results'):
            return f"No competitor posts found for: {topic}"

        # Analyze patterns
        formatted = [f"COMPETITOR ANALYSIS: {topic}\n"]

        if results.get('answer'):
            formatted.append(f"Patterns Observed:\n{results['answer']}\n")

        formatted.append("Top Performing Posts:")
        for i, result in enumerate(results['results'][:3], 1):
            title = result.get('title', '')
            content = result.get('content', '')[:200]
            formatted.append(f"{i}. {title}")
            formatted.append(f"   {content}...\n")

        return "\n".join(formatted)

    except Exception as e:
        return f"Competitor analysis error: {str(e)}"


def get_brand_voice_examples(user_id: str) -> str:
    """
    Retrieve brand voice guidelines and examples for user

    Args:
        user_id: User identifier

    Returns:
        Brand voice guidelines and example content
    """
    try:
        from supabase import create_client

        client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Try to get brand voice
        result = client.table('brand_voice')\
            .select('*')\
            .eq('user_id', user_id)\
            .limit(1)\
            .execute()

        if result.data:
            brand = result.data[0]
            voice_desc = brand.get('voice_description', '')
            do_list = brand.get('do_list', [])
            dont_list = brand.get('dont_list', [])

            formatted = [f"BRAND VOICE: {brand.get('brand_name', 'User Brand')}\n"]
            formatted.append(f"Description: {voice_desc}\n")

            if do_list:
                formatted.append("DO:")
                for item in do_list:
                    formatted.append(f"  ✓ {item}")

            if dont_list:
                formatted.append("\nDON'T:")
                for item in dont_list:
                    formatted.append(f"  ✗ {item}")

            return "\n".join(formatted)
        else:
            return "No brand voice configured. Using default professional tone."

    except Exception as e:
        return f"Brand voice error: {str(e)}"


# Tool definitions for Claude Agent SDK / Anthropic tool calling
LINKEDIN_TOOLS = [
    {
        "name": "web_search_linkedin_examples",
        "description": "Search the web for LinkedIn post examples and best practices. Use when you need inspiration or want to see how others write about a topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'best LinkedIn posts about AI productivity')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "research_topic_data",
        "description": "Research a topic to find statistics, trends, and data points. Use when you need specific numbers or recent developments to add credibility.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to research"
                },
                "include_stats": {
                    "type": "boolean",
                    "description": "Focus on statistics and data points",
                    "default": True
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "search_knowledge_base",
        "description": "Search internal knowledge base for brand guidelines, examples, and best practices. Use to maintain brand consistency.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_competitor_posts",
        "description": "Analyze how competitors write about a topic. Use to understand what works in your niche.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to analyze"
                },
                "platform": {
                    "type": "string",
                    "description": "Social platform",
                    "default": "linkedin"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "get_brand_voice_examples",
        "description": "Get brand voice guidelines for the user. Use to ensure content matches their voice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                }
            },
            "required": ["user_id"]
        }
    }
]

# Map tool names to functions
LINKEDIN_TOOL_FUNCTIONS = {
    "web_search_linkedin_examples": web_search_linkedin_examples,
    "research_topic_data": research_topic_data,
    "search_knowledge_base": search_knowledge_base,
    "analyze_competitor_posts": analyze_competitor_posts,
    "get_brand_voice_examples": get_brand_voice_examples
}

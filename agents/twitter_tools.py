"""
Twitter/X Research Tools for Agentic Content Creation
Enables autonomous research for examples, trends, and proven patterns
"""
import os
from tavily import TavilyClient
from typing import Dict, List, Any


def web_search_twitter_examples(query: str, max_results: int = 5) -> str:
    """
    Search web for real Twitter/X posts about a topic

    Args:
        query: Search query for Twitter posts
        max_results: Number of examples to return

    Returns:
        Formatted search results with post examples
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        # Search specifically for Twitter posts
        search_query = f"site:twitter.com OR site:x.com {query}"

        results = tavily.search(
            query=search_query,
            search_depth="advanced",
            max_results=max_results
        )

        # Format results
        formatted = f"Found {len(results.get('results', []))} Twitter examples for '{query}':\n\n"

        for i, result in enumerate(results.get('results', [])[:max_results], 1):
            formatted += f"{i}. {result.get('title', 'Untitled')}\n"
            formatted += f"   URL: {result.get('url', 'N/A')}\n"
            formatted += f"   Snippet: {result.get('content', 'N/A')[:200]}...\n\n"

        return formatted

    except Exception as e:
        return f"Error searching Twitter examples: {str(e)}"


def analyze_viral_tweets(topic: str, format_type: str = None) -> str:
    """
    Analyze what makes tweets go viral on a specific topic

    Args:
        topic: Topic to analyze
        format_type: Optional format (paragraph, listicle, old_vs_new, etc.)

    Returns:
        Analysis of viral patterns
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        # Search for viral tweets and analysis
        format_filter = f"{format_type} format" if format_type else "high engagement"
        search_query = f"viral tweets {topic} {format_filter} engagement metrics"

        results = tavily.search(
            query=search_query,
            search_depth="advanced",
            max_results=3
        )

        formatted = f"Viral patterns for '{topic}' tweets:\n\n"

        for i, result in enumerate(results.get('results', []), 1):
            formatted += f"{i}. {result.get('title', 'Untitled')}\n"
            formatted += f"   {result.get('content', 'N/A')[:250]}...\n\n"

        return formatted

    except Exception as e:
        return f"Error analyzing viral tweets: {str(e)}"


def search_twitter_trends(topic: str = None) -> str:
    """
    Search for current Twitter trends and discussions

    Args:
        topic: Optional topic to filter trends

    Returns:
        Current trends related to topic
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        # Search for trending topics
        search_query = f"Twitter trends {topic}" if topic else "Twitter trending topics today"

        results = tavily.search(
            query=search_query,
            search_depth="basic",
            max_results=5
        )

        formatted = f"Current Twitter trends{f' for {topic}' if topic else ''}:\n\n"

        for i, result in enumerate(results.get('results', []), 1):
            formatted += f"{i}. {result.get('title', 'Untitled')}\n"
            formatted += f"   {result.get('content', 'N/A')[:200]}...\n\n"

        return formatted

    except Exception as e:
        return f"Error searching trends: {str(e)}"


def get_format_best_practices(format_type: str) -> str:
    """
    Get best practices for specific Twitter format

    Args:
        format_type: Format type (paragraph, what_how_why, listicle, old_vs_new, magical_ways)

    Returns:
        Best practices for the format
    """

    best_practices = {
        "paragraph": """
Paragraph Format Best Practices:
- Concise language, economical sentences
- Alternate long and short sentences for rhythm
- Strong opinion or declarative statement
- Avoid hedging, take a clear stance
- Subtle poetic devices (alliteration, repetition)
- Should read like a highlighted book passage
""",
        "what_how_why": """
What/How/Why Format Best Practices:
- Opening hook (declarative, question, controversial, vulnerable, stat)
- 3-5 bulleted items that are tangible and differentiated
- Avoid conventional wisdom and fluff
- Steps should be clear and actionable
- Closing sentence inspires action or shows cost of inaction
""",
        "listicle": """
Listicle Format Best Practices:
- Clear first sentence stating what you're giving
- Tangible, specific items (not vague advice)
- Common categories: tips, tools, books, habits, mistakes, lessons
- Be as specific as possible in each item
- Optional closing question to engage readers
""",
        "old_vs_new": """
Old vs New Format Best Practices:
- Visual mirroring is key (symmetrical formatting)
- 1-3 word category labels (or short sentence)
- 3 bullets for "old" way
- 3 bullets for "new" way
- Opposing comparisons that conflict
- Tangible, differentiated examples
- Optional parting wisdom at end
""",
        "magical_ways": """
10 Magical Ways Format Best Practices:
- Pick one topic: tips, stats, steps, lessons, benefits, reasons, mistakes, examples, questions, stories
- Promise it in first sentence
- Deliver in bulleted list
- Differentiated or unconventional insights
- Extremely concise and actionable
- Optional closing encouragement
"""
    }

    return best_practices.get(format_type, "Unknown format type")


def search_knowledge_base_twitter(query: str, limit: int = 3) -> str:
    """
    Search internal knowledge base for Twitter examples

    Args:
        query: Search query
        limit: Max results

    Returns:
        Matching Twitter content from knowledge base
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

        # Create embedding for query
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = embedding_response.data[0].embedding

        # Search Supabase with vector similarity
        result = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.7,
                'match_count': limit
            }
        ).execute()

        if not result.data:
            return f"No Twitter examples found in knowledge base for '{query}'"

        formatted = f"Found {len(result.data)} Twitter examples from knowledge base:\n\n"

        for i, doc in enumerate(result.data, 1):
            formatted += f"{i}. (Score: {doc.get('similarity', 0):.2f})\n"
            formatted += f"{doc.get('content', 'N/A')}\n\n"

        return formatted

    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


# Tool definitions for Claude
TWITTER_TOOLS = [
    {
        "name": "web_search_twitter_examples",
        "description": "Search the web for real Twitter/X posts about a topic to analyze proven patterns and styles",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for Twitter posts"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of examples to return (default 5)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_viral_tweets",
        "description": "Analyze what makes tweets go viral on a specific topic, including engagement patterns",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to analyze for viral patterns"
                },
                "format_type": {
                    "type": "string",
                    "description": "Optional format filter (paragraph, listicle, etc.)"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "search_twitter_trends",
        "description": "Search for current Twitter trends and hot topics",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Optional topic to filter trends"
                }
            }
        }
    },
    {
        "name": "get_format_best_practices",
        "description": "Get best practices and guidelines for a specific Twitter format",
        "input_schema": {
            "type": "object",
            "properties": {
                "format_type": {
                    "type": "string",
                    "description": "Format type: paragraph, what_how_why, listicle, old_vs_new, or magical_ways"
                }
            },
            "required": ["format_type"]
        }
    },
    {
        "name": "search_knowledge_base_twitter",
        "description": "Search internal knowledge base for proven Twitter examples using vector similarity",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for Twitter examples"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of results (default 3)"
                }
            },
            "required": ["query"]
        }
    }
]

# Map tool names to functions
TOOL_FUNCTIONS = {
    "web_search_twitter_examples": web_search_twitter_examples,
    "analyze_viral_tweets": analyze_viral_tweets,
    "search_twitter_trends": search_twitter_trends,
    "get_format_best_practices": get_format_best_practices,
    "search_knowledge_base_twitter": search_knowledge_base_twitter
}

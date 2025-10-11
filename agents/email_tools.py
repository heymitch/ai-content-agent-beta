"""
Email Research Tools for Agentic Email Creation
Enables autonomous research for case studies, examples, and best practices
"""
import os
from tavily import TavilyClient
from typing import Dict, List, Any


def search_email_examples(email_type: str, topic: str = None, max_results: int = 3) -> str:
    """
    Search for proven email examples by type

    Args:
        email_type: Type of email (value, indirect, direct)
        topic: Optional topic filter
        max_results: Number of examples

    Returns:
        Formatted search results with email examples
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        # Build search query
        search_terms = {
            "value": "value email examples educational content",
            "indirect": "indirect email faulty belief framework case study",
            "direct": "direct response email call to action conversion"
        }

        base_query = search_terms.get(email_type, "email marketing examples")
        search_query = f"{base_query} {topic}" if topic else base_query

        results = tavily.search(
            query=search_query,
            search_depth="advanced",
            max_results=max_results
        )

        formatted = f"Found {len(results.get('results', []))} {email_type} email examples:\n\n"

        for i, result in enumerate(results.get('results', []), 1):
            formatted += f"{i}. {result.get('title', 'Untitled')}\n"
            formatted += f"   {result.get('content', 'N/A')[:300]}...\n\n"

        return formatted

    except Exception as e:
        return f"Error searching email examples: {str(e)}"


def research_case_study_data(topic: str, industry: str = None) -> str:
    """
    Research case studies and success stories

    Args:
        topic: Topic to research
        industry: Optional industry filter

    Returns:
        Case study data with metrics
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        industry_filter = f"{industry}" if industry else ""
        search_query = f"{topic} case study success story metrics results {industry_filter}"

        results = tavily.search(
            query=search_query,
            search_depth="advanced",
            max_results=5
        )

        formatted = f"Case study research for '{topic}':\n\n"

        for i, result in enumerate(results.get('results', []), 1):
            formatted += f"{i}. {result.get('title', 'Untitled')}\n"
            formatted += f"   {result.get('content', 'N/A')[:250]}...\n\n"

        return formatted

    except Exception as e:
        return f"Error researching case studies: {str(e)}"


def find_statistics_and_data(topic: str) -> str:
    """
    Find statistics and data points for email content

    Args:
        topic: Topic to find stats for

    Returns:
        Statistics and data points
    """
    try:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

        search_query = f"{topic} statistics data 2024 2025 metrics trends research"

        results = tavily.search(
            query=search_query,
            search_depth="advanced",
            max_results=5
        )

        formatted = f"Statistics and data for '{topic}':\n\n"

        for i, result in enumerate(results.get('results', []), 1):
            formatted += f"{i}. {result.get('title', 'Untitled')}\n"
            formatted += f"   {result.get('content', 'N/A')[:200]}...\n\n"

        return formatted

    except Exception as e:
        return f"Error finding statistics: {str(e)}"


def get_email_best_practices(email_type: str) -> str:
    """
    Get best practices for specific email type

    Args:
        email_type: Email type (value, indirect, direct)

    Returns:
        Best practices guidelines
    """

    practices = {
        "value": """
**VALUE EMAIL BEST PRACTICES:**

**Structure (400-500 words):**
1. Personal Credibility Hook (2-3 sentences)
2. Problem Recognition (2-3 sentences)
3. Value Delivery - SINGLE TOOL FOCUS (8-12 sentences)
4. Soft CTA (1-2 sentences)

**Critical Rules:**
- MAXIMUM 2 tools (1 primary + 1 supporting)
- Primary tool gets 150+ words with detailed implementation
- Minimum 3 step-by-step setup instructions
- Interface/screenshot details described
- Troubleshooting section for common issues
- Exact metrics and timeframe for results

**Subject Lines (30-45 chars):**
- "[Specific tool] that [specific outcome]"
- "How I [result] with ONE [tool]"
- "The [tool] workflow that [outcome]"

**Avoid:**
- Multiple tools (breadth kills conversions)
- Surface-level explanations
- Generic advice without personal experience
- Overview approach
""",
        "indirect": """
**INDIRECT EMAIL BEST PRACTICES:**

**Structure (400-600 words):**
1. Hook - Challenge belief or surprising insight (1-2 sentences)
2. Story/Case Study - Specific client example (3-4 sentences)
3. Faulty Belief - Why common approach fails (2-3 sentences)
4. Truth - What actually works (2-3 sentences)
5. Proof - Additional evidence (1-2 sentences)
6. Bridge - Connect to reader (1-2 sentences)
7. CTA - Relevant call-to-action (1-2 sentences)

**Subject Lines:**
- "So [client name] just told me..."
- "Because everyone thinks [faulty belief]..."
- "[Surprising result] in [timeframe]"
- "The [industry] lie nobody talks about"

**Faulty Belief Framework:**
1. Common Belief - What most think is true
2. Why It's Wrong - Real reason it's flawed
3. What's Actually True - Counter-intuitive reality
4. Proof - Case study or data demonstrating this

**Voice:**
- Start with "So" and "Because" naturally
- "Here's the thing..." for transitions
- "Most people think..." or "Everyone says..."
- Specific details: names, numbers, timeframes
""",
        "direct": """
**DIRECT EMAIL BEST PRACTICES:**

**Structure (100-200 words):**
1. Direct Hook (1-2 sentences)
2. Value/Reason (2-3 sentences)
3. Clear CTA (1-2 sentences)

**Subject Lines (20-35 chars):**
- "Ready to [specific outcome]?"
- "[Result] in [timeframe]?"
- "Want to [benefit]?"
- "Quick question for you"

**Hooks:**
- Direct Question: "Quick question: Are you ready to [outcome]?"
- Assumption: "If you're serious about [goal], this is for you."
- Urgency: "We close applications for [offer] in [timeframe]."

**Voice:**
- Business-first, writing-second
- No-bullshit directness
- Founder energy
- Anti-commodity positioning
- Direct and confident, not pushy
- Specific outcomes: "$15K retainer clients"

**Avoid:**
- Long explanations (they know the value)
- Multiple CTAs
- Weak urgency
- Generic benefits
"""
    }

    return practices.get(email_type, "Unknown email type")


def search_knowledge_base_emails(query: str, email_type: str = None, limit: int = 3) -> str:
    """
    Search internal knowledge base for email examples

    Args:
        query: Search query
        email_type: Optional email type filter
        limit: Max results

    Returns:
        Matching email content from knowledge base
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
            return f"No email examples found in knowledge base for '{query}'"

        formatted = f"Found {len(result.data)} email examples from knowledge base:\n\n"

        for i, doc in enumerate(result.data, 1):
            formatted += f"{i}. (Similarity: {doc.get('similarity', 0):.2f})\n"
            formatted += f"{doc.get('content', 'N/A')[:300]}...\n\n"

        return formatted

    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


# Tool definitions for Claude
EMAIL_TOOLS = [
    {
        "name": "search_email_examples",
        "description": "Search for proven email examples by type (value/indirect/direct) to analyze successful patterns",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_type": {
                    "type": "string",
                    "description": "Type of email: value, indirect, or direct"
                },
                "topic": {
                    "type": "string",
                    "description": "Optional topic filter"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of examples to return (default 3)"
                }
            },
            "required": ["email_type"]
        }
    },
    {
        "name": "research_case_study_data",
        "description": "Research case studies and success stories with metrics for indirect emails",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to research case studies for"
                },
                "industry": {
                    "type": "string",
                    "description": "Optional industry filter"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "find_statistics_and_data",
        "description": "Find statistics and data points to support email claims",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to find statistics for"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "get_email_best_practices",
        "description": "Get comprehensive best practices for a specific email type",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_type": {
                    "type": "string",
                    "description": "Email type: value, indirect, or direct"
                }
            },
            "required": ["email_type"]
        }
    },
    {
        "name": "search_knowledge_base_emails",
        "description": "Search internal knowledge base for proven email examples using vector similarity",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for email examples"
                },
                "email_type": {
                    "type": "string",
                    "description": "Optional email type filter"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 3)"
                }
            },
            "required": ["query"]
        }
    }
]

# Map tool names to functions
TOOL_FUNCTIONS = {
    "search_email_examples": search_email_examples,
    "research_case_study_data": research_case_study_data,
    "find_statistics_and_data": find_statistics_and_data,
    "get_email_best_practices": get_email_best_practices,
    "search_knowledge_base_emails": search_knowledge_base_emails
}

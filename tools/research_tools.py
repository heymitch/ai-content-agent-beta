"""
Research Tools
Save and search Tavily research digests and industry reports
"""

import os
from typing import List, Dict, Optional
from datetime import date, datetime
from openai import OpenAI
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)


def generate_embedding(text: str) -> List[float]:
    """Generate OpenAI embedding for text"""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000]  # Limit to avoid token limits
    )
    return response.data[0].embedding


def calculate_credibility_score(source_names: List[str]) -> int:
    """Calculate credibility score based on source quality (1-10 scale)"""
    high_credibility = [
        'harvard business review', 'mckinsey', 'mit', 'stanford',
        'gartner', 'forrester', 'pew research', 'nielsen'
    ]
    medium_credibility = [
        'techcrunch', 'wired', 'forbes', 'bloomberg', 'wsj',
        'new york times', 'economist', 'venturebeat'
    ]

    if not source_names:
        return 5  # Default

    scores = []
    for source in source_names:
        source_lower = source.lower()
        if any(hc in source_lower for hc in high_credibility):
            scores.append(10)
        elif any(mc in source_lower for mc in medium_credibility):
            scores.append(7)
        else:
            scores.append(5)  # Unknown source

    return max(scores) if scores else 5


def save_research(
    topic: str,
    summary: str,
    full_report: Optional[str] = None,
    key_stats: Optional[List[str]] = None,
    source_urls: Optional[List[str]] = None,
    source_names: Optional[List[str]] = None,
    primary_source: Optional[str] = None,
    topics: Optional[List[str]] = None,
    research_date: Optional[date] = None
) -> str:
    """
    Save research digest to database with embedding

    Args:
        topic: Main topic researched
        summary: Executive summary (2-3 sentences)
        full_report: Complete research report (optional)
        key_stats: List of key statistics found
        source_urls: URLs of sources
        source_names: Names of sources (e.g., "Harvard Business Review")
        primary_source: Most credible/relevant source
        topics: Tags for categorization (e.g., ['retention', 'SaaS'])
        research_date: When research was conducted (defaults to today)

    Returns:
        UUID of saved research record
    """

    # Generate embedding from summary + key stats
    embed_text = summary
    if key_stats:
        embed_text += "\n\n" + "\n".join(key_stats)

    embedding = generate_embedding(embed_text)

    # Calculate credibility
    credibility_score = calculate_credibility_score(source_names or [])

    # Prepare data
    data = {
        'topic': topic,
        'summary': summary,
        'full_report': full_report,
        'key_stats': key_stats or [],
        'source_urls': source_urls or [],
        'source_names': source_names or [],
        'primary_source': primary_source,
        'credibility_score': credibility_score,
        'research_date': (research_date or date.today()).isoformat(),
        'last_verified': date.today().isoformat(),
        'topics': topics or [],
        'embedding': embedding,
        'usage_count': 0,
        'used_in_content_ids': [],
        'status': 'active'
    }

    # Insert to database
    result = supabase.table('research').insert(data).execute()

    if result.data:
        research_id = result.data[0]['id']
        print(f"✅ Saved research: {topic} (ID: {research_id})")
        return research_id
    else:
        raise Exception(f"Failed to save research: {result}")


def search_research(
    query: str,
    match_count: int = 5,
    min_credibility: int = 5,
    match_threshold: float = 0.7
) -> List[Dict]:
    """
    Search research database using semantic similarity

    Args:
        query: Search query
        match_count: Number of results to return
        min_credibility: Minimum credibility score (1-10)
        match_threshold: Similarity threshold (0-1)

    Returns:
        List of matching research records with similarity scores
    """

    # Generate embedding for query
    query_embedding = generate_embedding(query)

    # Search using RPC function
    result = supabase.rpc('match_research', {
        'query_embedding': query_embedding,
        'match_threshold': match_threshold,
        'match_count': match_count,
        'min_credibility': min_credibility
    }).execute()

    return result.data


def get_research_by_topic(topic: str) -> List[Dict]:
    """Get all research records for a specific topic"""
    result = supabase.table('research').select('*').eq('topic', topic).eq(
        'status', 'active'
    ).order('research_date', desc=True).execute()

    return result.data


def mark_research_used(research_id: str, content_id: str):
    """Mark research as used in a piece of content"""
    # Get current research record
    result = supabase.table('research').select('used_in_content_ids, usage_count').eq(
        'id', research_id
    ).execute()

    if not result.data:
        return

    record = result.data[0]
    used_ids = record.get('used_in_content_ids', [])
    usage_count = record.get('usage_count', 0)

    # Update
    if content_id not in used_ids:
        used_ids.append(content_id)
        usage_count += 1

        supabase.table('research').update({
            'used_in_content_ids': used_ids,
            'usage_count': usage_count
        }).eq('id', research_id).execute()

        print(f"✅ Marked research {research_id} as used in content {content_id}")


def get_popular_research(limit: int = 10) -> List[Dict]:
    """Get most-used research records"""
    result = supabase.table('research').select('*').eq(
        'status', 'active'
    ).order('usage_count', desc=True).limit(limit).execute()

    return result.data


def archive_outdated_research(days_old: int = 365):
    """Mark research older than X days as outdated"""
    from datetime import timedelta

    cutoff_date = (date.today() - timedelta(days=days_old)).isoformat()

    result = supabase.table('research').update({
        'status': 'outdated'
    }).lt('research_date', cutoff_date).eq('status', 'active').execute()

    if result.data:
        count = len(result.data)
        print(f"📦 Archived {count} outdated research record(s)")


# Convenience function for Tavily web search results
def save_tavily_research(
    topic: str,
    tavily_results: List[Dict],
    summary: str
) -> str:
    """
    Save Tavily web search results as research

    Args:
        topic: Research topic
        tavily_results: Raw results from Tavily API
        summary: Your summary of findings

    Returns:
        Research ID
    """

    # Extract data from Tavily results
    source_urls = []
    source_names = []
    key_stats = []

    for result in tavily_results:
        if 'url' in result:
            source_urls.append(result['url'])
        if 'title' in result:
            source_names.append(result['title'])
        if 'content' in result:
            # Extract any numbers/stats from content (simple heuristic)
            content = result['content']
            # Look for patterns like "X%" or "X out of Y"
            import re
            stats = re.findall(r'\d+%|\d+\s+(?:out of|in)\s+\d+', content)
            key_stats.extend(stats[:2])  # Max 2 stats per source

    # Determine primary source (first result usually most relevant)
    primary_source = source_names[0] if source_names else None

    return save_research(
        topic=topic,
        summary=summary,
        key_stats=list(set(key_stats)),  # Deduplicate
        source_urls=source_urls,
        source_names=source_names,
        primary_source=primary_source
    )


# Testing
if __name__ == "__main__":
    # Example: Save research from Tavily
    print("Testing research tools...")

    # Save example research
    research_id = save_research(
        topic="SaaS retention rates 2024",
        summary="Top SaaS companies maintain 90%+ annual retention. Key drivers: onboarding quality, product-market fit, and customer success investment.",
        key_stats=[
            "90% of top SaaS companies have 90%+ net retention",
            "Companies with <85% retention struggle to achieve profitability",
            "Every 1% increase in retention = 7% increase in customer lifetime value"
        ],
        source_names=["McKinsey", "SaaS Capital"],
        source_urls=["https://mckinsey.com/saas-retention", "https://saas-capital.com/retention-2024"],
        primary_source="McKinsey",
        topics=["SaaS", "retention", "metrics"]
    )

    print(f"\nResearch ID: {research_id}")

    # Search for it
    print("\nSearching for 'customer retention'...")
    results = search_research("customer retention strategies", match_count=3)

    for r in results:
        print(f"\n- {r['topic']}")
        print(f"  Summary: {r['summary'][:100]}...")
        print(f"  Credibility: {r['credibility_score']}/10")
        print(f"  Similarity: {r['similarity']:.2f}")

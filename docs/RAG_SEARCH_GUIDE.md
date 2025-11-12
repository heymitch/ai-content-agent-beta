# RAG Search Strategy Guide

## Problem: Agents Creating Overly Specific Queries

When users ask vague questions like "What did Joel say?", agents often create verbose semantic queries like "Joel meeting notes insights takeaways discussion" that fail to match simple document titles like "Joel lift-off OB".

## Solution: Hybrid Search (Keyword + Semantic)

The `search_company_documents` tool now uses a two-phase approach:

### Phase 1: Keyword Matching (Fast, Exact)
- Extracts meaningful keywords from query (removes stop words like "meeting", "notes", "insights", "discussion")
- Searches document **titles** using case-insensitive partial matching
- Example: Query "Joel meeting notes insights" → Keyword "joel" → Finds "Joel Liftoff OB"

### Phase 2: Semantic Search (Slower, Fuzzy)
- Only runs if Phase 1 doesn't fill all requested slots
- Uses vector embeddings to find conceptually similar content
- Searches document **content** with lower threshold (30% similarity)
- Useful for topic-based searches: "AI productivity tools", "customer success metrics"

## How Agents Should Use This

### Simple Name/Keyword Searches
```python
# ✅ GOOD: Let the tool extract keywords
search_company_documents("Joel")
search_company_documents("pricing strategy")
search_company_documents("product roadmap Q2")

# ❌ BAD: Over-specifying creates noise
search_company_documents("Joel meeting notes insights takeaways discussion key points")
search_company_documents("comprehensive analysis of pricing strategy frameworks")
```

### Topic-Based Searches
```python
# ✅ GOOD: Natural phrases work for semantic search
search_company_documents("customer success stories")
search_company_documents("AI agent productivity case studies")
search_company_documents("testimonials about ROI improvement")
```

## Agent Prompt Guidance

**When user asks: "Find documents about Joel"**
- Agent should call: `search_company_documents("Joel", match_count=5)`
- NOT: `search_company_documents("Joel meeting notes onboarding discussion insights takeaways")`

**When user asks: "What do we have on pricing?"**
- Agent should call: `search_company_documents("pricing", match_count=5)`
- If that returns generic results, THEN try: `search_company_documents("pricing strategy enterprise B2B")`

## Result Format

Each match includes:
```json
{
  "title": "Joel Liftoff OB",
  "content": "...",
  "document_type": "meeting_notes",
  "similarity": 0.95,
  "match_type": "keyword"  // or "semantic"
}
```

The `match_type` field shows which phase found the result:
- `"keyword"` = Found via title matching (high confidence)
- `"semantic"` = Found via content embeddings (medium confidence)

## Performance

- **Keyword phase**: ~100-200ms (PostgreSQL ILIKE query)
- **Semantic phase**: ~1-2s (embedding generation + vector search)
- **Combined**: Typically 100-500ms if keywords match, 1-2s if semantic fallback needed

## Testing

Run the test suite to verify:
```bash
python3 test_hybrid_search.py
```

This tests both:
1. Simple keyword search ("Joel")
2. Verbose query with noise words ("Joel meeting notes insights takeaways discussion")

Both should return the same results via keyword extraction.
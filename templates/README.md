# Template Library

This directory contains searchable content templates that Prime Agent uses to suggest formats during strategy sessions.

## Structure

```
templates/
├── email/                      # Email templates (VALUE, STORY, ANNOUNCEMENT, etc)
├── linkedin/                   # LinkedIn post templates (frameworks, stories, hot takes)
├── twitter/                    # Twitter templates (single posts, threads, hot takes)
├── blog/                       # Long-form blog templates
├── digital-writing-tactics/    # Ship 30 tactics and frameworks
├── ship-30/                    # Ship 30 specific formats and strategies
└── copywriting/                # Classic copywriting formulas (AIDA, PAS, etc)
```

## Template Format

Each template is a JSON file with:
- **template_id**: Unique identifier
- **name**: Human-readable name
- **platform**: Target platform
- **description**: What this template is for
- **use_when**: List of scenarios where this template fits
- **structure**: Sections with word/char counts and guidelines
- **quality_criteria**: Platform-specific quality axes
- **examples**: 2-3 reference examples
- **forbidden_patterns**: Anti-patterns to avoid

## How It Works

1. **User gives vague intent** → "teach people about MCP"
2. **Prime Agent searches templates** → Semantic similarity on `description` + `use_when`
3. **Returns top 3 matches** → Shows user options
4. **User picks template** → Structure passed to platform sub-agent
5. **Sub-agent generates** → Following template guidelines

## RAG Search

Templates are semantically searchable:
- Embed `description` + `use_when` fields
- Cosine similarity with user intent
- Metadata filters (platform, content_type)
- Returns top-k matches with scores

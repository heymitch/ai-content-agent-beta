"""
Anthropic tool schemas for Claude function calling
"""

TOOL_SCHEMAS = [
    {
        "name": "execute_content_workflow",
        "description": "Execute the 3-agent content workflow (Writer → Validator → Reviser) to create high-quality content. Use this when the user requests content creation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["linkedin", "twitter", "email"],
                    "description": "Target platform for content"
                },
                "topic": {
                    "type": "string",
                    "description": "Content topic or brief"
                },
                "additional_context": {
                    "type": "string",
                    "description": "Extra context like research findings, brand voice, specific angles to take"
                },
                "target_score": {
                    "type": "integer",
                    "description": "Minimum quality score threshold (default 80)"
                }
            },
            "required": ["platform", "topic"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for current information, trends, news, or research. Use this when you need up-to-date information or data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default 5)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_knowledge_base",
        "description": "Search the RAG knowledge base for brand guidelines, past examples, frameworks, and strategies. Use this to maintain brand consistency.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in the knowledge base"
                },
                "match_count": {
                    "type": "integer",
                    "description": "Number of results (default 5)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_brand_voice",
        "description": "Fetch user-specific brand voice guidelines including tone, do/don't lists, and examples.",
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
    },
    {
        "name": "analyze_past_content",
        "description": "Analyze high-performing past content to learn patterns and what works well.",
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "Filter by platform (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of posts to analyze (default 10)"
                }
            },
            "required": []
        }
    },
    {
        "name": "send_to_calendar",
        "description": "Schedule content to the Airtable content calendar. Use after content is approved.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Content text to schedule"
                },
                "platform": {
                    "type": "string",
                    "description": "Platform name"
                },
                "publish_date": {
                    "type": "string",
                    "description": "Date to publish (YYYY-MM-DD, 'tomorrow', 'next monday', etc.)"
                },
                "score": {
                    "type": "integer",
                    "description": "Quality score"
                }
            },
            "required": ["content", "platform"]
        }
    },
    {
        "name": "execute_batch_workflows",
        "description": "Execute multiple content workflows in sequence with rate limiting. Use for batch content creation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflows": {
                    "type": "array",
                    "description": "List of workflow configurations",
                    "items": {
                        "type": "object",
                        "properties": {
                            "platform": {"type": "string"},
                            "topic": {"type": "string"},
                            "additional_context": {"type": "string"},
                            "publish_date": {"type": "string"}
                        }
                    }
                },
                "delay_seconds": {
                    "type": "integer",
                    "description": "Delay between workflows (default 2)"
                },
                "auto_send_to_calendar": {
                    "type": "boolean",
                    "description": "Auto-schedule to calendar (default true)"
                }
            },
            "required": ["workflows"]
        }
    },
    {
        "name": "save_to_knowledge_base",
        "description": "Save approved content or insights to the knowledge base for future reference.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Content title"
                },
                "content": {
                    "type": "string",
                    "description": "Content text"
                },
                "content_type": {
                    "type": "string",
                    "enum": ["example", "strategy", "voice", "framework"],
                    "description": "Type of content"
                }
            },
            "required": ["title", "content"]
        }
    }
]

"""
Tool registry for Slack agent
Clean, focused set of tools for content creation
"""

from .content_tools import (
    execute_content_workflow,
    execute_batch_workflows,
    send_to_calendar
)

from .search_tools import (
    web_search,
    search_knowledge_base,
    analyze_past_content
)

from .brand_tools import (
    get_brand_voice,
    save_to_knowledge_base
)

# Tool registry for Anthropic
TOOL_REGISTRY = {
    "execute_content_workflow": execute_content_workflow,
    "execute_batch_workflows": execute_batch_workflows,
    "send_to_calendar": send_to_calendar,
    "web_search": web_search,
    "search_knowledge_base": search_knowledge_base,
    "analyze_past_content": analyze_past_content,
    "get_brand_voice": get_brand_voice,
    "save_to_knowledge_base": save_to_knowledge_base,
}

__all__ = [
    'TOOL_REGISTRY',
    'execute_content_workflow',
    'execute_batch_workflows',
    'send_to_calendar',
    'web_search',
    'search_knowledge_base',
    'analyze_past_content',
    'get_brand_voice',
    'save_to_knowledge_base',
]

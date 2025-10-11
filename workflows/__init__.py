"""
Workflow registry for platform routing
Add new platforms here to enable auto-discovery by CMO agent
"""
from .agentic_linkedin_workflow import AgenticLinkedInWorkflow
from .agentic_twitter_workflow import AgenticTwitterWorkflow
from .agentic_email_workflow import AgenticEmailWorkflow

WORKFLOW_REGISTRY = {
    "linkedin": AgenticLinkedInWorkflow,  # Agentic with autonomous research
    "twitter": AgenticTwitterWorkflow,     # Agentic with format selection
    "email": AgenticEmailWorkflow,         # Agentic with type selection (value/indirect/direct)
    # "youtube": YouTubeWorkflow,  # Phase 4
}

__all__ = [
    'WORKFLOW_REGISTRY',
    'AgenticLinkedInWorkflow',
    'AgenticTwitterWorkflow',
    'AgenticEmailWorkflow',
]

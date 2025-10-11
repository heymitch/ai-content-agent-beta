"""
Agentic LinkedIn Workflow - Fully autonomous content creation
Wraps AgenticLinkedInOrchestrator to match workflow interface
"""
from .base_workflow import ContentWorkflow
import sys
import os
from typing import Dict, Any

# Add parent directory to path for validator imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from validators.linkedin_validator import LinkedInValidator
from agents.linkedin_sdk_agent import LinkedInSDKAgent


class AgenticLinkedInWorkflow(ContentWorkflow):
    """
    Fully agentic LinkedIn workflow with autonomous research and tool calling

    Flow:
    1. Autonomous hook generation (with web research)
    2. Draft creation with hook
    3. Autonomous proof injection (with data research)
    4. Validation & editing loop
    """

    def __init__(self, supabase_client, airtable_client=None):
        """
        Initialize agentic LinkedIn workflow

        Args:
            supabase_client: Supabase client instance
            airtable_client: Airtable client (optional)
        """
        super().__init__(
            platform="linkedin",
            validator_class=LinkedInValidator,
            supabase_client=supabase_client
        )

        # Tier 2 LinkedIn SDK agent (Claude tool orchestrator)
        self.agent = LinkedInSDKAgent()

    async def execute(
        self,
        brief: str,
        brand_context: str = "",
        user_id: str = "default",
        max_iterations: int = 3,
        target_score: int = 85
    ) -> Dict[str, Any]:
        """
        Execute fully agentic LinkedIn content creation

        Args:
            brief: Content topic/brief
            brand_context: Brand voice (optional - orchestrator fetches from DB)
            user_id: User identifier
            max_iterations: Max editing iterations
            target_score: Minimum quality score (default 85 for LinkedIn)

        Returns:
            Dict with draft, score, hooks, iterations, metadata
        """

        print(f"🚀 Agentic LinkedIn Workflow: Starting for '{brief}'")

        sdk_result = await self.agent.create_post(
            topic=brief,
            context=brand_context,
            post_type='standard',
            target_score=target_score
        )

        if not sdk_result.get('success'):
            raise RuntimeError(sdk_result.get('error', 'Unknown LinkedIn SDK error'))

        draft = sdk_result.get('post', '')
        score = sdk_result.get('score', 0)
        iterations = sdk_result.get('iterations', 1)
        grading = {
            'score': score,
            'feedback': '',
            'strengths': [],
            'issues': [],
            'timeline': sdk_result.get('timeline', [])
        }

        normalized_result = {
            'draft': draft,
            'grading': grading,
            'score': score,
            'iterations': iterations,
            'platform': 'linkedin',
            'hook_used': {'preview': sdk_result.get('hook')},
            'all_hooks': [],
            'workflow_type': 'sdk_agent'
        }

        print(f"✅ Agentic LinkedIn Workflow: Score {score}/100 in {iterations} iterations")

        return normalized_result

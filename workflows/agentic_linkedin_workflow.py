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
from agents.linkedin_direct_api_agent import create_linkedin_post


class AgenticLinkedInWorkflow(ContentWorkflow):
    """
    LinkedIn workflow using Direct API agent

    Flow:
    1. Hook generation
    2. Draft creation with hook
    3. Proof injection
    4. Validation & editing loop
    """

    def __init__(self, supabase_client, airtable_client=None):
        """
        Initialize LinkedIn workflow

        Args:
            supabase_client: Supabase client instance
            airtable_client: Airtable client (optional)
        """
        super().__init__(
            platform="linkedin",
            validator_class=LinkedInValidator,
            supabase_client=supabase_client
        )

        self.supabase_client = supabase_client

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

        print(f"🚀 LinkedIn Workflow: Starting for '{brief}'")

        # Use Direct API agent
        result = await create_linkedin_post(
            topic=brief,
            context=brand_context,
            post_type='standard',
            target_score=target_score,
            supabase_client=self.supabase_client
        )

        if not result.get('success'):
            raise RuntimeError(result.get('error', 'Unknown LinkedIn error'))

        draft = result.get('post', '')
        score = result.get('score', 0)
        iterations = result.get('iterations', 1)
        grading = {
            'score': score,
            'feedback': result.get('feedback', ''),
            'strengths': [],
            'issues': [],
            'timeline': result.get('timeline', [])
        }

        normalized_result = {
            'draft': draft,
            'grading': grading,
            'score': score,
            'iterations': iterations,
            'platform': 'linkedin',
            'hook_used': {'preview': result.get('hook')},
            'all_hooks': result.get('all_hooks', []),
            'workflow_type': 'direct_api'
        }

        print(f"✅ LinkedIn Workflow: Score {score}/100 in {iterations} iterations")

        return normalized_result

"""
LinkedIn-specific workflow implementation
NOW USES: Intelligent LinkedIn Agent with hook generation, proof injection, editing loop
"""
from .base_workflow import ContentWorkflow
import sys
import os
from typing import Dict, Any

# Add parent directory to path for validator imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from validators.linkedin_validator import LinkedInValidator
from agents.linkedin_agent import LinkedInContentAgent


class LinkedInWorkflow(ContentWorkflow):
    """
    LinkedIn content creation workflow with full agent orchestration

    Flow:
    1. Research (brand voice, RAG, web search)
    2. Hook generation (5 options)
    3. Draft creation
    4. Proof injection
    5. Validation & editing loop
    """

    def __init__(self, supabase_client, airtable_client=None):
        """
        Initialize LinkedIn workflow with agent

        Args:
            supabase_client: Supabase client instance
            airtable_client: Airtable client (optional)
        """
        super().__init__(
            platform="linkedin",
            validator_class=LinkedInValidator,
            supabase_client=supabase_client
        )

        # Initialize LinkedIn agent
        self.agent = LinkedInContentAgent(supabase_client, airtable_client)

    async def execute(
        self,
        brief: str,
        brand_context: str = "",
        user_id: str = "default",
        max_iterations: int = 3,
        target_score: int = 85
    ) -> Dict[str, Any]:
        """
        Execute full LinkedIn agent workflow

        Args:
            brief: Content topic/brief
            brand_context: Brand voice (optional - agent fetches from DB)
            user_id: User identifier
            max_iterations: Max editing iterations
            target_score: Minimum quality score (default 85 for LinkedIn)

        Returns:
            Dict with draft, score, hooks, iterations, metadata
        """

        print(f"📝 LinkedIn Workflow: Starting agent for '{brief}'")

        # Use the intelligent agent (handles everything)
        result = await self.agent.create_content(
            topic=brief,
            user_id=user_id,
            target_score=target_score,
            max_iterations=max_iterations
        )

        print(f"✅ LinkedIn Workflow: Complete! Score {result['score']}/100")

        return result

    def _get_platform_rules(self) -> str:
        """Override to include LinkedIn-specific emphasis (legacy - not used by agent)"""
        base_rules = super()._get_platform_rules()

        linkedin_emphasis = """

**LINKEDIN PLATFORM PRIORITY:**
- Mobile-first formatting (short paragraphs, line breaks)
- Professional but conversational tone
- Value-first (insight in first 2 lines for preview)
- Engagement-focused ending (comment prompt or CTA)
- Optimal length: 150-300 words for feed visibility
"""
        return base_rules + linkedin_emphasis

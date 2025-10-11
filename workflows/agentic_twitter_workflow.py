"""
Agentic Twitter Workflow - Fully autonomous tweet creation
Wraps AgenticTwitterOrchestrator to match workflow interface
"""
from .base_workflow import ContentWorkflow
import sys
import os
from typing import Dict, Any

# Add parent directory to path for agent imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from validators.twitter_validator import TwitterValidator
from agents.agentic_twitter_orchestrator import AgenticTwitterOrchestrator


class AgenticTwitterWorkflow(ContentWorkflow):
    """
    Fully agentic Twitter workflow with autonomous research and tool calling

    Flow:
    1. Autonomous format selection (paragraph, listicle, what/how/why, etc.)
    2. Research-driven generation (searches real tweets, analyzes viral patterns)
    3. Hybrid validation (code validators + LLM grading)
    4. Editing loop until quality gates pass
    """

    def __init__(self, supabase_client, airtable_client=None):
        """
        Initialize agentic Twitter workflow

        Args:
            supabase_client: Supabase client instance
            airtable_client: Airtable client (optional)
        """
        super().__init__(
            platform="twitter",
            validator_class=TwitterValidator,
            supabase_client=supabase_client
        )

        # Initialize agentic orchestrator
        self.orchestrator = AgenticTwitterOrchestrator(supabase_client, airtable_client)

    async def execute(
        self,
        brief: str,
        brand_context: str = "",
        user_id: str = "default",
        max_iterations: int = 3,
        target_score: int = 85
    ) -> Dict[str, Any]:
        """
        Execute fully agentic Twitter content creation

        Args:
            brief: Tweet topic/brief
            brand_context: Brand voice (optional - orchestrator can fetch from DB)
            user_id: User identifier
            max_iterations: Max editing iterations
            target_score: Minimum quality score (default 85)

        Returns:
            Dict with tweet, score, format, iterations, metadata
        """

        print(f"🐦 Agentic Twitter Workflow: Starting for '{brief}'")

        # Use agentic orchestrator (handles everything autonomously)
        result = await self.orchestrator.create_content(
            topic=brief,
            user_id=user_id,
            target_score=target_score,
            max_iterations=max_iterations
        )

        # Normalize result format to match workflow interface
        normalized_result = {
            'draft': result['draft'],
            'grading': result['grading'],
            'score': result['grading']['score'],
            'iterations': result['iterations'],
            'platform': 'twitter',
            'format': result.get('format', 'unknown'),
            'char_count': result.get('char_count', len(result['draft'])),
            'workflow_type': 'agentic',
            'metadata': result.get('metadata', {})
        }

        print(f"✅ Agentic Twitter Workflow: Score {normalized_result['score']}/100 in {normalized_result['iterations']} iterations")

        return normalized_result

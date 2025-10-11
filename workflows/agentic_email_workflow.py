"""
Agentic Email Workflow - Fully autonomous email creation
Wraps AgenticEmailOrchestrator to match workflow interface
Handles: Value, Indirect, and Direct emails
"""
from .base_workflow import ContentWorkflow
import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from validators.email_validator import EmailValidator
from agents.agentic_email_orchestrator import AgenticEmailOrchestrator


class AgenticEmailWorkflow(ContentWorkflow):
    """
    Fully agentic email workflow with autonomous type selection and research

    Email Types:
    1. Value - Educational (400-500 words), single tool focus
    2. Indirect - Faulty belief framework (400-600 words), case study
    3. Direct - Warm audience (100-200 words), immediate CTA
    """

    def __init__(self, supabase_client, airtable_client=None):
        """
        Initialize agentic email workflow

        Args:
            supabase_client: Supabase client instance
            airtable_client: Airtable client (optional)
        """
        super().__init__(
            platform="email",
            validator_class=EmailValidator,
            supabase_client=supabase_client
        )

        # Initialize agentic orchestrator
        self.orchestrator = AgenticEmailOrchestrator(supabase_client, airtable_client)

    async def execute(
        self,
        brief: str,
        brand_context: str = "",
        user_id: str = "default",
        max_iterations: int = 3,
        target_score: int = 85,
        email_type: str = None  # Optional: value, indirect, direct
    ) -> Dict[str, Any]:
        """
        Execute fully agentic email creation

        Args:
            brief: Email topic/brief
            brand_context: Brand voice (optional)
            user_id: User identifier
            max_iterations: Max editing iterations
            target_score: Minimum quality score (default 85)
            email_type: Optional email type (auto-selected if not provided)

        Returns:
            Dict with email, score, type, iterations, metadata
        """

        print(f"📧 Agentic Email Workflow: Starting for '{brief}'")

        # Use agentic orchestrator (handles everything autonomously)
        result = await self.orchestrator.create_content(
            topic=brief,
            user_id=user_id,
            email_type=email_type,
            target_score=target_score,
            max_iterations=max_iterations
        )

        # Normalize result format to match workflow interface
        normalized_result = {
            'draft': result['draft'],
            'grading': result['grading'],
            'score': result['grading']['score'],
            'iterations': result['iterations'],
            'platform': 'email',
            'email_type': result.get('email_type', 'unknown'),
            'word_count': result.get('word_count', len(result['draft'].split())),
            'workflow_type': 'agentic',
            'metadata': result.get('metadata', {})
        }

        print(f"✅ Agentic Email Workflow: {normalized_result['email_type']} email, Score {normalized_result['score']}/100 in {normalized_result['iterations']} iterations")

        return normalized_result

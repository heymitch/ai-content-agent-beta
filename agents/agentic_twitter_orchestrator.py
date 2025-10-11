"""
Agentic Twitter Content Orchestrator
Manages full workflow: format selection → generation → validation → editing
"""
import os
from typing import Dict, Any
from anthropic import Anthropic
from .agentic_twitter_format_generator import AgenticTwitterFormatGenerator
from validators.twitter_validator import TwitterValidator


class AgenticTwitterOrchestrator:
    """
    Fully autonomous Twitter content creation with quality gates

    Workflow:
    1. Autonomous format selection and generation (with research)
    2. Validation (hybrid: code + LLM)
    3. Editing loop until quality gates pass
    """

    def __init__(self, supabase_client=None, airtable_client=None):
        """
        Initialize orchestrator with subagents

        Args:
            supabase_client: Supabase for knowledge base
            airtable_client: Airtable for scheduling
        """
        self.format_generator = AgenticTwitterFormatGenerator()
        self.validator = TwitterValidator()
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.supabase = supabase_client
        self.airtable = airtable_client

    async def create_content(
        self,
        topic: str,
        user_id: str = "default",
        target_score: int = 85,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Create high-quality Twitter post with autonomous workflow

        Args:
            topic: Tweet topic
            user_id: User identifier
            target_score: Minimum quality score (default 85)
            max_iterations: Max editing iterations

        Returns:
            Dict with final tweet, score, format, metadata
        """
        print(f"🚀 Agentic Twitter Orchestrator: Creating post about '{topic}'")

        # Step 1: Autonomous format selection and generation
        print("📝 Step 1: Format generation with research")
        generation_result = await self.format_generator.generate(
            topic=topic,
            user_id=user_id
        )

        tweet = generation_result['tweet']
        format_type = generation_result['format']

        print(f"   Generated {format_type} format ({generation_result['char_count']} chars)")

        # Step 2: Validation & editing loop
        print(f"🎯 Step 2: Validation & editing loop (target: {target_score}+)")

        for iteration in range(max_iterations):
            # Validate
            grading = self.validator.validate(tweet, format_type)

            print(f"   Iteration {iteration + 1}: Score {grading['score']}/100")

            # Check quality gate
            if grading['score'] >= target_score:
                print(f"✅ Quality gate passed!")
                break

            # Edit if below target
            if iteration < max_iterations - 1:
                print(f"   Editing to improve score...")
                tweet = await self._edit_tweet(
                    tweet=tweet,
                    grading=grading,
                    format_type=format_type,
                    target_score=target_score
                )
            else:
                print(f"⚠️ Max iterations reached, using best attempt")

        # Final result
        final_grading = self.validator.validate(tweet, format_type)

        return {
            'draft': tweet,
            'grading': final_grading,
            'score': final_grading['score'],
            'format': format_type,
            'iterations': iteration + 1,
            'platform': 'twitter',
            'char_count': len(tweet),
            'metadata': {
                'initial_score': grading['score'] if iteration == 0 else None,
                'format_reasoning': generation_result.get('reasoning', '')
            }
        }

    async def _edit_tweet(
        self,
        tweet: str,
        grading: Dict[str, Any],
        format_type: str,
        target_score: int
    ) -> str:
        """
        Edit tweet to improve quality score

        Args:
            tweet: Current tweet text
            grading: Validation results
            format_type: Tweet format
            target_score: Target score to hit

        Returns:
            Edited tweet
        """
        edit_prompt = f"""You are editing a Twitter post to improve its quality score.

CURRENT TWEET:
{tweet}

FORMAT: {format_type}

CURRENT SCORE: {grading['score']}/100
TARGET SCORE: {target_score}+

ISSUES TO FIX:
{chr(10).join('- ' + issue for issue in grading.get('code_issues', []))}

LLM FEEDBACK:
{grading.get('llm_feedback', 'No feedback')}

IMPROVEMENTS NEEDED:
{chr(10).join('- ' + imp for imp in grading.get('improvements', []))}

RULES:
1. Must stay under 280 characters
2. Fix all code issues
3. Address LLM feedback
4. Maintain format structure
5. Keep the core message/value

Return ONLY the improved tweet text, nothing else."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": edit_prompt}]
            )

            edited_tweet = response.content[0].text.strip()

            # Remove quotes if Claude wrapped it
            if edited_tweet.startswith('"') and edited_tweet.endswith('"'):
                edited_tweet = edited_tweet[1:-1]

            # Enforce 280 char limit
            if len(edited_tweet) > 280:
                edited_tweet = edited_tweet[:277] + "..."

            return edited_tweet

        except Exception as e:
            print(f"❌ Edit error: {e}")
            return tweet  # Return original if edit fails

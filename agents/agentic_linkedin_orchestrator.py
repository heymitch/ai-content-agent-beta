"""
Agentic LinkedIn Orchestrator - Fully autonomous content creation
Intelligently uses subagents with tool calling for high-quality output
"""
from anthropic import Anthropic
import os
from typing import Dict, Any
from .agentic_hook_generator import AgenticHookGenerator
from .agentic_proof_injector import AgenticProofInjector
from .hybrid_editor import HybridEditor


class AgenticLinkedInOrchestrator:
    """
    Fully agentic LinkedIn content orchestrator
    Autonomous research, writing, and optimization
    """

    def __init__(self, supabase_client, airtable_client=None):
        self.supabase = supabase_client
        self.airtable = airtable_client
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        # Initialize agentic subagents
        self.hook_generator = AgenticHookGenerator()
        self.proof_injector = AgenticProofInjector()
        self.hybrid_editor = HybridEditor()

    async def create_content(
        self,
        topic: str,
        user_id: str = "slack_user",
        target_score: int = 85,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Autonomously create high-quality LinkedIn content

        Args:
            topic: Content topic/brief
            user_id: User identifier
            target_score: Minimum quality score (default 85)
            max_iterations: Max editing iterations (default 3)

        Returns:
            Dict with draft, score, hooks used, iterations, metadata
        """

        print(f"\n🚀 AGENTIC LINKEDIN ORCHESTRATOR")
        print(f"Topic: {topic}")
        print(f"Target Score: {target_score}+\n")

        # Step 1: Agentic hook generation (with autonomous research)
        print("🎣 STEP 1: Generating hooks with autonomous research...")
        hooks = await self.hook_generator.generate(
            topic=topic,
            user_id=user_id
        )

        best_hook = self.hook_generator.select_best_hook(hooks)
        print(f"✓ Selected: {best_hook['framework']} hook (score: {best_hook['score']}/10)")
        print(f"  '{best_hook['text'][:80]}...'\n")

        # Step 2: Draft creation with hook
        print("✍️  STEP 2: Creating initial draft...")
        draft = await self._create_draft_with_hook(
            hook=best_hook['text'],
            topic=topic,
            user_id=user_id
        )
        print(f"✓ Draft created ({len(draft)} chars)\n")

        # Step 3: Agentic proof injection (with autonomous research)
        print("💪 STEP 3: Injecting proof with autonomous research...")
        draft = await self.proof_injector.punch_up(
            draft=draft,
            topic=topic,
            user_id=user_id
        )
        print(f"✓ Proof points added\n")

        # Step 4: Validation & Editing Loop
        print("🔍 STEP 4: Validation & editing loop...")
        result = await self._editing_loop(
            draft=draft,
            topic=topic,
            target_score=target_score,
            max_iterations=max_iterations
        )

        # Add metadata
        result['hook_used'] = best_hook
        result['all_hooks'] = hooks

        print(f"\n✅ COMPLETE: Score {result['grading']['score']}/100 in {result['iterations']} iterations\n")

        return result

    async def _create_draft_with_hook(
        self,
        hook: str,
        topic: str,
        user_id: str
    ) -> str:
        """Create initial draft using hook and topic"""

        # Get brand voice
        brand_voice = await self._get_brand_voice(user_id)

        # System prompt for writer
        system_prompt = """You are a LinkedIn content writer following the Dickie Bush & Nicolas Cole system.

Your task: Write a complete LinkedIn post using this structure:

1. **Hook** (use the provided hook)
2. **Intro** (200-400 chars - expand on hook's promise)
3. **Sections** (3-5 sections with headers)
   - Use format: "Step 1:", "Stat 1:", "Mistake 1:", or "1/"
   - Each header must be tangible/specific with metrics
   - Body: 300-450 chars per section
   - Alternate bullets → paragraph → bullets
4. **Conclusion** (100-200 chars)
   - Include engagement trigger (question, request, or "Comment X")

CRITICAL RULES:
- Keep first 200 characters cliffhanger-worthy (ends with ?, :, ...)
- Short paragraphs (1-2 sentences)
- Include specific numbers from research
- Target specific audience (role + stage + problem)
- Natural voice (explaining at barbecue, not pitching)
- Total ≤ 2,800 characters

FORBIDDEN:
- No "not X but Y" contrast patterns
- No generic headers ("Here's what I learned")
- No vague audience ("founders" → "seed-stage SaaS founders")
- No AI phrases ("game-changer", "leverage", "synergy")

Return ONLY the post. No preamble, no explanation."""

        user_prompt = f"""TOPIC: {topic}

BRAND VOICE:
{brand_voice}

HOOK (already chosen):
{hook}

Write the LinkedIn post now."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text.strip()

    async def _editing_loop(
        self,
        draft: str,
        topic: str,
        target_score: int,
        max_iterations: int
    ) -> Dict[str, Any]:
        """Validation and editing loop"""

        from validators.linkedin_validator import LinkedInValidator
        from workflows.base_workflow import ContentWorkflow

        # Create validator
        validator = LinkedInValidator()

        iteration = 0
        current_draft = draft

        while iteration < max_iterations:
            # Validate
            issues = validator.validate(current_draft)

            # Grade with LLM
            grading = await self._grade_content(current_draft, issues)
            score = grading.get('score', 0)

            print(f"  Iteration {iteration + 1}: Score {score}/100")

            if score >= target_score:
                print(f"  ✓ Target reached!")
                break

            iteration += 1

            if iteration < max_iterations:
                print(f"  ↻ Editing (found {len(issues)} issues)...")

                # Use hybrid editor to fix issues
                current_draft = self.hybrid_editor.fix_issues(
                    draft=current_draft,
                    issues=issues,
                    context=topic
                )

        return {
            'draft': current_draft,
            'grading': grading,
            'iterations': iteration,
            'platform': 'linkedin'
        }

    async def _grade_content(self, content: str, code_issues: list) -> Dict:
        """Grade content with LLM"""

        grading_system = """Grade LinkedIn content on a scale of 0-100.

GRADING CRITERIA:
- Hook & First 200 chars (25 pts): Clear hook, cliffhanger
- Structure & Formatting (20 pts): Sentence headers, alternation, char limits
- Content Value (25 pts): Concrete insights, specificity
- Authenticity (20 pts): No AI artifacts, natural voice
- Engagement (10 pts): Clear CTA, discussion prompt

Return ONLY valid JSON:
{
  "score": <0-100>,
  "feedback": "<specific improvements needed>",
  "strengths": ["<what works well>"],
  "issues": ["<remaining problems>"]
}"""

        user_prompt = f"""CONTENT:
{content}

CODE ISSUES FOUND: {len(code_issues)}
{chr(10).join([f"- {issue.get('message', '')}" for issue in code_issues[:5]])}

Grade this content now."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            temperature=0.2,
            system=[
                {
                    "type": "text",
                    "text": grading_system,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse JSON
        response_text = response.content[0].text.strip()

        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        try:
            import json
            grading = json.loads(response_text)
        except:
            grading = {
                "score": 50,
                "feedback": "Error parsing grading",
                "strengths": [],
                "issues": []
            }

        grading['code_issues_remaining'] = code_issues
        return grading

    async def _get_brand_voice(self, user_id: str) -> str:
        """Get brand voice for user"""
        try:
            result = self.supabase.table('brand_voice')\
                .select('*')\
                .eq('user_id', user_id)\
                .limit(1)\
                .execute()

            if result.data:
                brand = result.data[0]
                return f"{brand.get('voice_description', 'Professional, clear, actionable')}"
            else:
                return "Professional, clear, actionable. Focus on outcomes."
        except:
            return "Professional, clear, actionable. Focus on outcomes."

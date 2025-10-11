"""
Agentic Email Orchestrator
Autonomously selects email type and generates with research
Handles: Value, Indirect, and Direct emails
"""
import os
from anthropic import Anthropic
from typing import Dict, List, Any
import json
from .email_tools import EMAIL_TOOLS, TOOL_FUNCTIONS


class AgenticEmailOrchestrator:
    """
    Fully autonomous email creation with type selection and research

    Email Types:
    1. Value - Educational, single tool focus, soft CTA (400-500 words)
    2. Indirect - Faulty belief framework, case study (400-600 words)
    3. Direct - Warm audience, immediate action (100-200 words)
    """

    def __init__(self, supabase_client=None, airtable_client=None):
        """Initialize with Anthropic client and tools"""
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.tools = EMAIL_TOOLS
        self.tool_functions = TOOL_FUNCTIONS
        self.supabase = supabase_client
        self.airtable = airtable_client

    async def create_content(
        self,
        topic: str,
        user_id: str = "default",
        email_type: str = None,  # Optional: value, indirect, direct
        target_score: int = 85,
        max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Autonomously create high-quality email with research

        Args:
            topic: Email topic/brief
            user_id: User identifier
            email_type: Optional email type (auto-selected if not provided)
            target_score: Minimum quality score
            max_iterations: Max editing iterations

        Returns:
            Dict with email, type, score, metadata
        """
        print(f"📧 Agentic Email Orchestrator: Creating email about '{topic}'")

        # Step 1: Generate email with autonomous research
        generation_result = await self._generate_with_research(
            topic=topic,
            email_type=email_type,
            user_id=user_id
        )

        email_content = generation_result['email']
        detected_type = generation_result['type']

        print(f"   Generated {detected_type} email ({generation_result['word_count']} words)")

        # Step 2: Validation & editing loop
        print(f"🎯 Validation & editing loop (target: {target_score}+)")

        from validators.email_validator import EmailValidator
        validator = EmailValidator()

        for iteration in range(max_iterations):
            # Validate
            grading = validator.validate(email_content)

            print(f"   Iteration {iteration + 1}: Score {grading['score']}/100")

            # Check quality gate
            if grading['score'] >= target_score:
                print(f"✅ Quality gate passed!")
                break

            # Edit if below target
            if iteration < max_iterations - 1:
                print(f"   Editing to improve score...")
                email_content = await self._edit_email(
                    email=email_content,
                    grading=grading,
                    email_type=detected_type,
                    target_score=target_score
                )
            else:
                print(f"⚠️ Max iterations reached, using best attempt")

        # Final grading
        final_grading = validator.validate(email_content)

        return {
            'draft': email_content,
            'grading': final_grading,
            'score': final_grading['score'],
            'email_type': detected_type,
            'iterations': iteration + 1,
            'platform': 'email',
            'word_count': len(email_content.split()),
            'metadata': {
                'initial_score': grading['score'] if iteration == 0 else None,
                'reasoning': generation_result.get('reasoning', '')
            }
        }

    async def _generate_with_research(
        self,
        topic: str,
        email_type: str = None,
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Generate email with autonomous research

        Args:
            topic: Email topic
            email_type: Optional type (auto-selected if None)
            user_id: User identifier

        Returns:
            Dict with email, type, word_count, reasoning
        """

        system_prompt = f"""You are an expert email copywriter with access to research tools.

**YOUR TASK:**
Create a high-converting email about: {topic}

**EMAIL TYPE:** {email_type if email_type else "Auto-select best type (value/indirect/direct)"}

**EMAIL TYPES:**
1. **Value Email** (400-500 words)
   - Educational, builds goodwill
   - Single tool focus (MAXIMUM 2 tools, 1 primary)
   - Personal credibility hook
   - Soft CTA
   - Use when: Teaching, demonstrating expertise

2. **Indirect Email** (400-600 words)
   - Faulty belief framework
   - Case study with specific client example
   - Challenges conventional wisdom
   - Subtle CTA
   - Use when: Educating while selling, building authority

3. **Direct Email** (100-200 words)
   - Warm audience, immediate action
   - Direct hook, clear CTA
   - Assumes interest/readiness
   - Use when: Warm leads, limited offers, following up

**YOUR PROCESS:**
1. ANALYZE topic and determine best email type (if not specified)
2. RESEARCH using tools:
   - search_email_examples: Find proven patterns
   - research_case_study_data: Get case studies (for indirect)
   - find_statistics_and_data: Support claims with data
   - get_email_best_practices: Load type-specific guidelines
3. GENERATE email following format precisely

**CRITICAL FORMATTING:**
- One sentence per line (NEVER break this rule)
- No double line breaks between sentences in paragraphs
- Single line break between related sentences
- Double line break only between major sections
- Use `{{app_cta}}` or `{{call_cta}}` for CTAs

**VOICE:**
- Conversational teacher, not salesy
- Specific over generic
- Personal experience
- Direct and helpful

**OUTPUT JSON:**
{{
  "type": "value|indirect|direct",
  "email": "Full email text with proper formatting",
  "subject": "Subject line",
  "reasoning": "Why this type and approach",
  "word_count": 450
}}
"""

        messages = [
            {"role": "user", "content": f"Create email about: {topic}"}
        ]

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,  # Emails need more tokens
                system=system_prompt,
                messages=messages,
                tools=self.tools
            )

            if response.stop_reason == "tool_use":
                print(f"🔧 Iteration {iteration}: Using research tools")

                # Execute tools
                tool_results = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input

                        print(f"   Calling {tool_name}...")

                        try:
                            result = self.tool_functions[tool_name](**tool_input)
                        except Exception as e:
                            result = f"Error: {str(e)}"

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": result
                        })

                # Add to conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            else:
                # Final response
                print(f"✅ Iteration {iteration}: Email generated")

                # Extract JSON
                response_text = ""
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        response_text += content_block.text

                # Parse JSON
                try:
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()
                    elif "```" in response_text:
                        json_start = response_text.find("```") + 3
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()

                    result = json.loads(response_text)

                    return {
                        'email': result.get('email', ''),
                        'type': result.get('type', 'value'),
                        'subject': result.get('subject', ''),
                        'reasoning': result.get('reasoning', ''),
                        'word_count': len(result.get('email', '').split())
                    }

                except json.JSONDecodeError as e:
                    print(f"❌ JSON parse error: {e}")
                    # Fallback: use raw text
                    return {
                        'email': response_text,
                        'type': email_type or 'value',
                        'subject': '',
                        'reasoning': 'JSON parse failed - using raw text',
                        'word_count': len(response_text.split())
                    }

        # Max iterations
        return {
            'email': f"Error: Failed to generate email after {max_iterations} iterations",
            'type': 'error',
            'subject': '',
            'reasoning': 'Max iterations exceeded',
            'word_count': 0
        }

    async def _edit_email(
        self,
        email: str,
        grading: Dict[str, Any],
        email_type: str,
        target_score: int
    ) -> str:
        """
        Edit email to improve quality score

        Args:
            email: Current email text
            grading: Validation results
            email_type: Email type
            target_score: Target score

        Returns:
            Edited email
        """
        edit_prompt = f"""Edit this email to improve quality score.

CURRENT EMAIL:
{email}

TYPE: {email_type}

CURRENT SCORE: {grading['score']}/100
TARGET: {target_score}+

ISSUES:
{chr(10).join('- ' + issue for issue in grading.get('code_issues', []))}

FEEDBACK:
{grading.get('llm_feedback', 'No feedback')}

IMPROVEMENTS NEEDED:
{chr(10).join('- ' + imp for imp in grading.get('improvements', []))}

RULES:
1. Fix all code issues
2. Maintain email type structure
3. Keep one sentence per line
4. Address all feedback
5. Preserve core message

Return ONLY the improved email, nothing else."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": edit_prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            print(f"❌ Edit error: {e}")
            return email  # Return original if edit fails

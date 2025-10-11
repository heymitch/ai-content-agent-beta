"""
Proof Injector: Adds specificity, numbers, and concrete examples to drafts
Replaces vague claims with research data and tangible proof points
"""
from anthropic import Anthropic
import os
from typing import Dict


class ProofInjector:
    """Add proof points and specificity to content"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def punch_up(
        self,
        draft: str,
        research_data: str = "",
        rag_examples: str = "",
        context: str = ""
    ) -> str:
        """
        Add proof points and specificity to draft

        Args:
            draft: Current draft text
            research_data: Web search results or research findings
            rag_examples: Examples from knowledge base
            context: Original brief/topic

        Returns:
            Punched-up draft with specific numbers and examples
        """

        # Static system instructions (cacheable)
        system_instructions = """You are a LinkedIn content editor specializing in adding proof and specificity.

Your task: "Punch up" the draft by adding:
1. **Specific numbers** instead of vague claims
   - Replace "significant improvement" with "41 to 23 days"
   - Replace "a lot of revenue" with "$100k in pipeline"
   - Replace "many customers" with "500+ customers"

2. **Concrete examples** from research or RAG
   - Add real company names, tools, or case studies
   - Include specific metrics or outcomes
   - Reference tangible proof points

3. **Tangible details** in every section
   - Time frames ("in 21 days", "within 30-day sprint")
   - Dollar amounts ("$15K saved", "$3M generated")
   - Percentages ("+40% clicks", "73% from referrals")
   - Scale ("2,847 emails", "12-minute demo")

RULES:
- Keep the overall structure and flow intact
- Add proof WITHOUT making it longer (replace vague with specific)
- Only use numbers/examples from the research data provided
- If no research data, use placeholder metrics like "[X days]" or "[Y%]"
- Maintain natural voice - don't sound robotic or salesy

FORBIDDEN:
- Don't add generic claims ("game-changer", "revolutionary")
- Don't fabricate numbers not in research data
- Don't make it wordier - replace, don't add

Return ONLY the punched-up draft. No preamble, no explanation."""

        # Dynamic user content
        user_prompt = f"""ORIGINAL CONTEXT:
{context}

CURRENT DRAFT:
{draft}

RESEARCH DATA (use this to add specificity):
{research_data if research_data else "No research data provided."}

EXAMPLES FROM KNOWLEDGE BASE:
{rag_examples if rag_examples else "No examples provided."}

Punch up the draft now."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=[
                    {
                        "type": "text",
                        "text": system_instructions,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )

            punched_up = response.content[0].text.strip()
            return punched_up

        except Exception as e:
            print(f"❌ Proof injection error: {e}")
            return draft  # Return unchanged if fails


# Convenience function
def add_proof(
    draft: str,
    research_data: str = "",
    rag_examples: str = "",
    context: str = ""
) -> str:
    """Add proof points to draft"""
    injector = ProofInjector()
    return injector.punch_up(draft, research_data, rag_examples, context)

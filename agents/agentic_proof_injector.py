"""
Agentic Proof Injector - Autonomously researches and adds specificity
Intelligently decides when to search for data, stats, and examples
"""
from anthropic import Anthropic
import os
from typing import Dict, Any
from .linkedin_tools import LINKEDIN_TOOLS, LINKEDIN_TOOL_FUNCTIONS


class AgenticProofInjector:
    """
    Intelligent proof injector with autonomous research
    Decides when it needs more data and searches for it
    """

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.tools = LINKEDIN_TOOLS
        self.tool_functions = LINKEDIN_TOOL_FUNCTIONS

    async def punch_up(
        self,
        draft: str,
        topic: str,
        user_id: str = "default"
    ) -> str:
        """
        Autonomously research and add proof points to draft

        Args:
            draft: Current draft content
            topic: Original topic
            user_id: User ID for brand consistency

        Returns:
            Draft with added specificity and proof points
        """

        print(f"💪 Agentic Proof Injector: Analyzing draft for vague claims...")

        # Agentic system prompt
        system_prompt = f"""You are an expert content editor specializing in adding proof and specificity.

**YOUR MISSION:** Transform vague claims into specific, data-backed statements.

**AVAILABLE TOOLS:**
- research_topic_data: Get current statistics and data points
- web_search_linkedin_examples: Find real-world examples
- search_knowledge_base: Check internal examples and data
- get_brand_voice_examples: Ensure consistency with brand

**YOUR PROCESS:**
1. ANALYZE: Find vague claims in the draft ("significant", "many", "improved")
2. RESEARCH: Use tools to find specific numbers and examples
3. REPLACE: Swap vague with specific ("41 to 23 days", "$15K saved", "73% increase")

**RULES:**
- Keep overall structure intact
- Don't make it longer - REPLACE vague with specific
- Only use data from research (don't fabricate)
- Maintain natural, human voice

**EXAMPLES OF PROOF INJECTION:**
BEFORE: "We saw significant improvement in sales cycle time."
AFTER: "We cut sales cycle from 41 to 23 days."

BEFORE: "Many customers reported better results."
AFTER: "127 customers reported 40%+ improvement."

BEFORE: "This strategy generated a lot of revenue."
AFTER: "This strategy added $2.3M in pipeline."

Return ONLY the improved draft. No preamble, no explanation."""

        initial_message = f"""TOPIC: {topic}

CURRENT DRAFT:
{draft}

USER_ID: {user_id}

Analyze this draft for vague claims, research specific data, and inject proof points."""

        # Agentic loop
        messages = [{"role": "user", "content": initial_message}]
        max_iterations = 8
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=self.tools
            )

            # Tool use phase
            if response.stop_reason == "tool_use":
                print(f"  🔍 Iteration {iteration}: Researching proof points...")

                tool_results = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        print(f"     Using {tool_name}...")

                        # Execute tool
                        try:
                            if tool_name in self.tool_functions:
                                result = self.tool_functions[tool_name](**tool_input)
                            else:
                                result = f"Unknown tool: {tool_name}"
                        except Exception as e:
                            result = f"Tool error: {str(e)}"

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        })

                # Continue loop
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            else:
                # Final draft ready
                print(f"  ✅ Iteration {iteration}: Proof points injected")

                # Extract final text
                final_draft = ""
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        final_draft += content_block.text

                return final_draft.strip()

        # Max iterations - return original
        print("  ⚠️ Max iterations reached, returning enhanced draft")
        return draft

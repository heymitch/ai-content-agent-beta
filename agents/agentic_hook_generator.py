"""
Agentic Hook Generator - Autonomously researches and creates optimal hooks
Uses Claude Agent SDK patterns for intelligent, tool-enabled hook generation
"""
from anthropic import Anthropic
import os
import json
from typing import List, Dict, Any
from .linkedin_tools import LINKEDIN_TOOLS, LINKEDIN_TOOL_FUNCTIONS


class AgenticHookGenerator:
    """
    Intelligent hook generator with autonomous research capabilities
    Decides when to search examples, research data, or analyze competitors
    """

    HOOK_FRAMEWORKS = """
    1. **Question Hook** (provokes curiosity)
    2. **Bold Statement Hook** (counter-intuitive claim)
    3. **Specific Number/Stat Hook** (data-driven opener)
    4. **Short Story Opener** (personal narrative)
    5. **Mistake/Lesson Framing** (vulnerability + insight)
    """

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.tools = LINKEDIN_TOOLS
        self.tool_functions = LINKEDIN_TOOL_FUNCTIONS

    async def generate(
        self,
        topic: str,
        user_id: str = "default",
        brand_voice: str = "",
        context: str = ""
    ) -> List[Dict]:
        """
        Autonomously generate 5 optimal hooks using tools and research

        Args:
            topic: Content topic/brief
            user_id: User ID for brand voice
            brand_voice: Brand voice guidelines (optional, will fetch if not provided)
            context: Additional context

        Returns:
            List of 5 hooks with framework, text, score, reasoning
        """

        print(f"🎣 Agentic Hook Generator: Researching '{topic}'")

        # Build agentic prompt
        system_prompt = f"""You are an expert LinkedIn hook generator with access to research tools.

**YOUR MISSION:** Generate 5 high-performing hooks for this topic: "{topic}"

**AVAILABLE TOOLS:**
- web_search_linkedin_examples: Find viral LinkedIn posts on this topic
- research_topic_data: Get statistics and data points to use in hooks
- analyze_competitor_posts: See how competitors approach this topic
- search_knowledge_base: Find brand-specific examples and guidelines
- get_brand_voice_examples: Understand the user's brand voice

**YOUR PROCESS:**
1. THINK: What information would make these hooks more specific and compelling?
2. USE TOOLS: Autonomously decide which tools to call for research
3. ANALYZE: Review research to find the best angles
4. GENERATE: Create 5 hooks using different frameworks

**HOOK FRAMEWORKS:**
{self.HOOK_FRAMEWORKS}

Generate ONE hook for EACH framework. Make them:
- Specific (use numbers, metrics, tangible details from research)
- Provocative (challenge assumptions, create curiosity)
- Under 200 characters
- Human-sounding (not AI-generated)

**OUTPUT FORMAT:**
Return ONLY valid JSON:
{{
  "hooks": [
    {{
      "framework": "question",
      "text": "Your hook ending with cliffhanger:",
      "score": 8.5,
      "reasoning": "Why this hook works based on research"
    }},
    ... (5 total hooks)
  ]
}}

Be proactive with tools. Don't ask - just use them when they'll improve the hooks."""

        initial_message = f"""Topic: {topic}

User ID: {user_id}
Brand Voice: {brand_voice if brand_voice else "(will fetch)"}
Context: {context if context else "(none)"}

Research and generate 5 optimal hooks now."""

        # Agentic loop
        messages = [{"role": "user", "content": initial_message}]
        max_iterations = 10
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

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                print(f"  🔧 Iteration {iteration}: Using research tools...")

                # Execute tools
                tool_results = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        print(f"     Calling {tool_name}({tool_input})")

                        # Execute
                        try:
                            if tool_name in self.tool_functions:
                                result = self.tool_functions[tool_name](**tool_input)
                            else:
                                result = f"Unknown tool: {tool_name}"
                        except Exception as e:
                            result = f"Tool error: {str(e)}"

                        print(f"     → {len(result)} chars of research data")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        })

                # Continue conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            else:
                # Final answer ready
                print(f"  ✅ Iteration {iteration}: Hooks generated")

                # Extract JSON from response
                response_text = ""
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        response_text += content_block.text

                # Parse JSON
                try:
                    # Clean potential markdown
                    if "```json" in response_text:
                        response_text = response_text.split("```json")[1].split("```")[0]
                    elif "```" in response_text:
                        response_text = response_text.split("```")[1].split("```")[0]

                    data = json.loads(response_text.strip())
                    hooks = data.get('hooks', [])

                    if len(hooks) == 5:
                        return hooks
                    else:
                        print(f"  ⚠️ Got {len(hooks)} hooks instead of 5, using what we have")
                        return hooks

                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON parse error: {e}")
                    print(f"  Response: {response_text[:200]}")

                    # Fallback: Return basic hooks
                    return self._generate_fallback_hooks(topic)

        # Max iterations - use fallback
        print("  ⚠️ Max iterations reached, using fallback hooks")
        return self._generate_fallback_hooks(topic)

    def _generate_fallback_hooks(self, topic: str) -> List[Dict]:
        """Generate basic hooks without agentic research (fallback)"""
        return [
            {
                "framework": "question",
                "text": f"What if your approach to {topic} is backwards?",
                "score": 6.0,
                "reasoning": "Fallback hook - minimal research"
            },
            {
                "framework": "bold_statement",
                "text": f"Most advice about {topic} is wrong. Here's why:",
                "score": 6.0,
                "reasoning": "Fallback hook - minimal research"
            },
            {
                "framework": "stat",
                "text": f"I analyzed 100+ examples of {topic}. The pattern was clear:",
                "score": 6.0,
                "reasoning": "Fallback hook - minimal research"
            },
            {
                "framework": "story",
                "text": f"Last month I completely changed how I think about {topic}.",
                "score": 6.0,
                "reasoning": "Fallback hook - minimal research"
            },
            {
                "framework": "mistake",
                "text": f"I wasted 6 months on {topic} before learning this:",
                "score": 6.0,
                "reasoning": "Fallback hook - minimal research"
            }
        ]

    def select_best_hook(self, hooks: List[Dict]) -> Dict:
        """Select the highest-scoring hook"""
        if not hooks:
            return self._generate_fallback_hooks("your topic")[0]

        return max(hooks, key=lambda h: h.get('score', 0))

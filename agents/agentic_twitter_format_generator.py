"""
Agentic Twitter Format Generator
Autonomously selects optimal format and researches examples before generating
"""
import os
from anthropic import Anthropic
from typing import Dict, List, Any
import json
from .twitter_tools import TWITTER_TOOLS, TOOL_FUNCTIONS


class AgenticTwitterFormatGenerator:
    """
    Autonomously selects best Twitter format and generates post with research

    Formats supported:
    1. Paragraph Style - declarative perspective
    2. What/How/Why - hook + bullets + closing
    3. Listicle - tips, tools, books, etc.
    4. Old vs New - comparing approaches
    5. 10 Magical Ways - proven topics
    """

    def __init__(self):
        """Initialize with Anthropic client and tools"""
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.tools = TWITTER_TOOLS
        self.tool_functions = TOOL_FUNCTIONS

    async def generate(self, topic: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Autonomously select format, research examples, and generate tweet

        Args:
            topic: Tweet topic
            user_id: User identifier for brand voice

        Returns:
            Dict with format, tweet text, research used
        """
        print(f"🐦 Agentic Twitter Format Generator: Starting for '{topic}'")

        system_prompt = """You are an expert Twitter/X content strategist with access to research tools.

**YOUR PROCESS:**

1. **ANALYZE TOPIC** - Understand the topic and determine best format:
   - Paragraph: For opinions, perspectives, insights
   - What/How/Why: For actionable advice, frameworks, steps
   - Listicle: For tips, tools, resources, books
   - Old vs New: For contrasts, comparisons, evolution
   - 10 Magical Ways: For benefits, reasons, mistakes, questions

2. **RESEARCH** - Use tools to find proven patterns:
   - web_search_twitter_examples: Find real successful tweets on topic
   - analyze_viral_tweets: Understand what drives engagement
   - get_format_best_practices: Load format guidelines
   - search_knowledge_base_twitter: Find internal examples

3. **GENERATE** - Create one tweet following format rules:
   - Must fit 280 characters (be strict about this)
   - Follow format best practices exactly
   - Use insights from research
   - Be specific, tangible, actionable
   - Strong hook if applicable
   - No hashtags unless natural

**AVAILABLE TOOLS:**
You have access to research tools. Use them autonomously to create better content.

**OUTPUT FORMAT:**
When ready, return JSON:
{
  "format": "paragraph|what_how_why|listicle|old_vs_new|magical_ways",
  "tweet": "The actual tweet text (max 280 chars)",
  "reasoning": "Why this format and approach"
}
"""

        messages = [
            {
                "role": "user",
                "content": f"Create a high-quality Twitter post about: {topic}"
            }
        ]

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

            # Check if Claude wants to use tools
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
                # Final response ready
                print(f"✅ Iteration {iteration}: Tweet generated")

                # Extract JSON from response
                response_text = ""
                for content_block in response.content:
                    if hasattr(content_block, "text"):
                        response_text += content_block.text

                # Parse JSON
                try:
                    # Extract JSON from markdown code blocks if present
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()
                    elif "```" in response_text:
                        json_start = response_text.find("```") + 3
                        json_end = response_text.find("```", json_start)
                        response_text = response_text[json_start:json_end].strip()

                    result = json.loads(response_text)

                    # Validate
                    if 'tweet' not in result:
                        raise ValueError("Missing 'tweet' field")

                    # Check length
                    if len(result['tweet']) > 280:
                        print(f"⚠️ Tweet too long ({len(result['tweet'])} chars), truncating")
                        result['tweet'] = result['tweet'][:277] + "..."

                    return {
                        'format': result.get('format', 'unknown'),
                        'tweet': result['tweet'],
                        'reasoning': result.get('reasoning', ''),
                        'char_count': len(result['tweet'])
                    }

                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON: {e}")
                    # Fallback: treat entire response as tweet
                    tweet_text = response_text.strip()
                    if len(tweet_text) > 280:
                        tweet_text = tweet_text[:277] + "..."

                    return {
                        'format': 'unknown',
                        'tweet': tweet_text,
                        'reasoning': 'Fallback mode - JSON parse failed',
                        'char_count': len(tweet_text)
                    }

        # Max iterations reached
        return {
            'format': 'error',
            'tweet': f"Error: Failed to generate tweet after {max_iterations} iterations",
            'reasoning': 'Max iterations exceeded',
            'char_count': 0
        }

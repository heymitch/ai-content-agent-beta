"""
LinkedIn Hook Generator
Generates 5 hooks using proven frameworks from Dickie Bush & Nicolas Cole
"""
from anthropic import Anthropic
import os
import json
from typing import List, Dict


class LinkedInHookGenerator:
    """Generate 5 hooks using proven frameworks"""

    HOOK_FRAMEWORKS = """
    1. **Question Hook** (provokes curiosity)
       - ✅ "You can add $100k in pipeline without posting daily—want the 3 plays we use?"
       - ✅ "What if your activation email is the reason 60% of users never return?"
       - ❌ "Have you ever thought about LinkedIn?" (too generic)

    2. **Bold Statement Hook** (counter-intuitive claim)
       - ✅ "Your ICP is too broad. Here's the 3-question test that cut our sales cycle by 40%:"
       - ✅ "I spent $50K on ads before realizing the real problem was my homepage."
       - ❌ "LinkedIn is important for business." (obvious, not bold)

    3. **Specific Number/Stat Hook** (data-driven opener)
       - ✅ "Last quarter we cut sales cycle time from 41 to 23 days. The lever wasn't headcount or ad spend…"
       - ✅ "2,847 cold emails. 3 meetings. Here's what I changed:"
       - ❌ "I sent a lot of emails and got some results." (vague, no numbers)

    4. **Short Story Opener** (personal narrative)
       - ✅ "I walked into our Q3 review with a 12% activation rate. My CEO gave me 30 days to fix it."
       - ✅ "The day I got fired for missing quota taught me more than 4 years of hitting it."
       - ❌ "I learned something interesting recently." (generic setup)

    5. **Mistake/Lesson Framing** (vulnerability + insight)
       - ✅ "I lost $15K on my second property deal because I skipped this one due diligence step:"
       - ✅ "For 6 months I optimized the wrong metric. Here's how I figured it out:"
       - ❌ "I made mistakes and learned from them." (vague, no specifics)
    """

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def generate(self, topic: str, brand_voice: str = "", context: str = "") -> List[Dict]:
        """
        Generate 5 hooks using proven frameworks

        Args:
            topic: Content topic/brief
            brand_voice: Brand voice guidelines
            context: Additional context (research, examples)

        Returns:
            List of 5 hooks with type, text, and score
        """

        # Static system instructions (cacheable)
        system_instructions = f"""You are a LinkedIn content strategist specializing in high-performing hooks.

Your task: Generate 5 hooks using the proven frameworks below. Each hook must:
- Be specific (include numbers, metrics, or tangible details)
- Provoke curiosity or challenge assumptions
- Be under 200 characters (room for cliffhanger)
- Sound like a human expert, not AI-generated

{self.HOOK_FRAMEWORKS}

Generate one hook for EACH of the 5 frameworks above.

For each hook, also:
1. Score it 0-10 based on specificity, curiosity, and authenticity
2. Explain why it works (or doesn't)

Return ONLY valid JSON in this exact format:
{{
  "hooks": [
    {{
      "framework": "question",
      "text": "Your hook text here ending with cliffhanger:",
      "score": 8.5,
      "reasoning": "Why this hook works or needs improvement"
    }},
    {{
      "framework": "bold_statement",
      "text": "Your hook text here:",
      "score": 9.0,
      "reasoning": "Why this hook works"
    }},
    {{
      "framework": "stat",
      "text": "Your hook with specific number:",
      "score": 8.0,
      "reasoning": "Why this hook works"
    }},
    {{
      "framework": "story",
      "text": "Your story opener:",
      "score": 7.5,
      "reasoning": "Why this hook works"
    }},
    {{
      "framework": "mistake",
      "text": "Your mistake/lesson hook:",
      "score": 8.5,
      "reasoning": "Why this hook works"
    }}
  ]
}}

CRITICAL: Return ONLY the JSON. No preamble, no explanation outside the JSON."""

        # Dynamic user content
        user_prompt = f"""TOPIC: {topic}

BRAND VOICE:
{brand_voice if brand_voice else "Professional, clear, actionable. Focus on outcomes."}

CONTEXT:
{context if context else "No additional context provided."}

Generate the 5 hooks now."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
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

            # Parse JSON response
            result_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:].strip()

            result = json.loads(result_text)

            return result['hooks']

        except Exception as e:
            print(f"❌ Hook generation error: {e}")
            # Return fallback hooks
            return self._fallback_hooks(topic)

    def select_best_hook(self, hooks: List[Dict]) -> Dict:
        """Select the hook with highest score"""
        return max(hooks, key=lambda h: h['score'])

    def _fallback_hooks(self, topic: str) -> List[Dict]:
        """Fallback hooks if generation fails"""
        return [
            {
                "framework": "question",
                "text": f"Want to master {topic}? Here's what nobody tells you:",
                "score": 6.0,
                "reasoning": "Generic fallback - needs more specificity"
            },
            {
                "framework": "bold_statement",
                "text": f"Most people get {topic} wrong. Here's why:",
                "score": 6.5,
                "reasoning": "Generic fallback - needs counter-intuitive angle"
            },
            {
                "framework": "stat",
                "text": f"I spent 6 months learning {topic}. Here's what worked:",
                "score": 7.0,
                "reasoning": "Has timeframe but needs specific metrics"
            },
            {
                "framework": "story",
                "text": f"Last year I failed at {topic}. Here's what I learned:",
                "score": 6.5,
                "reasoning": "Generic fallback - needs specific stakes"
            },
            {
                "framework": "mistake",
                "text": f"I wasted time on {topic} by making this mistake:",
                "score": 6.0,
                "reasoning": "Generic fallback - needs tangible cost"
            }
        ]


# Convenience function for direct use
def generate_hooks(topic: str, brand_voice: str = "", context: str = "") -> List[Dict]:
    """Generate 5 hooks for a LinkedIn post"""
    generator = LinkedInHookGenerator()
    return generator.generate(topic, brand_voice, context)


def get_best_hook(topic: str, brand_voice: str = "", context: str = "") -> Dict:
    """Generate 5 hooks and return the best one"""
    generator = LinkedInHookGenerator()
    hooks = generator.generate(topic, brand_voice, context)
    return generator.select_best_hook(hooks)

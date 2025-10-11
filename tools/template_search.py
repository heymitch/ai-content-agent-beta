"""
Template search tool for finding content templates using agentic reasoning
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from anthropic import Anthropic

def load_all_templates() -> List[Dict[str, Any]]:
    """Load all JSON templates from templates/ directory"""
    templates = []
    templates_dir = Path(__file__).parent.parent / "templates"

    for json_file in templates_dir.rglob("*.json"):
        try:
            with open(json_file, 'r') as f:
                template = json.load(f)
                template['_file_path'] = str(json_file.relative_to(templates_dir))
                templates.append(template)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    return templates


def search_templates_agentic(user_intent: str, max_results: int = 3) -> str:
    """
    Search templates using Claude's reasoning to match user intent

    Args:
        user_intent: User's request (e.g., "teach people about MCP", "compare old vs new approach")
        max_results: Number of templates to return

    Returns:
        Formatted string with top matching templates selected by Claude
    """
    templates = load_all_templates()

    if not templates:
        return "❌ No templates found in templates/ directory"

    # Initialize Anthropic client
    client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # Create compact template summaries for Claude
    template_summaries = []
    for t in templates:
        summary = {
            'name': t.get('name', 'Unnamed'),
            'platform': t.get('platform', 'N/A'),
            'description': t.get('description', 'No description'),
            'use_when': t.get('use_when', [])[:3],  # First 3 use cases
            'file': t.get('_file_path', 'Unknown')
        }
        template_summaries.append(summary)

    # Prompt for Claude to reason about best matches
    prompt = f"""You are a content strategy expert helping match user intent to content templates.

User wants: "{user_intent}"

Available templates:
{json.dumps(template_summaries, indent=2)}

Analyze the user's intent and select the top {max_results} templates that best match what they're trying to accomplish.

Consider:
1. What format best fits their goal (list, comparison, long-form, story, etc.)
2. The use cases listed for each template
3. Whether they want to teach, compare, test ideas, or tell stories
4. The platform (LinkedIn, email, Twitter) if they specified one

Return ONLY valid JSON (no markdown, no explanation) in this exact format:
{{
  "matches": [
    {{
      "name": "Template Name",
      "reasoning": "One sentence explaining why this fits",
      "confidence": 0.95
    }}
  ]
}}

Select exactly {max_results} templates, ranked by best match first."""

    try:
        # Call Claude for reasoning
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            temperature=0.3,  # Lower temp for consistent matching
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse Claude's response
        response_text = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]

        matches = json.loads(response_text)

        # Build output with Claude's reasoning
        output = f"📚 Claude selected {len(matches['matches'])} template(s) for: '{user_intent}'\n\n"

        for i, match in enumerate(matches['matches'], 1):
            # Find full template by name
            template = next((t for t in templates if t.get('name', '').lower() == match['name'].lower()), None)

            if template:
                output += f"**{i}. {template['name']}** (Confidence: {int(match.get('confidence', 0.8) * 100)}%)\n"
                output += f"   Platform: {template.get('platform', 'N/A')}\n"
                output += f"   Why: {match.get('reasoning', 'Good match')}\n"
                output += f"   File: {template.get('_file_path', 'Unknown')}\n\n"

        return output

    except Exception as e:
        # Fallback to simple keyword matching if Claude fails
        print(f"⚠️ Agentic search failed ({e}), falling back to keyword matching")
        return _fallback_keyword_search(user_intent, templates, max_results)


def _fallback_keyword_search(user_intent: str, templates: List[Dict], max_results: int = 3) -> str:
    """Simple keyword matching fallback"""
    results = []
    intent_lower = user_intent.lower()

    for template in templates:
        score = 0
        search_text = ""

        if 'description' in template:
            search_text += template['description'].lower() + " "
        if 'use_when' in template and isinstance(template['use_when'], list):
            search_text += " ".join(template['use_when']).lower()

        for word in intent_lower.split():
            if len(word) > 3 and word in search_text:
                score += 1

        if score > 0:
            results.append({'template': template, 'score': score})

    results.sort(key=lambda x: x['score'], reverse=True)
    top_results = results[:max_results]

    if not top_results:
        return f"❌ No templates found matching: '{user_intent}'"

    output = f"📚 Found {len(top_results)} template(s) matching: '{user_intent}'\n\n"
    for i, result in enumerate(top_results, 1):
        t = result['template']
        output += f"**{i}. {t.get('name', 'Unnamed')}**\n"
        output += f"   Platform: {t.get('platform', 'N/A')}\n"
        output += f"   Description: {t.get('description', 'No description')}\n\n"

    return output


# Keep the old name for backward compatibility
search_templates_semantic = search_templates_agentic


def get_template_by_name(template_name: str) -> str:
    """
    Get full template structure by name

    Args:
        template_name: Name of template (e.g., "Outline As Content")

    Returns:
        Full JSON template as formatted string
    """
    templates = load_all_templates()

    name_lower = template_name.lower()

    for template in templates:
        if template.get('name', '').lower() == name_lower:
            return json.dumps(template, indent=2)

    return f"❌ Template not found: '{template_name}'\n\nAvailable templates:\n" + \
           "\n".join([f"• {t.get('name', 'Unnamed')}" for t in templates])


# For testing
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test 1: Search for teaching content
    print("Test 1: Agentic search - 'I want to teach people about a framework I use'")
    print(search_templates_agentic("I want to teach people about a framework I use", max_results=3))
    print("\n" + "="*80 + "\n")

    # Test 2: Search for comparison
    print("Test 2: Agentic search - 'compare the old way vs new way'")
    print(search_templates_agentic("compare the old way vs new way", max_results=3))
    print("\n" + "="*80 + "\n")

    # Test 3: Search for quick test
    print("Test 3: Agentic search - 'I have an idea and want to test it quickly'")
    print(search_templates_agentic("I have an idea and want to test it quickly", max_results=3))

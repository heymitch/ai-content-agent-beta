"""
Principle-based RAG search - finds structural patterns, not topic matches
Use case: Extract writing principles applicable to ANY industry/topic
"""

import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))


def search_by_principle(
    principle: str,
    platform: Optional[str] = None,
    match_count: int = 5,
    match_threshold: float = 0.60
) -> str:
    """
    Search for content examples by WRITING PRINCIPLE (not topic)

    Principle Types:
    - Structure: "listicle 7-10 items", "personal story with lesson", "contrarian take"
    - Hook: "number transformation hook", "mistake admission", "bold claim"
    - Voice: "vulnerable authentic", "direct no fluff", "conversational funny"
    - Format: "thread with recap", "atomic essay", "long-form storytelling"

    Args:
        principle: Writing principle to search for (structure, hook, voice, format)
        platform: Filter by platform (LinkedIn, X, YouTube, etc.)
        match_count: Number of examples to return
        match_threshold: Similarity threshold (0.60 = good for principles)

    Returns:
        JSON string with matched examples

    Example:
        # Find listicle structure (works for ANY topic)
        search_by_principle("listicle with 7 items numbered list", platform="LinkedIn")

        # Find vulnerability hook pattern (works for ANY topic)
        search_by_principle("hook that admits mistakes or failures vulnerable", platform="X")
    """
    try:
        # Generate embedding for principle query
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=principle
        )
        query_embedding = response.data[0].embedding

        # Search examples
        result = supabase.rpc(
            'match_content_examples',
            {
                'query_embedding': query_embedding,
                'filter_platform': platform,
                'match_threshold': match_threshold,
                'match_count': match_count
            }
        ).execute()

        # Extract principles from examples
        examples_with_principles = []
        for match in result.data:
            examples_with_principles.append({
                'id': match['id'],
                'platform': match['platform'],
                'content': match['content'],
                'hook_line': match['hook_line'],
                'content_type': match['content_type'],
                'similarity': match['similarity'],

                # Extracted principles
                'principles': extract_principles_from_content(match)
            })

        return json.dumps({
            'success': True,
            'principle_query': principle,
            'platform_filter': platform,
            'matches': examples_with_principles,
            'count': len(examples_with_principles)
        }, indent=2)

    except Exception as e:
        return json.dumps({
            'error': str(e),
            'principle_query': principle
        })


def extract_principles_from_content(example: Dict) -> Dict:
    """
    Extract reusable writing principles from content example
    Returns principles that work for ANY topic/industry
    """
    content = example.get('content', '')
    hook = example.get('hook_line', '')

    principles = {}

    # Hook structure
    principles['hook_structure'] = analyze_hook_structure(hook)

    # Body structure
    principles['body_structure'] = analyze_body_structure(content)

    # Voice style
    principles['voice_style'] = analyze_voice_style(content)

    # Formatting patterns
    principles['formatting'] = analyze_formatting(content)

    return principles


def analyze_hook_structure(hook: str) -> Dict:
    """Analyze hook pattern (works across topics)"""
    if not hook:
        return {}

    patterns = {}

    # Check for numbers
    import re
    numbers = re.findall(r'\d+', hook)
    if numbers:
        patterns['uses_numbers'] = True
        patterns['number_count'] = len(numbers)

    # Check for transformation pattern (X → Y)
    if '→' in hook or ' to ' in hook.lower() or ' from ' in hook.lower():
        patterns['transformation_hook'] = True

    # Check for question
    if '?' in hook:
        patterns['question_hook'] = True

    # Check for "I" statement (personal)
    if hook.startswith('I ') or ' I ' in hook:
        patterns['first_person'] = True

    # Check for bold claim
    bold_words = ['never', 'always', 'every', 'no one', 'everyone', 'best', 'worst']
    if any(word in hook.lower() for word in bold_words):
        patterns['bold_claim'] = True

    # Length
    patterns['word_count'] = len(hook.split())
    patterns['character_count'] = len(hook)

    return patterns


def analyze_body_structure(content: str) -> Dict:
    """Analyze body structure (works across topics)"""
    if not content:
        return {}

    structure = {}

    # Check for list/numbered items
    lines = content.split('\n')
    bullets = sum(1 for line in lines if line.strip().startswith(('•', '-', '*', '1.', '2.', '3.')))

    if bullets >= 3:
        structure['list_format'] = True
        structure['list_item_count'] = bullets

    # Check for sections (headers)
    headers = sum(1 for line in lines if line.strip().startswith('#'))
    if headers > 0:
        structure['has_sections'] = True
        structure['section_count'] = headers

    # Paragraph count
    paragraphs = [p for p in content.split('\n\n') if p.strip()]
    structure['paragraph_count'] = len(paragraphs)

    # Average sentence length
    sentences = content.count('.') + content.count('!') + content.count('?')
    if sentences > 0:
        avg_words_per_sentence = len(content.split()) / sentences
        structure['avg_sentence_length'] = round(avg_words_per_sentence, 1)

    # Length metrics
    structure['total_words'] = len(content.split())
    structure['total_characters'] = len(content)

    return structure


def analyze_voice_style(content: str) -> Dict:
    """Analyze voice/tone (works across topics)"""
    if not content:
        return {}

    voice = {}

    # Personal vs impersonal
    first_person_count = content.lower().count(' i ') + content.lower().count('my ') + content.lower().count("i'm")
    voice['first_person_usage'] = first_person_count
    voice['is_personal'] = first_person_count > 3

    # Conversational markers
    conversational = ['but', 'and', 'so', 'well', 'now', 'here\'s']
    conv_count = sum(content.lower().count(word) for word in conversational)
    voice['conversational_score'] = conv_count

    # Emphasis (punctuation)
    voice['exclamation_points'] = content.count('!')
    voice['questions'] = content.count('?')
    voice['em_dashes'] = content.count('—') + content.count(' - ')

    # Short vs long sentences
    sentences = content.split('.')
    short_sentences = sum(1 for s in sentences if len(s.split()) <= 8)
    voice['uses_short_sentences'] = short_sentences > len(sentences) * 0.3

    return voice


def analyze_formatting(content: str) -> Dict:
    """Analyze formatting patterns (works across topics)"""
    if not content:
        return {}

    formatting = {}

    # Bullets/lists
    formatting['uses_bullets'] = '•' in content or '*' in content

    # Numbers
    formatting['uses_numbers'] = any(char.isdigit() for char in content)

    # Line breaks (white space)
    lines = content.split('\n')
    empty_lines = sum(1 for line in lines if not line.strip())
    formatting['empty_line_count'] = empty_lines
    formatting['uses_white_space'] = empty_lines > 2

    # Special characters
    formatting['uses_emojis'] = any(ord(char) > 127 for char in content)

    return formatting


def search_by_structure(structure_type: str, platform: Optional[str] = None) -> str:
    """
    Shortcut function: Search by content structure

    Structure types:
    - "listicle" → Numbered/bulleted lists
    - "story" → Narrative arc with lesson
    - "how-to" → Step-by-step guide
    - "thread" → Multi-part connected posts
    - "atomic" → Single focused idea
    - "contrarian" → Against-the-grain take
    """
    structure_queries = {
        'listicle': 'numbered list with multiple items 7-10 points format',
        'story': 'personal narrative story with beginning middle end and lesson',
        'how-to': 'step by step guide process instructions',
        'thread': 'multi part thread connected ideas numbered sequence',
        'atomic': 'single focused idea short concise one point',
        'contrarian': 'contrarian take against conventional wisdom different perspective'
    }

    query = structure_queries.get(structure_type.lower(), structure_type)
    return search_by_principle(query, platform=platform, match_count=5)


def search_by_hook_type(hook_type: str, platform: Optional[str] = None) -> str:
    """
    Shortcut function: Search by hook pattern

    Hook types:
    - "number_transformation" → X → Y in Z timeframe
    - "mistake_admission" → I did X wrong, here's what I learned
    - "bold_claim" → Strong statement that grabs attention
    - "question" → Thought-provoking question hook
    - "personal_story" → Starts with personal anecdote
    """
    hook_queries = {
        'number_transformation': 'hook with numbers showing transformation before after results',
        'mistake_admission': 'hook admitting mistakes failures what went wrong vulnerable',
        'bold_claim': 'hook with bold statement strong claim attention grabbing',
        'question': 'hook that asks thought provoking question to reader',
        'personal_story': 'hook starting with personal story anecdote experience'
    }

    query = hook_queries.get(hook_type.lower(), hook_type)
    return search_by_principle(query, platform=platform, match_count=5)


def search_by_voice(voice_style: str, platform: Optional[str] = None) -> str:
    """
    Shortcut function: Search by voice/tone

    Voice styles:
    - "vulnerable" → Authentic, admits struggles
    - "direct" → No fluff, straight to point
    - "conversational" → Casual, friendly tone
    - "authoritative" → Expert, confident
    - "funny" → Humorous, entertaining
    """
    voice_queries = {
        'vulnerable': 'vulnerable authentic admitting struggles personal honest raw',
        'direct': 'direct no fluff straight to point concise clear',
        'conversational': 'conversational casual friendly tone like talking to friend',
        'authoritative': 'authoritative expert confident professional credible',
        'funny': 'funny humorous entertaining witty playful'
    }

    query = voice_queries.get(voice_style.lower(), voice_style)
    return search_by_principle(query, platform=platform, match_count=5)


# Convenience function for agent workflow
def get_writing_principles(
    user_request: str,
    platform: str = "LinkedIn"
) -> Dict:
    """
    Extract writing principles from user request and find matching examples

    This is the main function for agent workflow integration.
    It automatically detects what principles to search for based on user intent.

    Args:
        user_request: User's content request (e.g., "write a listicle about AI tools")
        platform: Target platform

    Returns:
        Dict with principles and matched examples
    """
    # Detect structure type from request
    structure = detect_structure_type(user_request)

    # Detect hook preference
    hook = detect_hook_preference(user_request)

    # Search by detected principles
    examples = []

    if structure:
        result = json.loads(search_by_structure(structure, platform=platform))
        if result.get('matches'):
            examples.extend(result['matches'][:3])

    if hook:
        result = json.loads(search_by_hook_type(hook, platform=platform))
        if result.get('matches'):
            examples.extend(result['matches'][:2])

    # Deduplicate by ID
    seen_ids = set()
    unique_examples = []
    for ex in examples:
        if ex['id'] not in seen_ids:
            unique_examples.append(ex)
            seen_ids.add(ex['id'])

    return {
        'detected_structure': structure,
        'detected_hook_type': hook,
        'principle_examples': unique_examples[:5],
        'count': len(unique_examples[:5])
    }


def detect_structure_type(user_request: str) -> Optional[str]:
    """Detect structure type from user request"""
    request_lower = user_request.lower()

    if any(word in request_lower for word in ['listicle', 'list', 'tips', 'ways', 'reasons']):
        return 'listicle'
    elif any(word in request_lower for word in ['story', 'journey', 'experience']):
        return 'story'
    elif any(word in request_lower for word in ['how to', 'guide', 'steps']):
        return 'how-to'
    elif 'thread' in request_lower:
        return 'thread'
    elif any(word in request_lower for word in ['short', 'quick', 'atomic']):
        return 'atomic'
    elif any(word in request_lower for word in ['contrarian', 'against', 'why not']):
        return 'contrarian'

    return None


def detect_hook_preference(user_request: str) -> Optional[str]:
    """Detect hook preference from user request"""
    request_lower = user_request.lower()

    if any(word in request_lower for word in ['mistake', 'wrong', 'failed', 'learned']):
        return 'mistake_admission'
    elif any(word in request_lower for word in ['transformation', 'from', 'to', 'went from']):
        return 'number_transformation'
    elif 'question' in request_lower:
        return 'question'
    elif any(word in request_lower for word in ['story', 'experience', 'when i']):
        return 'personal_story'

    return None

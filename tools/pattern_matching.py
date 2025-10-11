"""
Pattern Matching for Cross-Industry Content Principles

Strategy: Search by CONTENT TYPE metadata, then extract universal patterns
This works better than semantic search for structural principles
"""

import os
import json
from typing import Dict, List, Optional
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))


def get_examples_by_type(
    content_type: str,
    platform: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Get examples by content_type field (faster than semantic search)

    Content types in your database:
    - "Thread", "Long Form", "Atomic Essay", "Infographic", "Video Long Form"

    Returns examples with extracted principles
    """
    try:
        query = supabase.table('content_examples').select('*')

        # Filter by content_type (case-insensitive partial match)
        if content_type:
            query = query.ilike('content_type', f'%{content_type}%')

        # Filter by platform
        if platform:
            query = query.eq('platform', platform)

        # Only approved content
        query = query.eq('status', 'approved')

        # Limit results
        query = query.limit(limit)

        result = query.execute()

        # Extract principles from each example
        examples_with_principles = []
        for item in result.data:
            examples_with_principles.append({
                **item,
                'principles': extract_principles(item)
            })

        return examples_with_principles

    except Exception as e:
        print(f"Error: {e}")
        return []


def extract_principles(content_example: Dict) -> Dict:
    """
    Extract reusable writing principles from a content example
    These principles work across ANY topic/industry
    """
    content = content_example.get('content', '')
    hook = content_example.get('hook_line', '')

    principles = {
        'hook_pattern': analyze_hook(hook),
        'structure': analyze_structure(content),
        'voice': analyze_voice(content),
        'formatting': analyze_formatting(content),
        'length': analyze_length(content)
    }

    return principles


def analyze_hook(hook: str) -> Dict:
    """Extract hook pattern (works across topics)"""
    if not hook:
        return {}

    import re

    pattern = {}

    # Pattern: Numbers
    numbers = re.findall(r'\b\d+[kKmM]?\b', hook)
    if numbers:
        pattern['uses_numbers'] = True
        pattern['numbers'] = numbers[:2]  # First 2 numbers

    # Pattern: Transformation (X → Y)
    if '→' in hook or ' to ' in hook or ' from ' in hook:
        pattern['pattern_type'] = 'transformation'

    # Pattern: First-person story
    if hook.strip().startswith('I ') or hook.strip().startswith("I'"):
        pattern['pattern_type'] = 'first_person_story'

    # Pattern: Question
    if '?' in hook:
        pattern['pattern_type'] = 'question'

    # Pattern: Bold claim with numbers
    if numbers and any(word in hook.lower() for word in ['never', 'always', 'every', 'best']):
        pattern['pattern_type'] = 'bold_claim_with_proof'

    # Length
    words = hook.split()
    pattern['word_count'] = len(words)
    pattern['length_category'] = 'short' if len(words) < 15 else 'medium' if len(words) < 25 else 'long'

    # Sentence structure
    sentences = hook.count('.') + hook.count('!') + hook.count('?')
    pattern['sentence_count'] = max(1, sentences)

    return pattern


def analyze_structure(content: str) -> Dict:
    """Extract structural patterns (works across topics)"""
    if not content:
        return {}

    structure = {}
    lines = content.split('\n')

    # List detection
    list_markers = ['•', '-', '*', '1.', '2.', '3.', '4.', '5.']
    list_lines = [line for line in lines if any(line.strip().startswith(m) for m in list_markers)]

    if len(list_lines) >= 3:
        structure['format'] = 'list'
        structure['list_items'] = len(list_lines)
        structure['list_style'] = 'numbered' if any(line.strip()[0].isdigit() for line in list_lines) else 'bulleted'

    # Paragraph structure
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    structure['paragraph_count'] = len(paragraphs)

    # Section headers
    headers = [line for line in lines if line.strip().startswith('#')]
    if headers:
        structure['has_sections'] = True
        structure['section_count'] = len(headers)

    # Story arc detection (beginning, middle, end markers)
    story_markers = ['when ', 'but ', 'now ', 'so ', 'here', 'lesson']
    story_count = sum(content.lower().count(marker) for marker in story_markers)
    if story_count >= 3 and len(paragraphs) >= 3:
        structure['likely_narrative'] = True

    return structure


def analyze_voice(content: str) -> Dict:
    """Extract voice/tone patterns (works across topics)"""
    if not content:
        return {}

    voice = {}

    # Personal vs impersonal
    first_person = content.lower().count(' i ') + content.lower().count("i'm ") + content.lower().count('my ')
    voice['first_person_count'] = first_person
    voice['voice_type'] = 'personal' if first_person > 3 else 'neutral'

    # Conversational markers
    conv_markers = [' but ', ' and ', ' so ', ' well ', ' now ', "here's", "that's"]
    conv_count = sum(content.lower().count(marker) for marker in conv_markers)
    voice['conversational_score'] = conv_count
    voice['is_conversational'] = conv_count > 5

    # Sentence length variation
    sentences = [s.strip() for s in content.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    if sentences:
        lengths = [len(s.split()) for s in sentences]
        voice['avg_sentence_length'] = sum(lengths) / len(lengths)
        voice['uses_short_sentences'] = sum(1 for l in lengths if l < 10) > len(lengths) * 0.3

    # Emphasis (exclamation, questions)
    voice['exclamation_count'] = content.count('!')
    voice['question_count'] = content.count('?')
    voice['is_emphatic'] = voice['exclamation_count'] > 2

    return voice


def analyze_formatting(content: str) -> Dict:
    """Extract formatting patterns (works across topics)"""
    if not content:
        return {}

    formatting = {}

    # White space usage
    lines = content.split('\n')
    empty_lines = sum(1 for line in lines if not line.strip())
    formatting['uses_white_space'] = empty_lines > 3
    formatting['empty_line_ratio'] = empty_lines / max(len(lines), 1)

    # Bullets
    formatting['uses_bullets'] = '•' in content or '- ' in content

    # Numbers in body
    import re
    numbers_in_body = len(re.findall(r'\b\d+\b', content))
    formatting['number_count'] = numbers_in_body
    formatting['uses_stats'] = numbers_in_body > 3

    # Special characters
    formatting['uses_arrows'] = '→' in content
    formatting['uses_emojis'] = any(ord(c) > 127 for c in content)

    return formatting


def analyze_length(content: str) -> Dict:
    """Extract length patterns"""
    if not content:
        return {}

    words = content.split()
    return {
        'word_count': len(words),
        'character_count': len(content),
        'length_category': (
            'short' if len(words) < 150 else
            'medium' if len(words) < 400 else
            'long'
        )
    }


# Main functions for agent workflow

def get_listicle_examples(platform: str = "LinkedIn", limit: int = 5) -> List[Dict]:
    """Get listicle examples with extracted principles"""
    # Get more examples to filter from
    examples = []
    examples.extend(get_examples_by_type("Thread", platform=platform, limit=50))
    examples.extend(get_examples_by_type("Long Form", platform=platform, limit=50))
    examples.extend(get_examples_by_type("Atomic", platform=platform, limit=50))

    # Filter to actual listicles (has numbered/bulleted list)
    listicles = [
        ex for ex in examples
        if ex['principles']['structure'].get('format') == 'list'
        and ex['principles']['structure'].get('list_items', 0) >= 5
    ]

    # Sort by list item count (more items = better listicle example)
    listicles.sort(key=lambda x: x['principles']['structure'].get('list_items', 0), reverse=True)

    return listicles[:limit]


def get_story_examples(platform: str = "LinkedIn", limit: int = 5) -> List[Dict]:
    """Get story/narrative examples with extracted principles"""
    examples = get_examples_by_type("Long Form", platform=platform, limit=20)

    # Filter to narratives
    stories = [
        ex for ex in examples
        if ex['principles']['structure'].get('likely_narrative')
        or ex['principles']['voice'].get('first_person_count', 0) > 5
    ]

    return stories[:limit]


def get_thread_examples(platform: str = "X", limit: int = 5) -> List[Dict]:
    """Get thread examples with extracted principles"""
    return get_examples_by_type("Thread", platform=platform, limit=limit)


def get_by_hook_pattern(hook_pattern: str, platform: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Get examples by hook pattern

    Hook patterns:
    - "transformation" → X to Y, before/after
    - "first_person_story" → I did X, here's what happened
    - "question" → Thought-provoking question
    - "bold_claim_with_proof" → Strong claim + numbers
    """
    # Get all approved examples
    query = supabase.table('content_examples').select('*').eq('status', 'approved')

    if platform:
        query = query.eq('platform', platform)

    result = query.limit(100).execute()  # Sample larger set

    # Extract principles and filter by hook pattern
    matches = []
    for item in result.data:
        principles = extract_principles(item)
        if principles['hook_pattern'].get('pattern_type') == hook_pattern:
            matches.append({
                **item,
                'principles': principles
            })

    return matches[:limit]


def summarize_principles(examples: List[Dict]) -> Dict:
    """
    Analyze multiple examples and extract common patterns
    Returns a "formula" that works across topics
    """
    if not examples:
        return {}

    summary = {
        'total_examples': len(examples),
        'common_patterns': {},
        'formula': {}
    }

    # Aggregate hook patterns
    hook_types = [ex['principles']['hook_pattern'].get('pattern_type') for ex in examples if ex['principles']['hook_pattern'].get('pattern_type')]
    if hook_types:
        from collections import Counter
        most_common_hook = Counter(hook_types).most_common(1)[0]
        summary['common_patterns']['hook_type'] = most_common_hook[0]
        summary['common_patterns']['hook_frequency'] = f"{most_common_hook[1]}/{len(examples)}"

    # Aggregate structure
    formats = [ex['principles']['structure'].get('format') for ex in examples if ex['principles']['structure'].get('format')]
    if formats:
        from collections import Counter
        most_common_format = Counter(formats).most_common(1)[0]
        summary['common_patterns']['structure_format'] = most_common_format[0]

        # Average list items for listicles
        if most_common_format[0] == 'list':
            list_counts = [ex['principles']['structure'].get('list_items', 0) for ex in examples if ex['principles']['structure'].get('list_items')]
            if list_counts:
                summary['common_patterns']['avg_list_items'] = sum(list_counts) / len(list_counts)

    # Aggregate voice
    personal_count = sum(1 for ex in examples if ex['principles']['voice'].get('voice_type') == 'personal')
    summary['common_patterns']['voice_style'] = 'personal' if personal_count > len(examples) * 0.5 else 'neutral'

    # Aggregate length
    word_counts = [ex['principles']['length'].get('word_count', 0) for ex in examples]
    if word_counts:
        summary['common_patterns']['avg_word_count'] = int(sum(word_counts) / len(word_counts))

    # Create formula
    summary['formula'] = {
        'hook': f"Use {summary['common_patterns'].get('hook_type', 'compelling')} hook pattern",
        'structure': f"{summary['common_patterns'].get('structure_format', 'standard')} format",
        'voice': f"{summary['common_patterns'].get('voice_style', 'neutral')} voice",
        'length': f"~{summary['common_patterns'].get('avg_word_count', 300)} words"
    }

    if summary['common_patterns'].get('avg_list_items'):
        summary['formula']['list_items'] = f"~{int(summary['common_patterns']['avg_list_items'])} items"

    return summary


# ==================== EMAIL PATTERN MATCHING ====================

def get_email_examples_by_type(
    email_type: str,
    limit: int = 5
) -> List[Dict]:
    """
    Get PGA email examples by type for WRITING QUALITY training (not topic training)

    Email types: "Email_Direct", "Email_Indirect", "Email_Tuesday", "Email_Value"

    Returns: Full email with extracted WRITING patterns (subject style, tone, structure)
    """
    try:
        query = supabase.table('content_examples')\
            .select('*')\
            .eq('platform', 'Email')\
            .eq('content_type', email_type)\
            .eq('status', 'approved')\
            .limit(limit)

        result = query.execute()

        # Extract WRITING patterns from each email
        emails_with_patterns = []
        for email in result.data:
            emails_with_patterns.append({
                **email,
                'writing_patterns': extract_email_writing_patterns(email)
            })

        return emails_with_patterns

    except Exception as e:
        print(f"Error fetching email examples: {e}")
        return []


def extract_email_writing_patterns(email: Dict) -> Dict:
    """
    Extract reusable WRITING patterns from PGA email (not topic patterns)
    Focus: How they write, not what they write about
    """
    subject = email.get('hook_line', '')
    body = email.get('content', '')

    return {
        'subject_line_pattern': analyze_subject_line(subject),
        'body_structure': analyze_email_body_structure(body),
        'tone_markers': analyze_email_tone(body),
        'cta_style': analyze_email_cta(body),
        'length_guidance': analyze_email_length(body, email.get('content_type', ''))
    }


def analyze_subject_line(subject: str) -> Dict:
    """Extract subject line writing pattern (not topic)"""
    if not subject:
        return {}

    import re

    pattern = {
        'char_count': len(subject),
        'word_count': len(subject.split())
    }

    # Pattern: Uses numbers
    numbers = re.findall(r'\b\d+[kKmM%]?\b', subject)
    if numbers:
        pattern['uses_numbers'] = True
        pattern['example_numbers'] = numbers[:2]

    # Pattern: Uses names/specifics
    capital_words = re.findall(r'\b[A-Z][a-z]+\b', subject)
    if capital_words and len(capital_words) > 1:  # More than just first word
        pattern['uses_names'] = True

    # Pattern: Question
    pattern['is_question'] = '?' in subject

    # Pattern: Curiosity gap
    teaser_words = ['how', 'why', 'secret', 'just', 'this', 'here']
    pattern['uses_curiosity'] = any(word in subject.lower() for word in teaser_words)

    # Pattern: Brackets/parentheses
    pattern['uses_brackets'] = '(' in subject or '[' in subject

    return pattern


def analyze_email_body_structure(body: str) -> Dict:
    """Extract body structure pattern (not topic)"""
    if not body:
        return {}

    structure = {}
    lines = [l for l in body.split('\n') if l.strip()]
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]

    # Opening style (first 2 sentences)
    sentences = body.replace('!', '.').replace('?', '.').split('.')
    first_sentences = [s.strip() for s in sentences[:2] if s.strip()]
    if first_sentences:
        first_text = ' '.join(first_sentences)
        structure['opens_with_story'] = any(word in first_text.lower() for word in ['i ', 'when ', 'last ', 'this week'])
        structure['opens_with_question'] = '?' in first_text
        structure['opening_length'] = len(first_text.split())

    # Section count
    structure['paragraph_count'] = len(paragraphs)

    # Uses lists/bullets
    structure['uses_bullets'] = '•' in body or '\n- ' in body

    # Uses line breaks for emphasis
    structure['uses_white_space'] = body.count('\n\n') > 2

    return structure


def analyze_email_tone(body: str) -> Dict:
    """Extract tone/voice markers (not topic)"""
    if not body:
        return {}

    tone = {}

    # Personal vs impersonal
    first_person_count = body.lower().count(' i ') + body.lower().count("i'm ") + body.lower().count('my ')
    tone['first_person_count'] = first_person_count
    tone['is_personal'] = first_person_count > 3

    # Conversational markers
    casual_markers = [' but ', ' and ', ' so ', "here's", "that's", "you're"]
    casual_count = sum(body.lower().count(marker) for marker in casual_markers)
    tone['conversational_score'] = casual_count

    # Specificity (names, numbers)
    import re
    tone['number_count'] = len(re.findall(r'\b\d+[kKmM%]?\b', body))
    capital_words = re.findall(r'\b[A-Z][a-z]+\b', body)
    tone['proper_noun_count'] = len([w for w in capital_words if w not in ['I', 'A']])

    # Emphasis
    tone['uses_bold'] = '**' in body or '__' in body
    tone['exclamation_count'] = body.count('!')

    return tone


def analyze_email_cta(body: str) -> Dict:
    """Extract CTA style pattern (not topic)"""
    if not body:
        return {}

    cta = {}

    # Find last paragraph (likely CTA)
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
    if paragraphs:
        last_para = paragraphs[-1]

        # Action words
        action_verbs = ['reply', 'click', 'join', 'check', 'grab', 'watch', 'read', 'book']
        cta['has_action_verb'] = any(verb in last_para.lower() for verb in action_verbs)

        # Specific vs vague
        vague_words = ['reach out', 'let me know', 'get in touch', 'feel free']
        cta['is_vague'] = any(phrase in last_para.lower() for phrase in vague_words)

        # Direct instruction
        cta['is_direct'] = last_para.lower().startswith(tuple(action_verbs))

        cta['cta_length'] = len(last_para.split())

    return cta


def analyze_email_length(body: str, email_type: str) -> Dict:
    """Email type best practices (guidance, not limits)"""
    if not body:
        return {}

    word_count = len(body.split())

    # Best practice ranges by type
    guidance = {
        'Email_Value': {'min': 300, 'max': 500, 'purpose': 'teach something specific'},
        'Email_Tuesday': {'min': 150, 'max': 300, 'purpose': 'quick wins, links'},
        'Email_Direct': {'min': 200, 'max': 400, 'purpose': 'clear value prop'},
        'Email_Indirect': {'min': 250, 'max': 400, 'purpose': 'story + soft offer'}
    }

    best_practice = guidance.get(email_type, {'min': 200, 'max': 400, 'purpose': 'balanced'})

    return {
        'actual_word_count': word_count,
        'best_practice_range': f"{best_practice['min']}-{best_practice['max']} words",
        'purpose': best_practice['purpose'],
        'is_within_range': best_practice['min'] <= word_count <= best_practice['max']
    }


def format_email_examples_for_prompt(email_type: str, limit: int = 3) -> str:
    """
    Format email examples for prompt injection
    Focus: Show WRITING STYLE, not topics
    """
    examples = get_email_examples_by_type(email_type, limit)

    if not examples:
        return f"No {email_type} examples found."

    formatted = f"**{email_type} WRITING STYLE EXAMPLES:**\n\n"

    for i, ex in enumerate(examples, 1):
        subject = ex.get('hook_line', 'No subject')
        body = ex.get('content', 'No body')[:500]  # First 500 chars
        patterns = ex['writing_patterns']

        formatted += f"Example {i}:\n"
        formatted += f"Subject: {subject}\n"
        formatted += f"Body: {body}...\n\n"
        formatted += f"Writing patterns to copy:\n"
        formatted += f"- Subject: {patterns['subject_line_pattern'].get('char_count', 0)} chars, "
        formatted += f"{'uses numbers' if patterns['subject_line_pattern'].get('uses_numbers') else 'no numbers'}\n"
        formatted += f"- Tone: {'personal' if patterns['tone_markers'].get('is_personal') else 'neutral'}, "
        formatted += f"{patterns['tone_markers'].get('proper_noun_count', 0)} names/specifics\n"
        formatted += f"- Structure: {patterns['body_structure'].get('paragraph_count', 0)} paragraphs\n"
        formatted += f"- CTA: {'direct' if patterns['cta_style'].get('is_direct') else 'soft'}\n\n"

    return formatted


# ==================== YOUTUBE PATTERN MATCHING ====================

def get_youtube_examples_by_type(
    content_type: str = "Video Long Form",
    limit: int = 3
) -> List[Dict]:
    """
    Get YouTube script examples for WRITING QUALITY training (not topic training)

    Content types: "Video Long Form" (only type currently in DB)

    Returns: Full script with extracted WRITING patterns (hook style, cadence, timing)
    """
    try:
        query = supabase.table('content_examples')\
            .select('*')\
            .eq('platform', 'YouTube')\
            .eq('content_type', content_type)\
            .eq('status', 'approved')\
            .limit(limit)

        result = query.execute()

        # Extract WRITING patterns from each script
        scripts_with_patterns = []
        for script in result.data:
            scripts_with_patterns.append({
                **script,
                'writing_patterns': extract_youtube_writing_patterns(script)
            })

        return scripts_with_patterns

    except Exception as e:
        print(f"Error fetching YouTube examples: {e}")
        return []


def extract_youtube_writing_patterns(script: Dict) -> Dict:
    """
    Extract reusable WRITING patterns from YouTube script (not topic patterns)
    Focus: How they write for video, not what they write about
    """
    hook = script.get('hook_line', '')
    body = script.get('content', '')

    return {
        'hook_pattern': analyze_video_hook(hook),
        'script_cadence': analyze_video_cadence(body),
        'proof_style': analyze_video_proof_style(body),
        'cta_pattern': analyze_video_cta(body),
        'timing_analysis': analyze_video_timing(body, hook)
    }


def analyze_video_hook(hook: str) -> Dict:
    """Extract video hook writing pattern (not topic)"""
    if not hook:
        return {}

    import re

    pattern = {
        'word_count': len(hook.split()),
        'char_count': len(hook)
    }

    # Pattern: Question
    pattern['is_question'] = '?' in hook

    # Pattern: Uses numbers upfront
    numbers = re.findall(r'\b\d+[kKmM%$+]?\b', hook)
    if numbers:
        pattern['uses_numbers'] = True
        pattern['numbers_upfront'] = hook.find(numbers[0]) < 50  # In first 50 chars

    # Pattern: "You" statement (direct address)
    pattern['uses_you'] = 'you' in hook.lower() or 'your' in hook.lower()

    # Pattern: Bold claim
    bold_words = ['made', 'earned', 'grew', 'built', 'achieved']
    pattern['is_bold_claim'] = any(word in hook.lower() for word in bold_words)

    # Estimated seconds (2.5 words/sec spoken)
    pattern['estimated_seconds'] = round(pattern['word_count'] / 2.5, 1)

    return pattern


def analyze_video_cadence(body: str) -> Dict:
    """Extract spoken cadence pattern (not topic)"""
    if not body:
        return {}

    cadence = {}

    # Sentence length for spoken rhythm
    sentences = [s.strip() for s in body.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    if sentences:
        lengths = [len(s.split()) for s in sentences]
        cadence['avg_sentence_length'] = sum(lengths) / len(lengths)
        cadence['has_short_punchy'] = sum(1 for l in lengths if l < 8) > len(lengths) * 0.3

    # Line breaks for pauses
    cadence['line_breaks'] = body.count('\n\n')
    cadence['uses_pauses'] = cadence['line_breaks'] > 2

    # Bullets for emphasis
    cadence['uses_bullets'] = '•' in body or '\n-' in body or '\n1.' in body

    return cadence


def analyze_video_proof_style(body: str) -> Dict:
    """Extract proof presentation pattern (not topic)"""
    if not body:
        return {}

    proof = {}

    import re

    # Numbers in script
    numbers = re.findall(r'\b\d+[kKmM%$+]?\b', body)
    proof['number_count'] = len(numbers)
    proof['uses_specific_numbers'] = len(numbers) > 0

    # Dollar amounts (common in video scripts)
    proof['has_money'] = '$' in body or 'dollar' in body.lower()

    # Proper nouns (names, places)
    capital_words = re.findall(r'\b[A-Z][a-z]+\b', body)
    proof['proper_noun_count'] = len([w for w in capital_words if w not in ['I', 'A']])

    # Called out vs embedded
    # Called out = in bullets or bold
    proof['called_out_style'] = '•' in body or '**' in body

    return proof


def analyze_video_cta(body: str) -> Dict:
    """Extract video CTA pattern (not topic)"""
    if not body:
        return {}

    cta = {}

    # Find last 2 sentences (likely CTA)
    sentences = [s.strip() for s in body.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    if len(sentences) >= 2:
        last_two = ' '.join(sentences[-2:])

        # Video-specific CTAs
        video_actions = ['comment', 'subscribe', 'follow', 'watch', 'like', 'share']
        cta['has_video_action'] = any(action in last_two.lower() for action in video_actions)

        # Comment bait (specific keyword to comment)
        cta['has_comment_bait'] = 'comment' in last_two.lower() and ('"' in last_two or "'" in last_two)

        # Direct instruction
        cta['is_direct'] = any(last_two.lower().startswith(action) for action in video_actions)

        cta['cta_length'] = len(last_two.split())

    return cta


def analyze_video_timing(body: str, hook: str = '') -> Dict:
    """Estimate timing for video sections (words → seconds)"""

    # Spoken rate: 150 words/min = 2.5 words/sec
    WORDS_PER_SECOND = 2.5

    timing = {}

    # Total script
    total_words = len(body.split())
    timing['total_words'] = total_words
    timing['estimated_total_seconds'] = round(total_words / WORDS_PER_SECOND, 1)

    # Hook timing
    hook_words = len(hook.split()) if hook else 0
    timing['hook_words'] = hook_words
    timing['hook_seconds'] = round(hook_words / WORDS_PER_SECOND, 1)

    # Estimate sections (if bullets present)
    if '•' in body or '\n-' in body:
        timing['has_sections'] = True
        # Rough estimate: intro + bullets + outro
        timing['section_style'] = 'bulleted'
    else:
        timing['has_sections'] = False
        timing['section_style'] = 'narrative'

    # Length category
    if total_words < 50:
        timing['length_category'] = 'ultra_short'  # <20 sec
        timing['ideal_for'] = 'TikTok, Reels'
    elif total_words < 150:
        timing['length_category'] = 'short'  # 20-60 sec
        timing['ideal_for'] = 'YouTube Shorts, Reels'
    elif total_words < 400:
        timing['length_category'] = 'medium'  # 1-3 min
        timing['ideal_for'] = 'Explainer videos'
    else:
        timing['length_category'] = 'long'  # 3+ min
        timing['ideal_for'] = 'Deep dives'

    return timing


def format_youtube_examples_for_prompt(content_type: str = "Video Long Form", limit: int = 3) -> str:
    """
    Format YouTube script examples for prompt injection
    Focus: Show WRITING STYLE, not topics
    """
    examples = get_youtube_examples_by_type(content_type, limit)

    if not examples:
        return f"No {content_type} examples found."

    formatted = f"**YOUTUBE SCRIPT STYLE EXAMPLES:**\n\n"

    for i, ex in enumerate(examples, 1):
        hook = ex.get('hook_line', 'No hook')
        body = ex.get('content', 'No body')[:400]  # First 400 chars
        patterns = ex['writing_patterns']
        timing = patterns['timing_analysis']

        formatted += f"Example {i} ({timing['length_category']}, ~{timing['estimated_total_seconds']}s):\n"
        formatted += f"Hook: {hook}\n"
        formatted += f"Body: {body}...\n\n"
        formatted += f"Writing patterns to copy:\n"
        formatted += f"- Hook: {patterns['hook_pattern'].get('word_count', 0)} words, "
        formatted += f"{'question' if patterns['hook_pattern'].get('is_question') else 'statement'}, "
        formatted += f"~{patterns['hook_pattern'].get('estimated_seconds', 0)}s\n"
        formatted += f"- Cadence: {'short punchy' if patterns['script_cadence'].get('has_short_punchy') else 'flowing'}, "
        formatted += f"{'uses bullets' if patterns['script_cadence'].get('uses_bullets') else 'narrative'}\n"
        formatted += f"- Proof: {patterns['proof_style'].get('number_count', 0)} numbers, "
        formatted += f"{'called out' if patterns['proof_style'].get('called_out_style') else 'embedded'}\n"
        formatted += f"- CTA: {'direct video action' if patterns['cta_pattern'].get('has_video_action') else 'soft'}\n\n"

    return formatted

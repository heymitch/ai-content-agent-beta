"""
Shared library of forbidden AI patterns and clichés
Used across all platform validators for consistent quality control
"""
import re
from typing import List, Dict, Any

class ForbiddenPatterns:
    """Central repository of AI clichés and forbidden patterns"""

    # Contrast framing (biggest offender from n8n grading)
    CONTRAST_FRAMING = [
        r'\bnot\s+\w+\s*,\s*but\s+\w+\b',  # "not X, but Y"
        r'\b\w+\s*,\s*not\s+\w+\b',  # "X, not Y"
        r'\bdon\'t\s+\w+\s*,\s*\w+\b',  # "don't do X, do Y"
        r'\bisn\'t\s+about\s+\w+\s*,\s*it\'s\s+about\b',  # "isn't about X, it's about Y"
    ]

    # AI clichés and overused phrases
    AI_CLICHES = [
        r'\bhere\'s\s+the\s+thing\b',
        r'\blet\'s\s+be\s+honest\b',
        r'\bpicture\s+this\b',
        r'\bimagine\s+a\s+world\s+where\b',
        r'\bin\s+a\s+world\s+where\b',
        r'\bthe\s+reality\s+is\b',
        r'\bthe\s+truth\s+is\b',
        r'\bthink\s+about\s+it\b',
        r'\bconsider\s+this\b',
        r'\bat\s+the\s+end\s+of\s+the\s+day\b',
        r'\bgame[\s-]?changer\b',
        r'\bparadigm\s+shift\b',
        r'\blow[\s-]?hanging\s+fruit\b',
        r'\bsynergy\b',
        r'\bcircle\s+back\b',
        r'\btouch\s+base\b',
        r'\blevel\s+up\b',
        r'\bdouble[\s-]?click\b',
        r'\bdeep\s+dive\b',
        r'\bunpack\s+(this|that)\b',
        r'\bdrink\s+the\s+kool[\s-]?aid\b',
    ]

    # Rhetorical questions (especially as endings)
    RHETORICAL_QUESTIONS = [
        r'\bwhat\s+if\s+I\s+told\s+you\b',
        r'\bever\s+wonder(?:ed)?\s+why\b',
        r'\bhave\s+you\s+ever\b',
        r'\bwouldn\'t\s+you\s+agree\b',
        r'\bisn\'t\s+it\s+time\b',
        r'\bdon\'t\s+you\s+think\b',
        r'\bsound\s+familiar\?',
        r'\brings?\s+a\s+bell\?',
    ]

    # Vague/abstract language (prefer concrete specificity)
    VAGUE_LANGUAGE = [
        r'\bseveral\s+ways?\b',
        r'\bmany\s+reasons?\b',
        r'\ba\s+lot\s+of\b',
        r'\bvarious\s+methods?\b',
        r'\bnumerous\s+benefits?\b',
        r'\bsignificantly\s+better\b',  # Better: "37% faster"
        r'\bmassively\s+improved\b',  # Better: "cut costs by $12K"
        r'\bincredibly\s+effective\b',
    ]

    # Empty fluff (no value)
    EMPTY_FLUFF = [
        r'\bin\s+today\'s\s+fast[\s-]?paced\s+world\b',
        r'\bin\s+this\s+day\s+and\s+age\b',
        r'\bas\s+we\s+all\s+know\b',
        r'\bit\s+goes\s+without\s+saying\b',
        r'\bneedless\s+to\s+say\b',
        r'\bto\s+be\s+honest\b',  # TBH
        r'\bquite\s+frankly\b',
    ]

    # Fake case studies and fabricated stories (FORBIDDEN)
    FAKE_STORIES = [
        r'\b[A-Z][a-z]+\s+from\s+[A-Z][a-z]+(?:Scale|Pro|Agency|Systems?)\b',  # "Kevin from ContentScale"
        r'\b[A-Z][a-z]+\s+at\s+[A-Z][a-z]+(?:Scale|Pro|Agency|Systems?)\b',  # "Mark at ContentPro"
        r'\bI\s+(?:just\s+)?(?:helped|worked with|coached)\s+(?:an?\s+)?agency\b',  # "I helped an agency"
        r'\bafter\s+(?:helping|working with|coaching)\s+(?:an?\s+)?(?:\d+\+?\s+)?(?:agencies|clients)\b',  # "after helping 50+ agencies"
        r'\bone\s+agency\s+(?:implemented|used|tried)\b',  # "one agency implemented"
        r'\b(?:scaled|helped|took)\s+\d+\s+agencies?\s+to\s+\$[\d,]+K?\+?\s+MRR\b',  # "scaled 4 agencies to $50K+ MRR"
        r'\breal\s+results\s+from\s+our\s+(?:latest\s+)?(?:agency\s+partner|client)\b',  # "real results from our latest agency partner"
        r'\bmost\s+agencies?\s+(?:cap out|max out|struggle|fail)\s+at\b',  # "most agencies cap out at"
        r'\bthat\'s\s+what\s+[A-Z][a-z]+\s+(?:thought too|believed)\b',  # "that's what Kevin thought too"
    ]

    @classmethod
    def get_all_patterns(cls) -> List[str]:
        """Get all forbidden patterns combined"""
        return (
            cls.CONTRAST_FRAMING +
            cls.AI_CLICHES +
            cls.RHETORICAL_QUESTIONS +
            cls.VAGUE_LANGUAGE +
            cls.EMPTY_FLUFF +
            cls.FAKE_STORIES
        )

    @classmethod
    def check_content(cls, content: str) -> List[Dict[str, Any]]:
        """
        Check content against all forbidden patterns

        Args:
            content: Content to check

        Returns:
            List of detected pattern issues
        """
        issues = []

        # Check each pattern category
        pattern_categories = {
            'contrast_framing': (cls.CONTRAST_FRAMING, 'high'),
            'ai_cliche': (cls.AI_CLICHES, 'high'),
            'rhetorical_question': (cls.RHETORICAL_QUESTIONS, 'medium'),
            'vague_language': (cls.VAGUE_LANGUAGE, 'medium'),
            'empty_fluff': (cls.EMPTY_FLUFF, 'low'),
            'fake_story': (cls.FAKE_STORIES, 'critical'),
        }

        for category_name, (patterns, severity) in pattern_categories.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    issues.append({
                        'type': category_name,
                        'pattern': pattern,
                        'matched_text': match.group(0),
                        'position': match.start(),
                        'severity': severity,
                        'auto_fixable': False,  # Manual revision required
                        'message': f"Forbidden pattern detected: '{match.group(0)}'"
                    })

        return issues

    @classmethod
    def get_pattern_explanation(cls, pattern_type: str) -> str:
        """Get explanation for why a pattern is forbidden"""
        explanations = {
            'contrast_framing': "Use concrete specificity instead of abstract contrasts. Replace 'not X, but Y' with specific examples and data.",
            'ai_cliche': "This phrase is overused in AI-generated content. Use fresh, authentic language instead.",
            'rhetorical_question': "Replace rhetorical questions with direct statements and concrete insights.",
            'vague_language': "Be specific. Use numbers, timelines, and measurable outcomes instead of vague qualifiers.",
            'empty_fluff': "This adds no value. Get to the point with concrete insights.",
            'fake_story': "NEVER fabricate case studies, client stories, or fake examples. Only use real, verified data or speak from personal experience.",
        }
        return explanations.get(pattern_type, "Forbidden pattern detected")


class ContentQualityChecks:
    """Additional quality checks beyond pattern matching"""

    @staticmethod
    def check_specificity(content: str) -> Dict[str, Any]:
        """Check for concrete numbers and specific claims"""
        # Count numbers in content
        numbers = re.findall(r'\b\d+[%$KM]?\b', content)
        word_count = len(content.split())
        number_density = len(numbers) / max(word_count, 1) * 100

        if number_density < 1.0:  # Less than 1% numbers
            return {
                'type': 'low_specificity',
                'severity': 'medium',
                'auto_fixable': False,
                'message': f'Low specificity: Only {len(numbers)} numbers found. Add concrete data/metrics.',
                'numbers_found': len(numbers),
                'density': round(number_density, 2)
            }

        return None

    @staticmethod
    def check_length(content: str, min_words: int, max_words: int, platform: str) -> Dict[str, Any]:
        """Check content length for platform"""
        word_count = len(content.split())

        if word_count < min_words:
            return {
                'type': 'too_short',
                'severity': 'medium',
                'auto_fixable': False,
                'message': f'{platform} content too short: {word_count} words (min: {min_words})',
                'current': word_count,
                'minimum': min_words
            }
        elif word_count > max_words:
            return {
                'type': 'too_long',
                'severity': 'low',
                'auto_fixable': False,
                'message': f'{platform} content too long: {word_count} words (max: {max_words})',
                'current': word_count,
                'maximum': max_words
            }

        return None

    @staticmethod
    def check_ending_question(content: str) -> Dict[str, Any]:
        """Check if content ends with rhetorical question"""
        # Get last sentence
        sentences = re.split(r'[.!?]+', content.strip())
        last_sentence = sentences[-1].strip() if sentences else ""

        if '?' in last_sentence:
            return {
                'type': 'ending_question',
                'severity': 'high',
                'auto_fixable': False,
                'message': f'Ends with question: "{last_sentence}". Use a direct statement instead.',
                'question': last_sentence
            }

        return None

    @staticmethod
    def check_paragraph_structure(content: str, platform: str) -> Dict[str, Any]:
        """Check paragraph length for readability"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if platform == 'linkedin':
            # LinkedIn prefers short paragraphs (1-3 sentences)
            long_paragraphs = []
            for i, para in enumerate(paragraphs):
                sentences = len(re.split(r'[.!?]+', para))
                if sentences > 3:
                    long_paragraphs.append(i + 1)

            if long_paragraphs:
                return {
                    'type': 'long_paragraphs',
                    'severity': 'low',
                    'auto_fixable': False,
                    'message': f'Paragraphs {long_paragraphs} are too long. Break into 1-3 sentence chunks.',
                    'paragraphs': long_paragraphs
                }

        return None

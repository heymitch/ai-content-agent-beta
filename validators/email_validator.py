"""
Email content validator with subject line grading and spam detection
Supports Value, Indirect, and Direct email types from n8n workflow
"""
import re
from typing import List, Dict, Any
from .base_validator import BaseValidator
from .pattern_library import ForbiddenPatterns, ContentQualityChecks

class EmailValidator(BaseValidator):
    """Validates email content with subject line optimization and spam checks"""

    # Email metrics (from n8n PGA data)
    MIN_WORD_COUNT = {
        'value': 400,
        'indirect': 400,
        'direct': 100
    }
    MAX_WORD_COUNT = {
        'value': 500,
        'indirect': 600,
        'direct': 200
    }

    # Subject line optimization (from n8n patterns)
    SUBJECT_MIN_CHARS = 20
    SUBJECT_MAX_CHARS = 50  # Optimal for mobile preview
    SUBJECT_OPTIMAL_WORDS = (5, 9)  # 5-9 words performs best

    # Spam trigger words (based on email deliverability best practices)
    SPAM_TRIGGERS = [
        r'\bfree\s+money\b',
        r'\b100%\s+free\b',
        r'\bact\s+now\b',
        r'\bcall\s+now\b',
        r'\bclick\s+here\b',
        r'\bguaranteed\b',
        r'\bmake\s+\$\d+\b',
        r'\bno\s+obligation\b',
        r'\brisk[\s-]?free\b',
        r'\b!!+\b',  # Multiple exclamation marks
        r'[A-Z]{5,}',  # All caps words (5+ chars)
    ]

    def __init__(self, email_type: str = 'indirect'):
        """
        Initialize email validator

        Args:
            email_type: One of 'value', 'indirect', 'direct'
        """
        self.email_type = email_type.lower()
        if self.email_type not in ['value', 'indirect', 'direct']:
            self.email_type = 'indirect'  # Default to indirect

    def validate(self, content: str) -> List[Dict[str, Any]]:
        """
        Run deterministic validation checks for email

        Args:
            content: Full email with subject line (format: "Subject: ...\n\nBody...")

        Returns:
            List of validation issues
        """
        issues = []

        # Parse subject line and body
        subject, body = self._parse_email(content)

        if not subject or not body:
            return [{
                'type': 'invalid_format',
                'severity': 'high',
                'auto_fixable': False,
                'message': 'Email must include "Subject: ..." line followed by body'
            }]

        # 1. Subject line validation
        subject_issues = self._validate_subject_line(subject)
        issues.extend(subject_issues)

        # 2. Spam trigger detection
        spam_issues = self._check_spam_triggers(content)
        issues.extend(spam_issues)

        # 3. Forbidden AI patterns
        pattern_issues = ForbiddenPatterns.check_content(body)
        issues.extend(pattern_issues)

        # 4. Email length validation
        length_issue = self._check_email_length(body)
        if length_issue:
            issues.append(length_issue)

        # 5. CTA validation
        cta_issue = self._check_cta_presence(body)
        if cta_issue:
            issues.append(cta_issue)

        # 6. Email type-specific validation
        type_issues = self._validate_by_type(body)
        issues.extend(type_issues)

        # 7. Formatting issues
        format_issues = self._check_formatting(body)
        issues.extend(format_issues)

        return issues

    def _parse_email(self, content: str) -> tuple:
        """Extract subject line and body from email content"""
        lines = content.strip().split('\n')

        subject = ""
        body_start = 0

        # Find subject line
        for i, line in enumerate(lines):
            if line.lower().startswith('subject:'):
                subject = line[8:].strip()  # Remove "Subject:" prefix
                body_start = i + 1
                break

        # Get body (skip empty lines after subject)
        body_lines = []
        for line in lines[body_start:]:
            if line.strip() or body_lines:  # Start collecting after first non-empty
                body_lines.append(line)

        body = '\n'.join(body_lines).strip()

        return subject, body

    def _validate_subject_line(self, subject: str) -> List[Dict[str, Any]]:
        """Validate subject line for length and format"""
        issues = []

        # Length check
        char_count = len(subject)
        if char_count < self.SUBJECT_MIN_CHARS:
            issues.append({
                'type': 'subject_too_short',
                'severity': 'high',
                'auto_fixable': False,
                'message': f'Subject line is {char_count} chars (min: {self.SUBJECT_MIN_CHARS})',
                'current': char_count
            })
        elif char_count > self.SUBJECT_MAX_CHARS:
            issues.append({
                'type': 'subject_too_long',
                'severity': 'medium',
                'auto_fixable': False,
                'message': f'Subject line is {char_count} chars (optimal max: {self.SUBJECT_MAX_CHARS} for mobile)',
                'current': char_count
            })

        # Word count check
        word_count = len(subject.split())
        min_words, max_words = self.SUBJECT_OPTIMAL_WORDS
        if word_count < min_words:
            issues.append({
                'type': 'subject_too_few_words',
                'severity': 'medium',
                'auto_fixable': False,
                'message': f'Subject has {word_count} words (optimal: {min_words}-{max_words})',
                'current': word_count
            })
        elif word_count > max_words:
            issues.append({
                'type': 'subject_too_many_words',
                'severity': 'low',
                'auto_fixable': False,
                'message': f'Subject has {word_count} words (optimal: {min_words}-{max_words})',
                'current': word_count
            })

        # All caps check
        if subject.isupper() and len(subject) > 10:
            issues.append({
                'type': 'subject_all_caps',
                'severity': 'high',
                'auto_fixable': False,
                'message': 'Subject line is all caps (triggers spam filters)'
            })

        # Excessive punctuation
        if subject.count('!') > 1 or subject.count('?') > 1:
            issues.append({
                'type': 'subject_excessive_punctuation',
                'severity': 'medium',
                'auto_fixable': False,
                'message': 'Subject has multiple exclamation/question marks (spammy)'
            })

        return issues

    def _check_spam_triggers(self, content: str) -> List[Dict[str, Any]]:
        """Check for spam trigger words and patterns"""
        issues = []

        for pattern in self.SPAM_TRIGGERS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                issues.append({
                    'type': 'spam_trigger',
                    'severity': 'high',
                    'auto_fixable': False,
                    'message': f'Spam trigger detected: "{match.group(0)}"',
                    'matched_text': match.group(0)
                })

        return issues

    def _check_email_length(self, body: str) -> Dict[str, Any]:
        """Check email body length for type"""
        word_count = len(body.split())
        min_words = self.MIN_WORD_COUNT[self.email_type]
        max_words = self.MAX_WORD_COUNT[self.email_type]

        if word_count < min_words:
            return {
                'type': 'body_too_short',
                'severity': 'medium',
                'auto_fixable': False,
                'message': f'{self.email_type.title()} email too short: {word_count} words (min: {min_words})',
                'current': word_count,
                'minimum': min_words
            }
        elif word_count > max_words:
            return {
                'type': 'body_too_long',
                'severity': 'low',
                'auto_fixable': False,
                'message': f'{self.email_type.title()} email too long: {word_count} words (max: {max_words})',
                'current': word_count,
                'maximum': max_words
            }

        return None

    def _check_cta_presence(self, body: str) -> Dict[str, Any]:
        """Check for CTA with backtick variables"""
        # Look for CTA variables like {{call_cta}}, {{app_cta}}, {{ghost_cta}}
        cta_pattern = r'`\{\{(?:call_cta|app_cta|ghost_cta)\}\}`'

        if not re.search(cta_pattern, body):
            return {
                'type': 'missing_cta',
                'severity': 'high',
                'auto_fixable': False,
                'message': 'No CTA found. Include `{{call_cta}}`, `{{app_cta}}`, or `{{ghost_cta}}`'
            }

        # Check for multiple CTAs (reduces conversion)
        cta_matches = re.findall(cta_pattern, body)
        if len(cta_matches) > 1:
            return {
                'type': 'multiple_ctas',
                'severity': 'medium',
                'auto_fixable': False,
                'message': f'Found {len(cta_matches)} CTAs. Use only ONE for best conversion.'
            }

        return None

    def _validate_by_type(self, body: str) -> List[Dict[str, Any]]:
        """Email type-specific validation"""
        issues = []

        if self.email_type == 'indirect':
            # Indirect emails should have case study/story
            if not re.search(r'\b[A-Z][a-z]+\b.*\b(?:told me|went from|achieved|landed)\b', body):
                issues.append({
                    'type': 'indirect_missing_story',
                    'severity': 'high',
                    'auto_fixable': False,
                    'message': 'Indirect email needs specific client case study/story'
                })

        elif self.email_type == 'value':
            # Value emails should focus on tool/system
            if not re.search(r'\b(?:tool|system|workflow|framework|method|approach)\b', body, re.IGNORECASE):
                issues.append({
                    'type': 'value_missing_tool_focus',
                    'severity': 'medium',
                    'auto_fixable': False,
                    'message': 'Value email should highlight specific tool/system'
                })

        elif self.email_type == 'direct':
            # Direct emails need urgency
            if not re.search(r'\b(?:today|now|last call|closing|limited|spots left|deadline)\b', body, re.IGNORECASE):
                issues.append({
                    'type': 'direct_missing_urgency',
                    'severity': 'high',
                    'auto_fixable': False,
                    'message': 'Direct email needs urgency element (deadline, limited spots, etc.)'
                })

        return issues

    def _check_formatting(self, body: str) -> List[Dict[str, Any]]:
        """Check for n8n formatting requirements"""
        issues = []

        # Check for double line breaks between sentences (n8n requires single line per sentence)
        if '\n\n\n' in body:
            issues.append({
                'type': 'triple_line_breaks',
                'severity': 'low',
                'auto_fixable': True,
                'message': 'Remove triple line breaks (n8n format: single line per sentence)'
            })

        # Check for proper sign-off (any capitalized first name)
        if not re.search(r'\n[A-Z][a-z]+\s*$', body, re.MULTILINE):
            issues.append({
                'type': 'missing_signature',
                'severity': 'low',
                'auto_fixable': False,
                'message': 'Email should end with first name signature'
            })

        return issues

    def get_grading_rubric(self) -> str:
        """Return email grading criteria for Claude"""
        return f"""
EMAIL GRADING RUBRIC ({self.email_type.upper()} TYPE) (0-100):

**Subject Line Quality (20 points)**
- 20-50 characters (mobile optimized)
- 5-9 words
- No spam triggers (all caps, multiple !!)
- Clear value proposition

**Opening Hook (20 points)**
- Engaging first sentence
- Relevant to audience pain point
- Sets up value delivery

**Body Content ({self.email_type.upper()}-specific) (40 points)**
{'- Specific client case study with results' if self.email_type == 'indirect' else ''}
{'- Clear tool/system explanation with actionable value' if self.email_type == 'value' else ''}
{'- Direct value proposition with urgency' if self.email_type == 'direct' else ''}
- Concrete examples and data
- Logical flow and readability
- No AI clichés or spam triggers

**CTA Effectiveness (20 points)**
- Single clear call-to-action
- Proper variable format (`{{call_cta}}` etc.)
- Natural transition to CTA
- Compelling reason to act

**CRITICAL VIOLATIONS (Auto -30 points each):**
- Spam trigger words detected
- Multiple CTAs (decision fatigue)
- All caps subject line
- Missing CTA variable
- AI clichés ("here's the thing", "picture this")

**OPTIMAL METRICS:**
- Subject: 30-40 chars, 5-7 words
- Body: {self.MIN_WORD_COUNT[self.email_type]}-{self.MAX_WORD_COUNT[self.email_type]} words
- Format: One sentence per line
- CTAs: Exactly ONE
"""

    def get_writing_rules(self) -> str:
        """Return email writing guidelines"""
        return f"""
EMAIL WRITING RULES ({self.email_type.upper()} TYPE):

**Subject Line Rules:**
- Length: 30-40 characters (optimal for mobile)
- Words: 5-7 words (proven best performance)
- NO all caps, NO multiple !!, NO spam words
- Conversational and specific

**Body Structure:**
{self._get_type_specific_structure()}

**Formatting (n8n Requirements):**
- One sentence per line (NO double breaks within paragraphs)
- Double line break ONLY between major sections
- CTA variables in backticks: `{{call_cta}}` or `{{app_cta}}` or `{{ghost_cta}}`
- Sign-off: First name only (e.g., "Mitchell")

**Forbidden:**
- ❌ Spam triggers ("free money", "guaranteed", "act now")
- ❌ Multiple CTAs (use only ONE)
- ❌ All caps words (spam filter trigger)
- ❌ Excessive punctuation (!!! or ???)
- ❌ AI clichés from pattern library
- ❌ Content mill language

**Optimal Length:**
- Subject: 30-40 chars
- Body: {self.MIN_WORD_COUNT[self.email_type]}-{self.MAX_WORD_COUNT[self.email_type]} words
"""

    def _get_type_specific_structure(self) -> str:
        """Get email type-specific structure guidance"""
        structures = {
            'indirect': """
1. Hook - Challenge belief/share surprise (1-2 sentences)
2. Story - Specific client case study (3-4 sentences)
3. Faulty Belief - Why common approach fails (2-3 sentences)
4. Truth - What actually works (2-3 sentences)
5. Proof - Additional evidence (1-2 sentences)
6. Bridge - Connect to reader (1-2 sentences)
7. CTA - Single clear action (1-2 sentences)""",

            'value': """
1. Hook - Personal credibility (2-3 sentences)
2. Problem Recognition (2-3 sentences)
3. Value Delivery - Main tool/system (8-12 sentences)
4. Soft CTA (1-2 sentences)""",

            'direct': """
1. Direct Hook - Question/assumption (1-2 sentences)
2. Value/Reason - Why now (2-3 sentences)
3. Clear CTA - Single action (1-2 sentences)"""
        }

        return structures.get(self.email_type, structures['indirect'])

    def get_optimal_metrics(self) -> Dict[str, Any]:
        """Return email optimal performance metrics"""
        return {
            'subject_line': {
                'min_chars': self.SUBJECT_MIN_CHARS,
                'max_chars': self.SUBJECT_MAX_CHARS,
                'optimal_chars': (30, 40),
                'optimal_words': self.SUBJECT_OPTIMAL_WORDS
            },
            'body_length': {
                'min': self.MIN_WORD_COUNT[self.email_type],
                'max': self.MAX_WORD_COUNT[self.email_type]
            },
            'cta_count': 1,
            'email_type': self.email_type
        }

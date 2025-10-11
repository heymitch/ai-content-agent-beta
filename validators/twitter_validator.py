"""
Twitter/X content validator with thread-specific rules
Validates thread structure, character limits, and engagement patterns
"""
import re
from typing import List, Dict, Any
from .base_validator import BaseValidator
from .pattern_library import ForbiddenPatterns, ContentQualityChecks

class TwitterValidator(BaseValidator):
    """Validates Twitter/X content with thread structure and character limits"""

    # Twitter metrics
    MAX_TWEET_LENGTH = 280
    OPTIMAL_TWEET_LENGTH = 250  # Leave room for edits
    MAX_THREAD_LENGTH = 25
    OPTIMAL_THREAD_LENGTH = 7-10  # Sweet spot for engagement

    def validate(self, content: str) -> List[Dict[str, Any]]:
        """
        Run deterministic validation checks for Twitter

        Args:
            content: Twitter thread content (tweets separated by double newlines)

        Returns:
            List of validation issues
        """
        issues = []

        # Parse thread structure (tweets separated by \n\n)
        tweets = [t.strip() for t in content.split('\n\n') if t.strip()]

        if not tweets:
            return [{
                'type': 'empty_thread',
                'severity': 'high',
                'auto_fixable': False,
                'message': 'No content found. Thread cannot be empty.'
            }]

        # 1. Check forbidden patterns (shared library)
        pattern_issues = ForbiddenPatterns.check_content(content)
        issues.extend(pattern_issues)

        # 2. Check thread length
        thread_length_issue = self._check_thread_length(tweets)
        if thread_length_issue:
            issues.append(thread_length_issue)

        # 3. Check individual tweet character limits
        tweet_length_issues = self._check_tweet_lengths(tweets)
        issues.extend(tweet_length_issues)

        # 4. Check hook tweet (first tweet)
        hook_issue = self._check_hook_tweet(tweets[0])
        if hook_issue:
            issues.append(hook_issue)

        # 5. Check thread structure
        structure_issue = self._check_thread_structure(tweets)
        if structure_issue:
            issues.append(structure_issue)

        # 6. Check CTA/engagement (last tweet)
        cta_issue = self._check_thread_cta(tweets[-1])
        if cta_issue:
            issues.append(cta_issue)

        # 7. Check for specificity (numbers/data)
        specificity_issue = ContentQualityChecks.check_specificity(content)
        if specificity_issue:
            issues.append(specificity_issue)

        return issues

    def _check_thread_length(self, tweets: List[str]) -> Dict[str, Any]:
        """Check if thread length is optimal"""
        tweet_count = len(tweets)

        if tweet_count > self.MAX_THREAD_LENGTH:
            return {
                'type': 'thread_too_long',
                'severity': 'high',
                'auto_fixable': False,
                'message': f'Thread has {tweet_count} tweets (max: {self.MAX_THREAD_LENGTH}). Break into multiple threads.',
                'current': tweet_count,
                'maximum': self.MAX_THREAD_LENGTH
            }

        if tweet_count == 1:
            return {
                'type': 'single_tweet',
                'severity': 'low',
                'auto_fixable': False,
                'message': 'Thread has only 1 tweet. Consider expanding to 3-7 tweets for better engagement.',
                'current': 1
            }

        if tweet_count > 15:
            return {
                'type': 'thread_long',
                'severity': 'medium',
                'auto_fixable': False,
                'message': f'Thread has {tweet_count} tweets. Optimal range: 7-10 for engagement.',
                'current': tweet_count
            }

        return None

    def _check_tweet_lengths(self, tweets: List[str]) -> List[Dict[str, Any]]:
        """Check character count for each tweet"""
        issues = []

        for i, tweet in enumerate(tweets):
            char_count = len(tweet)

            if char_count > self.MAX_TWEET_LENGTH:
                issues.append({
                    'type': 'tweet_too_long',
                    'severity': 'high',
                    'auto_fixable': False,
                    'message': f'Tweet #{i+1} is {char_count} chars (max: {self.MAX_TWEET_LENGTH}). Shorten it.',
                    'tweet_number': i + 1,
                    'current': char_count,
                    'maximum': self.MAX_TWEET_LENGTH,
                    'tweet_preview': tweet[:50] + '...'
                })

            elif char_count > self.OPTIMAL_TWEET_LENGTH:
                issues.append({
                    'type': 'tweet_near_limit',
                    'severity': 'low',
                    'auto_fixable': False,
                    'message': f'Tweet #{i+1} is {char_count} chars (optimal: <{self.OPTIMAL_TWEET_LENGTH}). Leave room for edits.',
                    'tweet_number': i + 1,
                    'current': char_count
                })

        return issues

    def _check_hook_tweet(self, first_tweet: str) -> Dict[str, Any]:
        """Validate the hook tweet (most critical for engagement)"""
        # Hook should be punchy (under 200 chars for preview)
        if len(first_tweet) > 200:
            return {
                'type': 'hook_too_long',
                'severity': 'medium',
                'auto_fixable': False,
                'message': f'Hook tweet is {len(first_tweet)} chars. Keep under 200 for full preview.',
                'current': len(first_tweet)
            }

        # Hook shouldn't be a question
        if first_tweet.strip().endswith('?'):
            return {
                'type': 'hook_question',
                'severity': 'high',
                'auto_fixable': False,
                'message': f'Hook tweet ends with question: "{first_tweet}". Use bold statement instead.'
            }

        # Hook should contain specific claim
        if not re.search(r'\d+', first_tweet):
            return {
                'type': 'hook_vague',
                'severity': 'medium',
                'auto_fixable': False,
                'message': 'Hook tweet has no numbers. Start with specific claim or metric.'
            }

        return None

    def _check_thread_structure(self, tweets: List[str]) -> Dict[str, Any]:
        """Check for good thread flow"""
        # Threads should have value-dense middle tweets
        if len(tweets) >= 3:
            middle_tweets = tweets[1:-1]

            # Check if middle tweets are too short (likely fluff)
            short_middle = [i for i, t in enumerate(middle_tweets, start=2) if len(t) < 50]

            if len(short_middle) > len(middle_tweets) / 2:
                return {
                    'type': 'weak_middle',
                    'severity': 'medium',
                    'auto_fixable': False,
                    'message': f'Tweets {short_middle} are too short (<50 chars). Add more value.',
                    'short_tweets': short_middle
                }

        return None

    def _check_thread_cta(self, last_tweet: str) -> Dict[str, Any]:
        """Check for engagement CTA in last tweet"""
        cta_patterns = [
            r'\bfollow\b',
            r'\bretweet\b',
            r'\blike\b',
            r'\bshare\b',
            r'\bthoughts\?',
            r'\bcomment\b',
            r'\bthread\b.*below',
            r'\bcheck out\b',
            r'\blearn more\b',
        ]

        has_cta = any(re.search(pattern, last_tweet.lower()) for pattern in cta_patterns)

        if not has_cta:
            return {
                'type': 'missing_cta',
                'severity': 'medium',
                'auto_fixable': False,
                'message': 'Last tweet has no CTA. Add follow prompt, share request, or engagement hook.'
            }

        return None

    def get_grading_rubric(self) -> str:
        """Return Twitter grading criteria for Claude"""
        return """
TWITTER THREAD GRADING RUBRIC (0-100):

**Hook Quality (30 points)**
- First tweet grabs attention with bold claim
- Under 200 chars for full preview
- Contains specific number or metric
- No rhetorical questions

**Value Delivery (30 points)**
- Each tweet adds new insight (not fluff)
- Concrete examples and data
- Logical flow from tweet to tweet
- Actionable takeaways

**Engagement Potential (20 points)**
- Clear CTA in last tweet (follow, share, comment)
- Thread length optimized (7-10 tweets ideal)
- Hooks curiosity for continued reading

**Format & Readability (20 points)**
- Each tweet under 280 chars (optimal: <250)
- Clear thread structure (hook → value → CTA)
- No AI clichés or generic phrases

**CRITICAL VIOLATIONS (Auto -30 points each):**
- Any tweet over 280 characters
- Hook tweet is a question
- No numbers/specificity in thread
- AI clichés ("here's the thing", "picture this")

**OPTIMAL METRICS:**
- Thread length: 7-10 tweets (sweet spot)
- Hook tweet: 150-200 chars
- Each tweet: 200-250 chars
- Numbers: 3-5 concrete data points across thread
"""

    def get_writing_rules(self) -> str:
        """Return Twitter writing guidelines"""
        return """
TWITTER THREAD WRITING RULES:

**Structure:**
1. Hook Tweet (1st): Bold claim with specific number (<200 chars)
2. Value Tweets (2-9): One insight per tweet, build logically
3. CTA Tweet (last): Clear call-to-action (follow, share, engage)

**Mandatory Elements:**
- ✅ Hook with specific claim (NO questions)
- ✅ 3-5 concrete numbers/metrics across thread
- ✅ Each tweet under 280 chars (optimal: 200-250)
- ✅ Logical flow (each tweet builds on previous)
- ✅ Clear CTA in last tweet

**Forbidden:**
- ❌ Tweets over 280 characters
- ❌ Hook tweet as question
- ❌ Contrast framing ("not X, but Y")
- ❌ AI clichés ("here's the thing", "picture this")
- ❌ Vague language ("several ways", "many reasons")
- ❌ Threads over 15 tweets (loses engagement)

**Style Guidelines:**
- One idea per tweet
- Use line breaks within tweets sparingly
- Front-load value in each tweet
- Use specific examples and data
- Build curiosity between tweets
- End with strong CTA

**Thread Length Guide:**
- 3-5 tweets: Quick insight
- 7-10 tweets: Deep dive (OPTIMAL for engagement)
- 11-15 tweets: Comprehensive guide
- 16+ tweets: Risk losing readers

**Engagement Tactics:**
- Hook promises specific value ("7 ways...")
- Use numbered threads ("1/7") for clarity
- Include surprising data or counterintuitive insight
- End with "Follow for more [topic]" or "Share if valuable"
"""

    def get_optimal_metrics(self) -> Dict[str, Any]:
        """Return Twitter optimal performance metrics"""
        return {
            'thread_length': {
                'min': 3,
                'max': 15,
                'optimal_min': 7,
                'optimal_max': 10
            },
            'hook_tweet': {
                'max_chars': 200,
                'optimal_chars': 150
            },
            'tweet_length': {
                'max': 280,
                'optimal': 250
            },
            'numbers_count': {
                'min': 3,
                'optimal': 5
            },
            'cta_required': True
        }

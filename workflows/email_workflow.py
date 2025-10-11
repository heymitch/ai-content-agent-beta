"""
Email workflow implementation with support for Value, Indirect, and Direct types
Based on n8n PGA email generation patterns
"""
from .base_workflow import ContentWorkflow
import sys
import os

# Add parent directory to path for validator imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from validators.email_validator import EmailValidator

class EmailWorkflow(ContentWorkflow):
    """Email creation workflow with 3-agent pattern (supports Value/Indirect/Direct)"""

    def __init__(self, supabase_client, email_type: str = 'indirect'):
        """
        Initialize Email workflow

        Args:
            supabase_client: Supabase client instance
            email_type: One of 'value', 'indirect', 'direct' (from n8n analyzer)
        """
        self.email_type = email_type.lower()

        super().__init__(
            platform=f"email_{self.email_type}",  # email_indirect, email_value, email_direct
            validator_class=lambda: EmailValidator(email_type=self.email_type),
            supabase_client=supabase_client
        )

    def _get_platform_rules(self) -> str:
        """Override to include email-specific emphasis"""
        base_rules = super()._get_platform_rules()

        email_emphasis = f"""

**EMAIL ({self.email_type.upper()}) PRIORITY:**
- Format: Subject line + body (use "Subject: ..." on first line)
- Subject length: 30-40 characters (5-7 words for mobile optimization)
- Body length: {self._get_word_count_guidance()}
- CTA format: Use backticks like `{{call_cta}}` or `{{app_cta}}` or `{{ghost_cta}}`
- Formatting: One sentence per line (n8n requirement)
- Sign-off: End with "Cole" or "Dickie"

**{self.email_type.upper()} EMAIL STRUCTURE:**
{self._get_type_structure()}

**SPAM AVOIDANCE:**
- NO all caps words
- NO multiple exclamation marks
- NO spam triggers ("free money", "guaranteed", "act now", "click here")
- NO multiple CTAs (use exactly ONE)

**EXAMPLE FORMAT:**
```
Subject: [Conversational hook 30-40 chars]

[Hook sentence]
[Value delivery]
[Additional context]

[Social proof or case study if relevant]

[CTA sentence with variable]
Book a call: `{{call_cta}}`

Cole
```
"""
        return base_rules + email_emphasis

    def _get_word_count_guidance(self) -> str:
        """Get word count based on email type"""
        counts = {
            'value': '400-500 words',
            'indirect': '400-600 words',
            'direct': '100-200 words'
        }
        return counts.get(self.email_type, '400-600 words')

    def _get_type_structure(self) -> str:
        """Get structure guidance for email type"""
        structures = {
            'indirect': """
1. Hook - Challenge common belief or share surprise
2. Story - Specific client case study with results
3. Faulty Belief - Why conventional wisdom fails
4. Truth - Counter-intuitive approach that works
5. Proof - Additional evidence or examples
6. Bridge - Connect to reader's situation
7. CTA - Single clear call-to-action""",

            'value': """
1. Hook - Personal credibility or tool introduction
2. Problem Recognition - What audience struggles with
3. Value Delivery - How tool/system solves it (main body)
4. Soft CTA - Optional next step""",

            'direct': """
1. Direct Hook - Question or assumption of readiness
2. Value Bullets - 2-3 specific benefits
3. Urgency - Time-sensitive element
4. Clear CTA - Single action to take"""
        }

        return structures.get(self.email_type, structures['indirect'])

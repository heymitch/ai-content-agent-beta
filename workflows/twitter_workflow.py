"""
Twitter/X-specific workflow implementation
Extends base workflow with Twitter validator and thread formatting
"""
from .base_workflow import ContentWorkflow
import sys
import os

# Add parent directory to path for validator imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from validators.twitter_validator import TwitterValidator

class TwitterWorkflow(ContentWorkflow):
    """Twitter/X thread creation workflow with 3-agent pattern"""

    def __init__(self, supabase_client):
        """
        Initialize Twitter workflow

        Args:
            supabase_client: Supabase client instance
        """
        super().__init__(
            platform="twitter",
            validator_class=TwitterValidator,
            supabase_client=supabase_client
        )

    def _get_platform_rules(self) -> str:
        """Override to include Twitter-specific emphasis"""
        base_rules = super()._get_platform_rules()

        twitter_emphasis = """

**TWITTER THREAD PRIORITY:**
- Thread format: Each tweet separated by double newline (\\n\\n)
- Character limits: Max 280 per tweet (optimal: 200-250)
- Hook tweet: Bold claim with number (<200 chars, NO question)
- Thread flow: One insight per tweet, build logically
- CTA required: Last tweet should prompt follow/share/engage
- Optimal length: 7-10 tweets for maximum engagement
- Number tweets: Use "1/7", "2/7" format for clarity

**THREAD STRUCTURE EXAMPLE:**
```
Our AI workflow cut content production by 73% in Q3. Here's the exact system:

1. Research Agent analyzed 840 data sources in 4 minutes (vs 45 min manual)

2. Writing Agent used 22 proven frameworks to draft in 45 minutes (vs 4 hours)

3. Quality Agent ran 127-point checks, reducing edits from 5 rounds to 1

Results: 400+ pieces in Q3, 92% client satisfaction, zero compliance issues

Follow for more AI workflow insights
```
"""
        return base_rules + twitter_emphasis

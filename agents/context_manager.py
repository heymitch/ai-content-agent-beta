"""
Context Manager for Batch Content Execution
Routes strategic context to each post (NO learning accumulation)

Simplified from v1: Removed learning extraction, compaction, and quality trend analysis.
Focus: Pass user's strategic outline + optional strategy memory to each post.
"""

from typing import Dict, List, Any, Optional


class ContextManager:
    """
    Routes strategic context to each post in a batch.

    NO learning accumulation - each post uses user's strategic outline.
    Optional strategy memory (compacted conversation history) can be included.
    """

    def __init__(self, plan_id: str, plan: Optional[Dict[str, Any]] = None):
        """
        Initialize context manager for a batch execution

        Args:
            plan_id: Unique identifier for this content batch
            plan: Batch plan with detailed_outlines and optional strategy_memory
        """
        self.plan_id = plan_id
        self.plan = plan or {}

        # Extract strategic outlines from plan
        self.detailed_outlines = []
        if self.plan.get('posts'):
            self.detailed_outlines = [
                post.get('detailed_outline', post.get('context', ''))
                for post in self.plan['posts']
            ]

        # Optional strategy memory (compacted from last 5 conversations)
        self.strategy_memory = self.plan.get('strategy_memory', '')

        # Simple tracking (no learning accumulation)
        self.total_posts = 0
        self.scores = []

    def get_context_for_post(self, post_index: int) -> str:
        """
        Get context for specific post - NO compaction, NO learning

        Returns:
            Strategic outline + optional strategy memory
        """
        # Get strategic outline for this specific post
        outline = ''
        if post_index < len(self.detailed_outlines):
            outline = self.detailed_outlines[post_index]

        # Build context with strategic outline
        context = f"""**STRATEGIC OUTLINE FOR THIS POST:**
{outline}"""

        # Add strategy memory if present (optional, already compacted to 1k tokens)
        if self.strategy_memory:
            context += f"""

**RELEVANT PAST DISCUSSIONS (Compacted):**
{self.strategy_memory[:1000]}  # Enforce 1k token limit

**INSTRUCTION:** Use past discussions for consistency in tone and topics.
Do NOT try to "improve" on previous posts - each post is independent with its own strategic outline.
"""

        return context

    async def add_post_summary(self, summary: Dict[str, Any]):
        """
        Track post completion (NO learning extraction)

        Args:
            summary: {
                'post_num': int,
                'score': int (out of 25),
                'hook': str (first 100 chars),
                'platform': str,
                'airtable_url': str
            }
        """
        self.total_posts += 1

        # Track score for stats only (no learning extraction)
        if 'score' in summary:
            self.scores.append(summary['score'])

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns simple stats for checkpoint messages

        Returns:
            Dictionary with:
            - total_posts: int
            - avg_score: float
            - recent_scores: List[int] (last 10)
            - lowest_score: int
            - highest_score: int
        """
        if not self.scores:
            return {
                'total_posts': 0,
                'avg_score': 0,
                'recent_scores': [],
                'lowest_score': 0,
                'highest_score': 0,
                'quality_trend': 'N/A'
            }

        avg_score = sum(self.scores) / len(self.scores)
        recent_scores = self.scores[-10:] if len(self.scores) >= 10 else self.scores

        # Simple quality trend (for checkpoint messages)
        if len(self.scores) >= 2:
            first_half_avg = sum(self.scores[:len(self.scores)//2]) / (len(self.scores)//2)
            second_half_avg = sum(self.scores[len(self.scores)//2:]) / (len(self.scores) - len(self.scores)//2)

            if second_half_avg > first_half_avg + 1:
                quality_trend = "improving"
            elif second_half_avg < first_half_avg - 1:
                quality_trend = "declining"
            else:
                quality_trend = "stable"
        else:
            quality_trend = "too early to tell"

        return {
            'total_posts': self.total_posts,
            'avg_score': avg_score,
            'average_score': avg_score,  # Alias for consistency
            'recent_scores': recent_scores,
            'quality_trend': quality_trend,
            'lowest_score': min(self.scores),
            'highest_score': max(self.scores)
        }

    def add_strategic_context(self, post_index: int, strategic_outline: str):
        """
        Store strategic outline for tracking alignment

        Args:
            post_index: Which post in the batch
            strategic_outline: The original user-provided outline
        """
        if not hasattr(self, 'strategic_outlines'):
            self.strategic_outlines = {}

        self.strategic_outlines[post_index] = strategic_outline

    def check_alignment(self, post_index: int, generated_content: str) -> float:
        """
        Check how well generated content aligns with strategic outline

        Returns:
            Alignment score 0-1 (1 = perfect alignment)
        """
        if not hasattr(self, 'strategic_outlines'):
            return 1.0  # No outline to check against

        outline = self.strategic_outlines.get(post_index, '')
        if not outline:
            return 1.0

        # Simple check: key phrases from outline appear in content
        outline_words = set(outline.lower().split())
        content_words = set(generated_content.lower().split())

        overlap = len(outline_words & content_words)
        alignment = overlap / len(outline_words) if outline_words else 1.0

        if alignment < 0.5:
            print(f"⚠️ WARNING: Generated content has low alignment ({alignment:.1%}) with strategic outline")

        return alignment

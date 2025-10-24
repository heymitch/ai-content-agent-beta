"""
Context Manager for Batch Content Execution
Manages context accumulation and compaction per Anthropic best practices

Reference: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
"""

import os
from typing import Dict, List, Any
from anthropic import Anthropic


class ContextManager:
    """
    Manages context across N-post batch with compaction every 10 posts

    Implements Anthropic's context engineering best practices:
    - Treats context as precious resource
    - Compacts every 10 posts (20k tokens → 2k tokens)
    - Returns condensed learnings for next post
    - Tracks quality progression over batch
    """

    def __init__(self, plan_id: str):
        """
        Initialize context manager for a batch execution

        Args:
            plan_id: Unique identifier for this content batch
        """
        self.plan_id = plan_id
        self.learnings = []  # List of post summaries
        self.posts_since_compact = 0
        self.total_posts = 0
        self.scores = []

    async def add_post_summary(self, summary: Dict[str, Any]):
        """
        Stores condensed summary from SDK agent workflow

        Args:
            summary: {
                'post_num': int,
                'score': int (out of 25),
                'hook': str (first 100 chars),
                'platform': str,
                'airtable_url': str,
                'what_worked': str (optional)
            }
        """
        self.learnings.append(summary)
        self.scores.append(summary['score'])
        self.posts_since_compact += 1
        self.total_posts += 1

        # Compact every 10 posts to prevent context overflow
        if self.posts_since_compact >= 10:
            await self.compact()

    async def compact(self):
        """
        Every 10 posts: Summarize into key learnings
        Reduces 20k tokens → 2k tokens

        Uses Anthropic Messages API to extract patterns:
        - What hook styles scored highest
        - What content patterns performed well
        - What to avoid in future posts
        """
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        # Build summary of last 10 posts
        summaries = "\n\n".join([
            f"Post {s['post_num']}: {s['platform'].capitalize()}\n"
            f"Score: {s['score']}/25\n"
            f"Hook: {s['hook'][:100]}\n"
            f"What worked: {s.get('what_worked', 'N/A')}"
            for s in self.learnings[-10:]
        ])

        print(f"🔄 Compacting posts {self.total_posts-9} to {self.total_posts}...")

        # Compact using Sonnet 4.5
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Analyze these 10 posts and extract key learnings for improving future posts.

Focus on:
- What hook styles worked best (based on scores)
- What content patterns performed well
- What platform-specific insights emerged
- What to avoid in future posts

Be concise (2000 tokens max). Use bullet points.

Posts analyzed:
{summaries}"""
            }]
        )

        compacted = response.content[0].text
        print(f"✅ Compacted {len(summaries)} chars → {len(compacted)} chars")

        # Replace last 10 summaries with compacted version
        self.learnings = self.learnings[:-10] + [{
            'compacted': True,
            'summary': compacted,
            'posts_range': f"{self.total_posts-9}-{self.total_posts}",
            'avg_score': sum([s['score'] for s in self.learnings[-10:]]) / 10
        }]
        self.posts_since_compact = 0

    def get_compacted_learnings(self) -> str:
        """
        Returns all learnings as string for next post context

        Compacted learnings + recent post summaries = ~5k tokens

        Returns:
            String containing all accumulated learnings
        """
        if not self.learnings:
            return "No previous posts in this batch yet."

        learnings_text = []

        for l in self.learnings:
            if l.get('compacted'):
                # Compacted summary (2k tokens)
                learnings_text.append(
                    f"**Posts {l['posts_range']} (Avg score: {l['avg_score']:.1f}):**\n{l['summary']}"
                )
            else:
                # Recent post summary (100 tokens)
                learnings_text.append(
                    f"- Post {l['post_num']}: Score {l['score']}, Hook: \"{l['hook'][:50]}...\""
                )

        return "\n\n".join(learnings_text)

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns stats for checkpoint messages

        Returns:
            Dictionary with:
            - total_posts: int
            - avg_score: float
            - learnings: str (compacted)
            - recent_scores: List[int] (last 10)
            - quality_trend: str (improving/declining/stable)
        """
        if not self.scores:
            return {
                'total_posts': 0,
                'avg_score': 0,
                'learnings': 'No data yet',
                'recent_scores': [],
                'quality_trend': 'N/A'
            }

        avg_score = sum(self.scores) / len(self.scores)
        recent_scores = self.scores[-10:] if len(self.scores) >= 10 else self.scores

        # Calculate quality trend
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
            'learnings': self.get_compacted_learnings(),
            'recent_scores': recent_scores,
            'quality_trend': quality_trend,
            'lowest_score': min(self.scores),
            'highest_score': max(self.scores)
        }

    def get_target_score(self) -> int:
        """
        Calculate target score for next post
        Aims to improve on batch average

        Returns:
            Target score (18-25)
        """
        if not self.scores:
            return 20  # Default target for first post

        avg = sum(self.scores) / len(self.scores)

        # Aim for +1 above average, capped at 24
        target = int(avg + 1)
        return min(24, max(18, target))

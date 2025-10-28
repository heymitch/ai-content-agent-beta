"""
Base workflow pattern for multi-platform content creation
3-agent pattern: Writer → Validator → Reviser
"""
from anthropic import Anthropic
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

class ContentWorkflow:
    """Base workflow class for platform-specific content creation"""

    def __init__(self, platform: str, validator_class, supabase_client):
        """
        Initialize workflow

        Args:
            platform: Platform name (linkedin, twitter, email, etc.)
            validator_class: Platform-specific validator class
            supabase_client: Supabase client instance
        """
        self.platform = platform
        self.validator = validator_class()
        self.supabase = supabase_client
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    async def execute(
        self,
        brief: str,
        brand_context: str,
        user_id: str = "default",
        max_iterations: int = 3,
        target_score: int = 80
    ) -> Dict[str, Any]:
        """
        Execute full workflow with retry logic

        Args:
            brief: Content creation instructions
            brand_context: Brand voice and guidelines
            user_id: User identifier
            max_iterations: Max revision attempts
            target_score: Minimum quality score threshold

        Returns:
            Dict with draft, grading, and metadata
        """

        # Load platform training examples
        examples = self._fetch_platform_examples()

        # Phase 1: Draft (Sonnet 3.7 for quality)
        print(f"\n{'='*60}")
        print(f"🎨 [{self.platform.upper()}] WRITER AGENT")
        print(f"{'='*60}")
        print(f"📝 Model: claude-3-7-sonnet-20250219")
        print(f"📚 Context: Brand voice + {len(examples.split())} words of examples")
        draft = await self._writer_agent(brief, brand_context, examples)
        print(f"✅ Draft created ({len(draft)} chars)")

        # Phase 2: Validate (Hybrid: Code + Sonnet 4.0)
        print(f"\n{'='*60}")
        print(f"✅ [{self.platform.upper()}] VALIDATOR AGENT")
        print(f"{'='*60}")
        print(f"🔍 Running code-based validation...")
        grading = await self._validator_agent(draft)
        print(f"📊 Score: {grading['score']}/100")
        if grading.get('issues'):
            print(f"⚠️  Issues found: {len(grading['issues'])}")

        # Phase 3: Revise (max iterations)
        iterations = 0
        revision_history = []

        while grading['score'] < target_score and iterations < max_iterations:
            iterations += 1
            print(f"\n{'='*60}")
            print(f"🔄 [{self.platform.upper()}] REVISER AGENT - Iteration {iterations}")
            print(f"{'='*60}")
            print(f"📝 Model: claude-3-7-sonnet-20250219")
            print(f"🎯 Current score: {grading['score']}/100 (target: {target_score})")
            print(f"📋 Feedback: {grading['feedback'][:100]}...")

            # Pass verified facts to reviser if there are factual issues
            verified_facts = grading.get('verified_facts', '')
            draft = await self._reviser_agent(draft, grading['feedback'], brand_context, verified_facts)
            grading = await self._validator_agent(draft)
            print(f"✅ Revision complete - New score: {grading['score']}/100")

            revision_history.append({
                'iteration': iterations,
                'score': grading['score'],
                'issues': grading.get('issues', []),
                'feedback': grading.get('feedback', '')
            })

        # Final summary
        print(f"\n{'='*60}")
        print(f"✅ [{self.platform.upper()}] WORKFLOW COMPLETE")
        print(f"{'='*60}")
        print(f"📊 Final Score: {grading['score']}/100")
        print(f"🔄 Total Iterations: {iterations}")
        print(f"📝 Tools Used:")
        print(f"   - Writer Agent (Sonnet 3.7)")
        print(f"   - Code Validator (deterministic rules)")
        print(f"   - Factual Accuracy Check (Tavily + Sonnet 4.0)")
        print(f"   - LLM Validator (Sonnet 4.0)")
        if iterations > 0:
            print(f"   - Reviser Agent (Sonnet 3.7) × {iterations}")
        print(f"   - Database Examples (RAG from proven_copy_examples)")
        print(f"{'='*60}\n")

        # Log to database
        workflow_log = {
            'platform': self.platform,
            'user_id': user_id,
            'brief': brief[:500],  # Truncate for storage
            'final_draft': draft,
            'final_score': grading['score'],
            'iterations': iterations,
            'revision_history': json.dumps(revision_history, ensure_ascii=False),
            'created_at': datetime.utcnow().isoformat()
        }

        try:
            self.supabase.table('workflow_executions').insert(workflow_log).execute()
        except Exception as e:
            print(f"⚠️ Failed to log workflow: {e}")

        return {
            'draft': draft,
            'grading': grading,
            'iterations': iterations,
            'platform': self.platform,
            'revision_history': revision_history
        }

    async def _writer_agent(self, brief: str, brand_context: str, examples: str) -> str:
        """
        Writer subagent using Claude Sonnet

        Args:
            brief: Content creation instructions
            brand_context: Brand voice and guidelines
            examples: Platform training examples

        Returns:
            Draft content
        """
        # Use system blocks with prompt caching for brand context and examples
        system_blocks = [
            {
                "type": "text",
                "text": f"""You are an expert {self.platform} content writer.

BRAND VOICE & CONTEXT:
{brand_context}

PLATFORM: {self.platform}

PROVEN EXAMPLES FROM THIS PLATFORM:
{examples}

WRITING RULES:
{self._get_platform_rules()}""",
                "cache_control": {"type": "ephemeral"}  # CACHE BRAND + EXAMPLES
            },
            {
                "type": "text",
                "text": """CRITICAL RULES - AUTO-FAIL IF VIOLATED:
• NEVER fabricate case studies, client stories, or fake examples
• NEVER invent people, companies, or results ("Kevin from ContentScale", "helped 4 agencies to $50K MRR")
• NEVER use phrases like "I just helped an agency", "one client implemented", "real results from our latest partner"
• ONLY use real, verified data or speak from genuine personal experience
• If you don't have real examples, focus on frameworks, principles, and actionable insights instead

Write engaging, high-quality content that matches the proven patterns above.
Focus on concrete specificity with numbers, timelines, and measurable outcomes.
Avoid AI clichés and rhetorical questions.

**OUTPUT FORMAT:**
Return ONLY the final post content - no introductions, no meta-commentary, no "Here's a post about...", no "Let me know if you'd like changes".
Start directly with the post hook. End with the final line of the post.
DO NOT add conversational framing before or after the content."""
            }
        ]

        response = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",  # Upgraded to 3.7
            max_tokens=1500,
            temperature=0.7,
            system=system_blocks,
            messages=[{"role": "user", "content": brief}]
        )

        return response.content[0].text

    async def _validator_agent(self, content: str) -> Dict[str, Any]:
        """
        Hybrid validator: Code rules + Claude strategic assessment

        Args:
            content: Content to validate

        Returns:
            Grading dict with score, feedback, issues
        """

        # Phase 1: Code-based validation (deterministic)
        code_issues = self.validator.validate(content)
        print(f"   ├─ Code validation: {len(code_issues)} issues found")

        # Auto-fix deterministic issues if possible
        cleaned_content = content
        auto_fixes = 0
        for issue in code_issues:
            if issue.get('auto_fixable') and 'fix_function' in issue:
                cleaned_content = issue['fix_function'](cleaned_content)
                auto_fixes += 1
        
        if auto_fixes > 0:
            print(f"   ├─ Auto-fixed {auto_fixes} issues")

        # Phase 2: Factual accuracy check with web search
        factual_warnings, verified_facts = await self._check_factual_accuracy(cleaned_content)
        if factual_warnings:
            print(f"   ├─ Factual accuracy: {len(factual_warnings)} claims need verification")
            code_issues.extend(factual_warnings)
        else:
            print(f"   ├─ Factual accuracy: No unverified claims detected")

        # Phase 2.5: Semantic contrast pattern detection (catch ALL forms)
        contrast_warnings = await self._check_semantic_contrast(cleaned_content)
        if contrast_warnings:
            print(f"   ├─ Contrast patterns: {len(contrast_warnings)} AI patterns detected")
            code_issues.extend(contrast_warnings)
        else:
            print(f"   ├─ Contrast patterns: None detected")

        # Phase 3: Claude strategic validation (Sonnet 4.0 for critical analysis)
        print(f"   └─ LLM grading (Sonnet 4.0)...")

        # Include factual accuracy issues in grading context
        factual_context = ""
        if factual_warnings:
            factual_context = f"\n\nFACTUAL ACCURACY WARNINGS:\n"
            for warning in factual_warnings:
                factual_context += f"- {warning['message']}\n"
                if warning.get('contradiction'):
                    factual_context += f"  CONTRADICTION: {warning['contradiction']}\n"

        # Static grading system (cacheable)
        grading_system = f"""Grade {self.platform} content on a scale of 0-100.

GRADING CRITERIA:
{self.validator.get_grading_rubric()}

Analyze:
1. Hook/opening strength
2. Value delivery (concrete insights, specificity)
3. Engagement potential (CTA, thought-provoking end)
4. Brand alignment
5. Factual accuracy (AUTO-FAIL if contradictions detected)

**CRITICAL: If there are factual accuracy warnings, score must be <60 until claims are corrected.**

Return ONLY valid JSON (no markdown, no explanations):
{{
  "score": <0-100>,
  "feedback": "<specific improvements needed>",
  "strengths": ["<what works well>"],
  "issues": ["<remaining problems>"]
}}"""

        # Dynamic content to grade
        user_prompt = f"""CONTENT:
{cleaned_content}
{factual_context}
Grade this content now."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",  # Upgraded to Sonnet 4.0 for critical grading
            max_tokens=800,
            temperature=0.2,  # Lower temp for more consistent grading
            system=[
                {
                    "type": "text",
                    "text": grading_system,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse JSON from response
        response_text = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        try:
            grading = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse grading JSON: {e}")
            grading = {
                "score": 50,
                "feedback": "Error parsing validation response",
                "strengths": [],
                "issues": ["Validation error"]
            }

        # Add code validation metadata
        grading['code_issues_found'] = len(code_issues)
        grading['code_issues_fixed'] = auto_fixes
        grading['code_issues_remaining'] = [
            issue for issue in code_issues if not issue.get('auto_fixable')
        ]
        grading['verified_facts'] = verified_facts

        return grading

    async def _check_factual_accuracy(self, content: str) -> tuple[List[Dict[str, Any]], str]:
        """
        Check factual claims in content using web search

        Args:
            content: Content to fact-check

        Returns:
            Tuple of (issues list, verified facts string)
        """
        from tavily import TavilyClient

        issues = []
        verified_facts_list = []

        # Extract potential factual claims using Claude
        claim_extraction_prompt = f"""Analyze this content and extract ALL factual claims that need verification:

CONTENT:
{content}

Look for:
**EXTERNAL CLAIMS (verify with web search):**
- Specific statistics (percentages, dollar amounts, dates)
- Company announcements or news
- Technology pricing changes
- Industry data or research findings
- Specific events or milestones

**INTERNAL CLAIMS (verify with knowledge base):**
- Case studies or client examples
- Testimonials or client quotes
- Specific client results ("I helped X achieve Y")
- Company track record ("we've worked with 50+ clients")
- Past project outcomes

Return ONLY valid JSON (no markdown):
{{
  "claims": [
    {{
      "claim": "<exact claim from text>",
      "type": "external|internal",
      "category": "statistic|price|event|case_study|testimonial|result",
      "needs_verification": true/false
    }}
  ]
}}

If there are NO specific factual claims (just opinions, advice, frameworks), return:
{{"claims": []}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0,
                messages=[{"role": "user", "content": claim_extraction_prompt}]
            )

            response_text = response.content[0].text.strip()

            # Remove markdown if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            claims_data = json.loads(response_text)
            claims = claims_data.get('claims', [])

            if not claims:
                return [], ""  # No factual claims to verify

            # Verify each claim using appropriate source
            tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

            for claim_obj in claims:
                if not claim_obj.get('needs_verification'):
                    continue

                claim = claim_obj['claim']
                claim_type = claim_obj.get('type', 'general')
                category = claim_obj.get('category', 'statistic')

                # Internal claims: check knowledge base
                if claim_type == 'internal':
                    try:
                        # Search knowledge base via RAG
                        kb_results = await self._search_knowledge_base(claim)

                        if not kb_results:
                            # No RAG support for this claim
                            issues.append({
                                'code': 'claim_unverified_internal',
                                'severity': 'high',
                                'message': f"Internal claim not found in knowledge base: '{claim}'",
                                'explanation': 'Case studies, testimonials, and client results must exist in knowledge base. Remove claim or add supporting documentation.',
                                'auto_fixable': False
                            })
                            verified_facts_list.append({
                                'claim': claim,
                                'verified': False,
                                'evidence': 'Not found in knowledge base',
                                'sources': []
                            })
                        else:
                            # Found in knowledge base
                            verified_facts_list.append({
                                'claim': claim,
                                'verified': True,
                                'evidence': kb_results,
                                'sources': ['Knowledge Base']
                            })
                    except Exception as kb_error:
                        print(f"⚠️ Knowledge base check failed for '{claim}': {kb_error}")
                    continue

                # External claims: web search
                try:
                    search_results = tavily_client.search(
                        query=claim,
                        max_results=3,
                        include_answer=True
                    )

                    # Ask Claude to verify the claim against search results
                    verification_prompt = f"""Verify this claim against search results:

CLAIM: {claim}

SEARCH RESULTS:
{json.dumps(search_results.get('results', [])[:3], indent=2)}

Does the evidence SUPPORT or CONTRADICT this claim?

Return ONLY valid JSON:
{{
  "verified": true/false,
  "confidence": "high|medium|low",
  "explanation": "<brief explanation>",
  "contradiction": "<specific contradiction if found, else null>"
}}"""

                    verify_response = self.client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=300,
                        temperature=0,
                        messages=[{"role": "user", "content": verification_prompt}]
                    )

                    verify_text = verify_response.content[0].text.strip()
                    if verify_text.startswith('```'):
                        verify_text = verify_text.split('```')[1]
                        if verify_text.startswith('json'):
                            verify_text = verify_text[4:]
                        verify_text = verify_text.strip()

                    verification = json.loads(verify_text)

                    # Store verified facts for reviser
                    if verification.get('verified'):
                        verified_facts_list.append({
                            'claim': claim,
                            'verified': True,
                            'evidence': search_results.get('answer', ''),
                            'sources': [r.get('url', '') for r in search_results.get('results', [])[:2]]
                        })

                    # Flag unverified or contradicted claims
                    if not verification.get('verified') or verification.get('contradiction'):
                        issues.append({
                            'code': 'claim_unverified',
                            'severity': 'high',
                            'message': f"Factual claim needs verification: '{claim}'",
                            'explanation': verification.get('explanation', 'Could not verify'),
                            'contradiction': verification.get('contradiction'),
                            'auto_fixable': False
                        })
                        # Also store what we found for reviser
                        verified_facts_list.append({
                            'claim': claim,
                            'verified': False,
                            'evidence': verification.get('explanation', ''),
                            'contradiction': verification.get('contradiction'),
                            'sources': [r.get('url', '') for r in search_results.get('results', [])[:2]]
                        })

                except Exception as search_error:
                    print(f"⚠️ Failed to verify claim '{claim}': {search_error}")
                    # Don't fail the whole validation, just skip this claim
                    continue

        except Exception as e:
            print(f"⚠️ Factual accuracy check error: {e}")
            return [], ""  # Don't block on fact-check failures

        # Format verified facts for reviser
        verified_facts_str = "\n".join([
            f"- {f['claim']}: {'✓ VERIFIED' if f['verified'] else '✗ UNVERIFIED'}\n  {f['evidence']}\n  Sources: {', '.join(f['sources'])}"
            for f in verified_facts_list
        ])

        return issues, verified_facts_str

    async def _check_semantic_contrast(self, content: str) -> List[Dict[str, Any]]:
        """
        Use Sonnet 4.0 to detect ALL forms of contrast patterns semantically.
        Catches variations that regex can't: "go beyond X to Y", "don't only focus on X", etc.

        Args:
            content: Content to check for contrast patterns

        Returns:
            List of contrast pattern issues
        """
        issues = []

        contrast_detection_prompt = f"""Analyze this content for AI contrast patterns (not X but Y structure).

CONTENT:
{content}

**CRITICAL DETECTION TASK:**
Find ANY sentence that uses contrast structure to make a point. This includes:

**Direct Forms:**
- "This isn't about X—it's about Y"
- "It's not X, it's Y"
- "They aren't just X—they're Y"
- "Not just X, but Y"
- "The problem isn't X—it's Y"

**Subtle/Masked Forms:**
- "Rather than X, focus on Y"
- "Instead of X, consider Y"
- "Don't only focus on X, focus on Y"
- "Go beyond X to Y"
- "More than X, it's Y"
- "Less about X, more about Y"
- ANY form where negative statement about X is immediately followed by positive statement about Y

**What to IGNORE (acceptable):**
- Spaced reframes with 3+ sentences between negative and positive
- Simple comparisons without negation ("X is good, Y is better")
- Historical context ("We used to do X. Now we do Y.")

Return ONLY valid JSON (no markdown):
{{
  "patterns_found": [
    {{
      "text": "<exact text from content>",
      "pattern_type": "direct|masked|subtle",
      "explanation": "<why this is contrast pattern>",
      "suggested_fix": "<direct positive assertion alternative>"
    }}
  ]
}}

If NO contrast patterns found, return:
{{"patterns_found": []}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                temperature=0,
                messages=[{"role": "user", "content": contrast_detection_prompt}]
            )

            response_text = response.content[0].text.strip()

            # Remove markdown if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            result = json.loads(response_text)
            patterns = result.get('patterns_found', [])

            for pattern in patterns:
                issues.append({
                    'code': 'contrast_semantic',
                    'severity': 'high',
                    'message': f"AI contrast pattern detected: '{pattern['text']}'",
                    'explanation': pattern.get('explanation', 'Contrast structure detected'),
                    'suggested_fix': pattern.get('suggested_fix', 'Rewrite as direct positive assertion'),
                    'auto_fixable': False
                })

        except Exception as e:
            print(f"⚠️ Semantic contrast detection error: {e}")
            return []  # Don't block on detection failures

        return issues

    async def _search_knowledge_base(self, query: str) -> str:
        """
        Search knowledge base for internal claims (case studies, testimonials, etc.)

        Args:
            query: The claim to search for

        Returns:
            Relevant knowledge base content or empty string
        """
        try:
            # Query embeddings table for relevant documents
            results = self.supabase.rpc(
                'match_documents',
                {
                    'query_embedding': await self._get_embedding(query),
                    'match_threshold': 0.7,
                    'match_count': 3
                }
            ).execute()

            if results.data:
                # Combine relevant chunks
                relevant_content = "\n\n".join([
                    doc.get('content', '') for doc in results.data
                ])
                return relevant_content[:500]  # Limit to 500 chars
            return ""
        except Exception as e:
            print(f"⚠️ Knowledge base search error: {e}")
            return ""

    async def _get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text"""
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')

        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def _reviser_agent(self, draft: str, feedback: str, brand_context: str, verified_facts: str = "") -> str:
        """
        Reviser subagent using Claude Sonnet

        Args:
            draft: Current draft
            feedback: Validation feedback
            brand_context: Brand voice and guidelines
            verified_facts: Web-verified facts to use instead of hallucinating

        Returns:
            Revised content
        """
        # Use system blocks with caching for brand context
        system_blocks = [
            {
                "type": "text",
                "text": f"""You are a content editor for {self.platform}.

BRAND CONTEXT:
{brand_context}

PLATFORM RULES:
{self._get_platform_rules()}""",
                "cache_control": {"type": "ephemeral"}  # CACHE BRAND CONTEXT
            },
            {
                "type": "text",
                "text": """CRITICAL: NEVER fabricate case studies, client stories, or fake examples.
NEVER invent people, companies, or results.
Only use real, verified data or speak from genuine personal experience.

If factual claims are flagged as incorrect, you MUST either:
1. Use the verified facts provided from web search
2. Remove the claim entirely if no verified facts available
3. Replace with a general principle/framework that doesn't require verification

DO NOT make up new numbers or claims. DO NOT guess corrections.

Improve the draft based on feedback while maintaining the core message and brand voice.

**OUTPUT FORMAT:**
Return ONLY the revised post content - nothing else.
No "Here's the revised version", no "I've updated...", no "Let me know if..."
Start with the post hook, end with the final line.
DO NOT add any conversational text before or after the content."""
            }
        ]

        revision_prompt = f"""Revise this {self.platform} content based on specific feedback.

ORIGINAL DRAFT:
{draft}

FEEDBACK TO ADDRESS:
{feedback}"""

        if verified_facts:
            revision_prompt += f"""

WEB-VERIFIED FACTS (use these instead of guessing):
{verified_facts}"""

        response = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",  # Upgraded to 3.7
            max_tokens=1500,
            temperature=0.5,
            system=system_blocks,
            messages=[{"role": "user", "content": revision_prompt}]
        )

        return response.content[0].text

    def _fetch_platform_examples(self, limit: int = 5) -> str:
        """
        Fetch top-performing content for this platform

        Args:
            limit: Max number of examples to fetch

        Returns:
            Formatted examples string
        """
        try:
            # Query platform-specific column
            column_name = f'{self.platform}_copy'

            response = self.supabase.table('proven_copy_examples')\
                .select(f'{column_name}, performance_score, hooks_used')\
                .not_.is_(column_name, 'null')\
                .order('performance_score', desc=True)\
                .limit(limit)\
                .execute()

            if not response.data:
                return f"No {self.platform} examples available yet. Use best practices for the platform."

            examples = []
            for item in response.data:
                hooks = item.get('hooks_used', [])
                if isinstance(hooks, list):
                    hooks_str = ', '.join(hooks)
                else:
                    hooks_str = str(hooks)

                examples.append(f"""
Example (Score: {item.get('performance_score', 'N/A')}):
{item[column_name]}
Hooks Used: {hooks_str}
---""")

            return '\n'.join(examples)

        except Exception as e:
            print(f"⚠️ Failed to fetch examples: {e}")
            return f"No {self.platform} examples available. Use platform best practices."

    def _get_platform_rules(self) -> str:
        """
        Get platform-specific writing rules from validator

        Returns:
            Writing rules string
        """
        return self.validator.get_writing_rules()

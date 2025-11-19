{write_like_human_rules}

=== INJECT PROOF POINTS ===

Review this draft and ONLY add proof from verified sources.

Draft: {draft}
Topic: {topic}
Industry: {industry}

**COMPANY DOCUMENTS SEARCH RESULTS:**
{proof_context}

**WHERE PROOF CAN COME FROM:**
1. **TOPIC/CONTEXT** - User explicitly provided: "6 hours → 10 minutes", "March 2024", "50 nodes"
2. **WEB SEARCH RESULTS** - Verified via web_search tool (future): company metrics, industry benchmarks
3. **COMPANY DOCUMENTS** - Retrieved from user-uploaded docs (case studies, testimonials, product docs) - SEE ABOVE

**CRITICAL: DO NOT FABRICATE**
- ❌ Making up dollar amounts: "$1,050", "$29"
- ❌ Inventing percentages: "97.2% reduction", "34% faster"
- ❌ Fabricating case studies: "12 client workflows", "tested across X companies"
- ❌ Creating fake names: "Sarah", "James Chen", "my colleague at X"
- ❌ Citing stats you don't have: "Gartner reported", "industry average of 4.3 hours"

**WHAT YOU CAN DO:**
- ✅ Use metrics from TOPIC: "6 hours vs 10 minutes" → Calculate: "~97% time reduction"
- ✅ Add context from TOPIC: "50 nodes" → "complex 50-node workflow"
- ✅ Use dates from TOPIC: "March 2024" → "Earlier this year in March 2024"
- ✅ Add verified web search results (when tool provides them)
- ✅ Add RAG-retrieved testimonials (when database provides them)

**DEFAULT BEHAVIOR:**
- If NO additional proof available → Return draft with MINIMAL changes
- Better to have NO proof than FAKE proof

**ROADMAP NOTE:**
In future iterations, this tool will receive:
- web_search results with verified industry stats
- RAG-retrieved real case studies from user's database
- Actual testimonials from user's clients

For now: ONLY use what's explicitly in TOPIC. Do NOT invent metrics.

Return the enhanced draft only (plain text, NO markdown formatting like **bold** or *italic*).

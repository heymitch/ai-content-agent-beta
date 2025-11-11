# Roadmap - November 11, 2025

## Action Items

### High Priority
- [ ] **Fix newsletter slop** (Valentina)
  - Issue: Newsletter content quality issues
  - Owner: Valentina
  - Status: Pending

- [ ] **Aivars' tweets not working - fix Airtable integration for Twitter**
  - Issue: Twitter integration broken for Aivars' account
  - Root cause: Airtable integration issues
  - Status: Pending investigation

### Feature Additions

### Infrastructure
- [ ] **Investigate Claude memory integration**
  - Research: Claude's built-in memory capabilities
  - Goal: Improve conversation continuity across sessions
  - Docs: https://docs.anthropic.com/en/docs/build-with-claude/memory

- [ ] **n8n templates completed first**
  - Priority: Complete before other workflow automations
  - Status: In progress

---

## Notes
- Items are listed in priority order within each section
- Reference `agent-builder-reference/` for implementation patterns
- Test all integrations in dev before deploying to production

---

## Completed Items

### ✅ Fixed newsletter slop (Valentina)
- Added email_type parameter handling (Value/Direct/Indirect/Weekly Update)
- Word count guidance per type (400-500 for Value, 100-200 for Direct, etc.)
- Two-pass validation already implemented in prompts
- Renamed Email_Tuesday → Weekly Update (not restricted to Tuesday)
- **Branch**: `fix/direct-api-linkedin-agent` (commits 1a9417b, c685e35)

### ✅ Fixed Aivars' Twitter/Airtable integration
- Fixed `platform='email'` bug in twitter_direct_api_agent (was tagging Twitter posts as email)
- Fixed 6 copy-paste errors (instagram/email references)
- Added Airtable + Supabase saves to twitter_haiku_agent (was missing entirely)
- Added 'X' as Twitter platform alias
- Improved single/thread detection keywords
- **Branch**: `fix/direct-api-linkedin-agent` (commits e955989, 1a9417b)

### ✅ Fixed Airtable status mapping
- Adjusted thresholds: >= 24/25 → Ready, >= 18/25 → Draft, < 18/25 → Needs Review
- Applied to all direct API agents (email, twitter, linkedin)
- **Branch**: `fix/direct-api-linkedin-agent` (commits 26673b5, 53e6131, c685e35)

### ✅ Added Perplexity tool
- Integrated Perplexity API for deep research with citations
- Best for: fact-checking, recent stats/data, academic research, complex topics
- Uses sonar-pro model for academic queries, sonar for general queries
- Support for focused searches: internet, news, academic, youtube, reddit
- Added to tools/search_tools.py and registered in claude_agent_handler.py
- **Branch**: `fix/direct-api-linkedin-agent` (commit 9f42b0a)

### ✅ Added file reading capability
- Slack bot can now read uploaded files (images, PDFs, text files)
- Supports Claude's vision API for images (PNG, JPG, etc.)
- Supports Claude's PDF processing for documents
- Text files displayed inline with syntax highlighting
- Files downloaded securely using Slack API with bearer token
- Multimodal messages sent to Claude SDK with file content
- **Implementation:**
  - Modified main_slack.py to extract files from Slack events
  - Added _process_slack_files() method to claude_agent_handler.py
  - Files converted to base64 for images/PDFs
  - Text files decoded and included inline
- **Requirements:**
  - Add `files:read` scope to Slack app (in Slack app settings)
  - File size limit: 32MB (Claude API limit)
- **Branch**: `fix/direct-api-linkedin-agent` (ready to commit)


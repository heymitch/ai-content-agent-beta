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
- Slack bot can now read uploaded text files (JSON, code files, documents)
- Text files displayed inline with syntax highlighting
- Files downloaded securely using Slack API with bearer token
- File content embedded as text in Claude SDK messages
- **Supported formats:** JSON, Python, JavaScript, YAML, XML, HTML, CSS, Markdown, CSV, TXT, and other text files
- **Implementation:**
  - Modified main_slack.py to extract files from Slack events (lines 823-841)
  - Added _process_slack_files() method to claude_agent_handler.py (lines 1666-1786)
  - Smart file type detection (mimetype, Slack filetype, extension)
  - Files embedded as text in message string (SDK query() accepts strings only)
- **Fixes applied:**
  - Fixed JSON file detection (check Slack's filetype field when mimetype missing)
  - Fixed SDK compatibility issue (embed content as text, not multimodal list)
  - Added comprehensive debug logging for troubleshooting
- **Limitations:**
  - Images and PDFs show placeholder notes only (true multimodal requires different SDK approach)
  - File size limit: 32MB (Claude API limit)
- **Requirements:**
  - Add `files:read` scope to Slack app (in Slack app settings)
  - Add `PERPLEXITY_API_KEY` to environment variables (for Perplexity tool)
  - Redeploy application to pick up latest changes
- **Branch**: `fix/direct-api-linkedin-agent` (commits 0f31cbd, c0ceb38, 8cf147f)

### ✅ Fixed Airtable URL + Slack Formatting
- **Fixed Airtable URL bug**: Changed from `table_name` to `table.id` for proper URL construction
- **Fixed Slack markdown**: Added `mrkdwn=True` to all batch orchestrator messages (7 locations)
- **Impact**: Real clickable Airtable URLs, proper bold text rendering (no asterisks)
- **Branch**: `fix/direct-api-linkedin-agent` (commits 4ba7e04, 405880b)

### ✅ Added Calendar Reaction Handler
- React with ✅, 📅, or 🗓️ on Haiku-generated posts to save to Airtable
- **✅ = Draft** (save for review)
- **📅/🗓️ = Scheduled** (ready to publish)
- Returns confirmation with clickable Airtable URL
- Works on Twitter posts generated via Haiku fast path
- **Branch**: `fix/direct-api-linkedin-agent` (commit f79438f)

### ✅ Added Bidirectional Airtable Access
- **search_airtable_posts**: Search content calendar by platform, status, or date
- **get_airtable_post**: Retrieve specific post by record ID for rewriting
- **Workflow enabled**: Client edits in Airtable (via Google Docs) → Agent retrieves → Strategizes → Rewrites → Saves back
- Returns full metadata: content, status, suggested edits, timestamps, clickable URLs
- Added to agent capabilities and system prompt
- **Branch**: `fix/direct-api-linkedin-agent` (commit d013b1b)

### ✅ Fixed Twitter Batch Workflow Issues
- **Fixed Haiku agent Airtable URL**: Added `📊 Airtable: {url}` to Haiku return string so batch orchestrator can extract it
- **Fixed Slack markdown formatting**: Replaced all `**text**` with `*text*` (Slack's mrkdwn format uses single asterisks)
  - Updated 7 locations in batch orchestrator messages
  - Bold text now renders properly in Slack (no more literal asterisks)
- **Improved batch routing logic**: Smarter heuristics for Haiku vs Direct API agent
  - Context >500 chars OR has outline/bullets → use Direct API agent (better validation)
  - Context <100 chars AND topic <100 chars → use Haiku fast path (simpler validation)
  - Default changed: Batch workflows now use Direct API agent for better quality control
  - Haiku reserved for truly simple, short single posts
  - Thread/single post keywords still respected
- **Result**: Single posts get simpler validation (Haiku), threads get full validation (Direct API)
- **Branch**: `fix/direct-api-linkedin-agent`


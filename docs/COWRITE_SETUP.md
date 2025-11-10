# /cowrite Slash Command Setup Guide

## Overview

The `/cowrite` slash command enables interactive content creation sessions where Claude iterates with you using native tool access. Results print to Slack only and are NOT auto-saved to Airtable unless you explicitly approve.

---

## Features

✅ **Interactive Iteration** - Unlimited rounds of feedback
✅ **Native Tool Access** - Generation, quality check, RAG search, AI detection
✅ **Slack-Only Results** - No auto-save until you approve
✅ **Multi-Platform** - LinkedIn, Twitter, Email, YouTube, Instagram
✅ **Agent SDK Powered** - Claude intelligently uses tools available

---

## Slack App Registration

### Step 1: Navigate to Slash Commands

1. Go to https://api.slack.com/apps
2. Select your app
3. Navigate to **Slash Commands** in the left sidebar

### Step 2: Create New Command

Click **"Create New Command"** and fill in:

**Command:** `/cowrite`

**Request URL:** `https://[YOUR_DOMAIN]/slack/commands/cowrite`
- Replace `[YOUR_DOMAIN]` with your FastAPI server URL
- Example: `https://ai-content-agent.herokuapp.com/slack/commands/cowrite`

**Short Description:** `Start interactive content co-writing session`

**Usage Hint:** `[platform] [topic or brief]`

**Escape channels, users, and links sent to your app:** ☑️ Checked

### Step 3: Save Changes

Click **Save** and reinstall the app to your workspace if prompted.

---

## Usage

### Basic Syntax

```
/cowrite [platform] [topic/brief]
```

### Examples

**LinkedIn:**
```
/cowrite linkedin AI agents are changing content workflows for solo operators
```

**Twitter:**
```
/cowrite twitter 5 lessons I learned from building AI content agents
```

**Email:**
```
/cowrite email weekly newsletter about AI automation trends
```

**YouTube:**
```
/cowrite youtube tutorial on getting started with AI agents
```

**Instagram:**
```
/cowrite instagram behind the scenes: building with AI
```

---

## Workflow

### 1. Start Session

User types:
```
/cowrite linkedin thermodynamic chips for garage builders
```

Response:
```
🎨 Co-Write Session Started

Platform: linkedin
Topic: thermodynamic chips for garage builders

⏳ Generating initial draft and quality analysis...
```

### 2. Initial Draft + Analysis

Claude generates draft and runs quality check:
```
📝 Initial Draft:

[Draft content...]

📊 Quality Analysis:
- Hook: 4/5
- Proof: 3/5
- Readability: 4/5
- Total: 18/25

🤖 AI Detection: 15% AI probability (PASS)

Issues found:
- Missing proof points (add case study metrics)
- Hook could be more contrarian

What would you like me to improve?
```

### 3. User Provides Feedback

```
Make it more contrarian and search for proof points about thermodynamic chips
```

Claude:
- Uses `search_company_documents` for proof points
- Uses `apply_fixes_linkedin` with user feedback
- Shows revised draft + new quality score

### 4. Iterate Until Perfect

Repeat step 3 as many times as needed.

### 5. Approve & Save

When happy:
```
Looks great! Send to calendar
```

Claude:
- Uses `send_to_calendar` tool
- Saves to Airtable
- Returns Airtable URL

---

## Tools Available in Co-Write Session

### Generation Tools (5 platforms)
- `generate_post_linkedin`
- `generate_post_twitter`
- `generate_post_email`
- `generate_post_youtube`
- `generate_post_instagram`

### Quality Check Tools (5 platforms)
- `quality_check_linkedin` - 5-axis rubric + AI detection
- `quality_check_twitter`
- `quality_check_email`
- `quality_check_youtube`
- `quality_check_instagram`

### Apply Fixes Tools (5 platforms)
- `apply_fixes_linkedin` - Surgical edits based on feedback
- `apply_fixes_twitter`
- `apply_fixes_email`
- `apply_fixes_youtube`
- `apply_fixes_instagram`

### RAG Search Tools
- `search_company_documents` - Search user-uploaded case studies/testimonials
- `search_content_examples` - Search 700+ high-performing examples

### AI Detection
- `check_ai_detection` - GPTZero validation

### Manual Save
- `send_to_calendar` - Only when user approves

---

## Session Management

### Session Persistence

Sessions are tracked by thread_ts (Slack thread ID). Each `/cowrite` command creates a new thread and session.

### Multiple Sessions

You can have multiple co-write sessions running simultaneously in different threads.

### Session Cleanup

Sessions are kept in memory until:
- User closes thread
- Server restart
- Explicit cleanup (future feature)

---

## Differences: /cowrite vs Batch Mode

| Feature | Batch Mode | /cowrite |
|---------|-----------|----------|
| Entry point | Natural language | `/cowrite [platform] [topic]` |
| Workflow | Auto-generate → Auto-save | Generate → Iterate → Approve |
| Agent type | Direct API | Agent SDK |
| Iteration | No (single pass) | Yes (unlimited) |
| Save behavior | Auto-save to Airtable | Only on explicit approval |
| Tools | Direct API agents | Native tools |
| Use case | "Create 10 posts" | "Let's craft this post together" |

---

## Troubleshooting

### Command Not Found

**Symptom:** `/cowrite` shows "command not recognized"

**Solution:**
1. Verify slash command is registered in Slack App settings
2. Reinstall app to workspace
3. Check request URL matches your FastAPI server

### Session Timeout

**Symptom:** "Session timed out after 3 minutes"

**Solution:**
- First draft generation: 3 minutes timeout
- Iteration rounds: 2 minutes timeout
- If consistently timing out, check:
  - Anthropic API key validity
  - Server logs for errors
  - Network connectivity

### No Tools Available

**Symptom:** Claude says "I don't have access to that tool"

**Solution:**
1. Check `cowrite_tools.py` is importing correctly
2. Verify MCP server is created with tools
3. Check server logs for tool loading errors

### Draft Not Saved

**Symptom:** Draft disappeared, not in Airtable

**Solution:**
- Co-write mode does NOT auto-save
- Only saves when you say "approve", "send to calendar", "looks good"
- If you want to save, explicitly request it

---

## Advanced Usage

### Custom System Prompt

To modify co-write behavior, edit:
```
slack_bot/cowrite_handler.py → _create_system_prompt()
```

### Add Custom Tools

To add more tools to co-write sessions:
```python
# In cowrite_handler.py → _create_cowrite_mcp_server()
custom_tools = [your_custom_tool_here]
all_tools = base_tools + cowrite_tools + custom_tools
```

### Session Persistence Across Restarts

Currently sessions are in-memory only. For persistence:
1. Store session state in Redis/database
2. Serialize SDK session state
3. Restore on reconnection

---

## Testing

### Local Testing

1. Start FastAPI server: `python main_slack.py`
2. Use ngrok to expose: `ngrok http 8000`
3. Update Slack command URL to ngrok URL
4. Test command in Slack

### Production Testing

1. Deploy to production server
2. Update Slack command URL to production domain
3. Test all 5 platforms
4. Verify no auto-save until approval

---

## Support

For issues or questions:
- Check server logs: `/var/log/slack_bot.log`
- Review Slack event logs in App Dashboard
- Test with `/cowrite linkedin test` for simple case

---

## Future Enhancements

🔮 **Planned:**
- Session persistence across restarts
- Multi-user collaboration in same session
- Voice-to-text integration for mobile
- Template library for common patterns
- Analytics on iteration patterns

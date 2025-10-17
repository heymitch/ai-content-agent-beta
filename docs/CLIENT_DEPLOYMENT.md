# Client Deployment Guide

This guide helps you deploy and update the AI Content Agent in your Replit environment without breaking your customizations.

## Table of Contents

- [Initial Setup](#initial-setup)
- [Updating to Latest Version](#updating-to-latest-version)
- [Troubleshooting](#troubleshooting)
- [Understanding the Setup](#understanding-the-setup)

---

## Initial Setup

### Step 1: Clone and Configure (First Time Only)

Run these commands in your Replit shell:

```bash
# Clone the repository
git clone https://github.com/heymitch/ai-content-agent-beta.git
cd ai-content-agent-beta

# Switch to the branch you want (review-fix for testing, main for production)
git checkout review-fix  # or: git checkout main

# Configure git for clean updates (prevents merge conflicts)
git config pull.rebase true
```

### Step 2: Create Your Brand Context File

```bash
# Copy the template
cp .claude/CLAUDE.md.example .claude/CLAUDE.md

# Edit with your brand details (use Replit editor or nano)
nano .claude/CLAUDE.md
```

**What to include in `.claude/CLAUDE.md`:**
- Company name and product description
- Brand voice and tone guidelines
- Target audience details
- Key topics and messaging pillars
- Topics/phrases to avoid
- Preferred CTAs
- Example content in your voice

This file is **gitignored**, so your customizations are safe from updates!

### Step 3: Environment Variables

Create a `.env` file with your API keys:

```bash
# Required
ANTHROPIC_API_KEY=your_key_here
SLACK_BOT_TOKEN=your_token_here
SLACK_APP_TOKEN=your_app_token_here

# Database (Supabase)
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here

# Optional integrations
AIRTABLE_API_KEY=your_key_here
AIRTABLE_BASE_ID=your_base_id_here
AIRTABLE_TABLE_NAME=your_table_name_here
GPTZERO_API_KEY=your_key_here  # Optional: AI detection
```

### Step 4: Database Setup

```bash
# Install dependencies
npm install

# Bootstrap database (creates tables and migrations)
node scripts/bootstrap_database.js
```

### Step 5: Test the Setup

```bash
# Start the Slack bot
npm start
```

Your AI content agent is now running with your custom brand context!

---

## Updating to Latest Version

### Quick Update (Normal Scenario)

```bash
# Pull latest changes
git pull origin review-fix  # or: git pull origin main
```

This works cleanly because you configured `pull.rebase true` during setup.

### Safe Update (If You Get Divergent Branch Error)

If you see this error:

```
Your branch and 'origin/review-fix' have diverged,
and have 2 and 2 different commits each, respectively.
```

Use this **safe command** that preserves your `.claude/CLAUDE.md` file:

```bash
# Reset to match remote exactly (your .claude/CLAUDE.md is safe - it's gitignored!)
git fetch origin && git reset --hard origin/review-fix
```

**Why this is safe:**
- ✅ `.claude/CLAUDE.md` is gitignored, so it's never overwritten
- ✅ `.env` is gitignored, so your API keys are safe
- ✅ Your local commits are discarded, but you get the latest stable code

### Automated Update (Recommended)

Use the included script:

```bash
# Run the automated update script
bash scripts/client_update.sh review-fix  # or: bash scripts/client_update.sh main
```

This script:
1. Stashes any local changes
2. Pulls latest updates
3. Restores your local files
4. Shows a success message

---

## Troubleshooting

### Problem: "Need to specify how to reconcile divergent branches"

**Solution 1 (Safest):**
```bash
git fetch origin && git reset --hard origin/review-fix
```

**Solution 2 (Preserve uncommitted changes):**
```bash
git stash push -m "Local changes"
git pull origin review-fix --rebase
git stash pop
```

### Problem: My `.claude/CLAUDE.md` changes disappeared

**Cause:** You probably didn't create it in the first place, or it was never gitignored.

**Solution:**
```bash
# Check if file exists
ls -la .claude/

# If missing, recreate from template
cp .claude/CLAUDE.md.example .claude/CLAUDE.md

# Edit with your brand context again
nano .claude/CLAUDE.md
```

### Problem: Agent isn't using my brand context

**Diagnosis:**
```bash
# Check if file exists and has content
cat .claude/CLAUDE.md | head -20

# Check if gitignore is working
git status | grep CLAUDE.md  # Should NOT appear in changes
```

**Solution:**
- Make sure `.claude/CLAUDE.md` exists (not `.example`)
- Make sure it has actual content (not empty)
- Restart the agent: `npm start`

### Problem: Database tables are missing

**Solution:**
```bash
# Re-run database bootstrap
node scripts/bootstrap_database.js
```

### Problem: API rate limits or caching not working

**Info:** System prompts are automatically cached by the Claude Agent SDK.

**Benefits:**
- First call: Full cost (~$0.002 per post)
- Subsequent calls (within 5 min): 90% discount (~$0.0002 per post)
- Latency: 85% faster after first call

**No configuration needed** - caching is automatic!

---

## Understanding the Setup

### What Gets Updated (Pulled from Git)

- ✅ Agent code (`agents/`, `integrations/`, `tools/`)
- ✅ Prompt templates (`prompts/`)
- ✅ Database migrations (`sql/`)
- ✅ Scripts (`scripts/`)
- ✅ Documentation (`docs/`, `README.md`)
- ✅ `.claude/CLAUDE.md.example` (template only)

### What Stays Local (Your Customizations)

- ✅ `.claude/CLAUDE.md` (your brand context)
- ✅ `.env` (your API keys)
- ✅ Database content (your generated posts)
- ✅ Any files in gitignore

### File Structure

```
ai-content-agent-template/
├── .claude/
│   ├── CLAUDE.md.example    # Template (updated by dev)
│   └── CLAUDE.md            # Your customizations (gitignored)
├── .env                      # Your API keys (gitignored)
├── agents/                   # Agent code (updated by dev)
├── integrations/             # Integrations (updated by dev)
│   └── prompt_loader.py      # Composes your brand context
├── prompts/                  # Tool prompts (updated by dev)
├── scripts/                  # Utility scripts
│   ├── client_setup.sh       # Automated first-time setup
│   └── client_update.sh      # Automated safe updates
└── docs/
    └── CLIENT_DEPLOYMENT.md  # This guide
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **First-time setup** | `git config pull.rebase true` |
| **Normal update** | `git pull origin review-fix` |
| **Safe update (divergent)** | `git fetch origin && git reset --hard origin/review-fix` |
| **Automated update** | `bash scripts/client_update.sh review-fix` |
| **Create brand context** | `cp .claude/CLAUDE.md.example .claude/CLAUDE.md` |
| **Database setup** | `node scripts/bootstrap_database.js` |
| **Start agent** | `npm start` |

---

## Branch Strategy

- **`review-fix`** - Testing branch with latest features (may be unstable)
- **`main`** - Production-ready stable branch

Switch branches:
```bash
git checkout main          # Switch to stable
git checkout review-fix    # Switch to testing
git pull origin <branch>   # Pull latest
```

---

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Verify `.claude/CLAUDE.md` exists and has content
3. Check `.env` has all required API keys
4. Check database bootstrap completed: `node scripts/bootstrap_database.js`
5. Contact your developer with error logs

---

## Updates Log

Track what changed in each update:

```bash
# See recent commits
git log --oneline -10

# See what changed in specific files
git diff HEAD~5..HEAD agents/linkedin_sdk_agent.py
```

This helps you understand what was updated and if you need to adjust your brand context.

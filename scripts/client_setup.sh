#!/bin/bash

# Client Setup Script
# Run this once when deploying to a new client's Replit instance

set -e  # Exit on error

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   AI Content Agent - Client Setup                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Configure git for clean updates
echo "📋 Step 1: Configuring git for clean updates..."
git config pull.rebase true
echo "   ✅ Git configured (pull.rebase = true)"
echo ""

# Step 2: Check if .claude/CLAUDE.md already exists
echo "📋 Step 2: Setting up client brand context..."
if [ -f ".claude/CLAUDE.md" ]; then
    echo "   ⚠️  .claude/CLAUDE.md already exists"
    echo "   Skipping to avoid overwriting your customizations"
else
    if [ -f ".claude/CLAUDE.md.example" ]; then
        cp .claude/CLAUDE.md.example .claude/CLAUDE.md
        echo "   ✅ Created .claude/CLAUDE.md from template"
        echo "   📝 IMPORTANT: Edit this file with your brand context!"
    else
        echo "   ❌ ERROR: .claude/CLAUDE.md.example not found"
        echo "   You may need to pull the latest code first"
        exit 1
    fi
fi
echo ""

# Step 3: Check .env file
echo "📋 Step 3: Checking environment variables..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"

    # Check for required keys
    MISSING_KEYS=()

    if ! grep -q "ANTHROPIC_API_KEY=" .env; then
        MISSING_KEYS+=("ANTHROPIC_API_KEY")
    fi

    if ! grep -q "SLACK_BOT_TOKEN=" .env; then
        MISSING_KEYS+=("SLACK_BOT_TOKEN")
    fi

    if ! grep -q "SLACK_APP_TOKEN=" .env; then
        MISSING_KEYS+=("SLACK_APP_TOKEN")
    fi

    if ! grep -q "SUPABASE_URL=" .env; then
        MISSING_KEYS+=("SUPABASE_URL")
    fi

    if ! grep -q "SUPABASE_KEY=" .env; then
        MISSING_KEYS+=("SUPABASE_KEY")
    fi

    if [ ${#MISSING_KEYS[@]} -gt 0 ]; then
        echo "   ⚠️  WARNING: Missing required keys in .env:"
        for key in "${MISSING_KEYS[@]}"; do
            echo "      - $key"
        done
        echo "   Please add these to your .env file"
    else
        echo "   ✅ All required API keys present"
    fi
else
    echo "   ⚠️  .env file not found"
    echo "   Create .env with your API keys before running the agent"
    echo ""
    echo "   Required variables:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - SLACK_BOT_TOKEN"
    echo "   - SLACK_APP_TOKEN"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    echo "   - AIRTABLE_API_KEY (optional)"
    echo "   - GPTZERO_API_KEY (optional)"
fi
echo ""

# Step 4: Check if node_modules exists
echo "📋 Step 4: Checking dependencies..."
if [ -d "node_modules" ]; then
    echo "   ✅ Node modules installed"
else
    echo "   ⚠️  Node modules not found"
    echo "   Run: npm install"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════╗"
echo "║   Setup Complete!                                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📝 NEXT STEPS:"
echo ""
echo "1. Edit your brand context:"
echo "   nano .claude/CLAUDE.md"
echo ""
echo "2. Add API keys to .env (if not done already)"
echo ""
echo "3. Install dependencies (if needed):"
echo "   npm install"
echo ""
echo "4. Bootstrap database:"
echo "   node scripts/bootstrap_database.js"
echo ""
echo "5. Start the agent:"
echo "   npm start"
echo ""
echo "6. To update to latest code in the future:"
echo "   bash scripts/client_update.sh review-fix"
echo "   (or: bash scripts/client_update.sh main)"
echo ""
echo "📚 Full documentation: docs/CLIENT_DEPLOYMENT.md"
echo ""

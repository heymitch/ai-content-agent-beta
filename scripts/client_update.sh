#!/bin/bash

# Client Update Script
# Safely pulls latest code while preserving client customizations

set -e  # Exit on error

# Default to review-fix branch
BRANCH="${1:-review-fix}"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   AI Content Agent - Safe Update                       ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if in git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ ERROR: Not in a git repository"
    echo "   Run this script from the project root"
    exit 1
fi

# Show current status
echo "📍 Current branch: $(git branch --show-current)"
echo "📍 Target branch: $BRANCH"
echo ""

# Step 1: Backup client customizations (just in case)
echo "📋 Step 1: Checking client customizations..."
BACKED_UP=false

if [ -f ".claude/CLAUDE.md" ]; then
    echo "   ✅ Found .claude/CLAUDE.md (your brand context)"
    # Create backup
    cp .claude/CLAUDE.md .claude/CLAUDE.md.backup
    BACKED_UP=true
    echo "   💾 Created backup: .claude/CLAUDE.md.backup"
else
    echo "   ⚠️  .claude/CLAUDE.md not found"
    echo "   You may need to create it from .claude/CLAUDE.md.example"
fi
echo ""

# Step 2: Stash any uncommitted changes
echo "📋 Step 2: Saving local changes..."
if git diff-index --quiet HEAD --; then
    echo "   ✅ No uncommitted changes"
    STASHED=false
else
    git stash push -m "Auto-stash before update - $(date '+%Y-%m-%d %H:%M:%S')"
    STASHED=true
    echo "   💾 Stashed local changes"
fi
echo ""

# Step 3: Fetch latest from remote
echo "📋 Step 3: Fetching latest code..."
git fetch origin
echo "   ✅ Fetched from origin"
echo ""

# Step 4: Check if branch exists
if ! git rev-parse --verify "origin/$BRANCH" > /dev/null 2>&1; then
    echo "❌ ERROR: Branch 'origin/$BRANCH' does not exist"
    echo "   Available branches:"
    git branch -r
    exit 1
fi

# Step 5: Switch to target branch if needed
echo "📋 Step 4: Switching to $BRANCH..."
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    git checkout "$BRANCH"
    echo "   ✅ Switched from $CURRENT_BRANCH to $BRANCH"
else
    echo "   ✅ Already on $BRANCH"
fi
echo ""

# Step 6: Pull with rebase (handles divergent branches)
echo "📋 Step 5: Pulling latest changes..."
if git pull origin "$BRANCH" --rebase; then
    echo "   ✅ Successfully pulled latest code"
else
    echo "   ⚠️  Pull failed - attempting reset strategy..."

    # Fallback: Reset to remote (safe because .claude/CLAUDE.md is gitignored)
    git reset --hard "origin/$BRANCH"
    echo "   ✅ Reset to match origin/$BRANCH exactly"
fi
echo ""

# Step 7: Restore stashed changes (if any)
if [ "$STASHED" = true ]; then
    echo "📋 Step 6: Restoring local changes..."
    if git stash pop; then
        echo "   ✅ Restored local changes"
    else
        echo "   ⚠️  Could not auto-restore local changes"
        echo "   Your changes are saved in the stash"
        echo "   Run: git stash list"
        echo "   Then: git stash apply stash@{0}"
    fi
    echo ""
fi

# Step 8: Verify .claude/CLAUDE.md is intact
echo "📋 Step 7: Verifying client customizations..."
if [ -f ".claude/CLAUDE.md" ]; then
    echo "   ✅ .claude/CLAUDE.md is intact"

    # Remove backup if identical
    if [ "$BACKED_UP" = true ]; then
        if diff .claude/CLAUDE.md .claude/CLAUDE.md.backup > /dev/null 2>&1; then
            rm .claude/CLAUDE.md.backup
            echo "   🗑️  Removed backup (file unchanged)"
        else
            echo "   ⚠️  File changed! Backup kept: .claude/CLAUDE.md.backup"
        fi
    fi
else
    echo "   ⚠️  .claude/CLAUDE.md not found"
    if [ -f ".claude/CLAUDE.md.backup" ]; then
        mv .claude/CLAUDE.md.backup .claude/CLAUDE.md
        echo "   ✅ Restored from backup"
    else
        echo "   📝 Create it from: .claude/CLAUDE.md.example"
    fi
fi
echo ""

# Step 9: Check for new migrations
echo "📋 Step 8: Checking for database updates..."
if [ -d "sql" ]; then
    MIGRATION_COUNT=$(ls sql/*.sql 2>/dev/null | wc -l)
    echo "   📊 Found $MIGRATION_COUNT migration files"
    echo "   Run: node scripts/bootstrap_database.js"
    echo "   (This will apply any new migrations)"
else
    echo "   ✅ No database migrations folder"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════╗"
echo "║   Update Complete!                                     ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Updated to: $BRANCH ($(git rev-parse --short HEAD))"
echo ""
echo "📝 NEXT STEPS:"
echo ""

# Check if migrations need to run
if [ -d "sql" ] && [ "$MIGRATION_COUNT" -gt 0 ]; then
    echo "1. Apply database migrations:"
    echo "   node scripts/bootstrap_database.js"
    echo ""
fi

echo "2. Review what changed:"
echo "   git log --oneline -5"
echo ""
echo "3. Check if .claude/CLAUDE.md needs updates:"
echo "   cat .claude/CLAUDE.md.example"
echo ""
echo "4. Restart the agent:"
echo "   npm start"
echo ""

# Show recent commits
echo "📚 Recent updates:"
git log --oneline --decorate -5
echo ""
echo "Full deployment guide: docs/CLIENT_DEPLOYMENT.md"
echo ""

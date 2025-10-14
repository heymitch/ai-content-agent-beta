#!/usr/bin/env python3
"""
Deployment Verification Script
Run this on Replit to verify the deployment matches GitHub
"""
import subprocess
import sys
import os
from pathlib import Path

def run_cmd(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def verify_deployment():
    """Verify Replit deployment matches GitHub"""
    print("🔍 DEPLOYMENT VERIFICATION")
    print("=" * 60)

    # 1. Check git status
    print("\n1️⃣ Git Status:")
    status = run_cmd("git status --short")
    if status:
        print(f"   ⚠️  Uncommitted changes detected:\n{status}")
    else:
        print("   ✅ Working tree clean")

    # 2. Check current commit
    print("\n2️⃣ Current Commit:")
    current = run_cmd("git log -1 --oneline")
    print(f"   {current}")

    # 3. Check if ahead/behind origin
    print("\n3️⃣ Sync Status:")
    behind = run_cmd("git rev-list HEAD..origin/main --count")
    ahead = run_cmd("git rev-list origin/main..HEAD --count")

    if behind and int(behind) > 0:
        print(f"   ⚠️  {behind} commits BEHIND origin/main (need to pull)")
    if ahead and int(ahead) > 0:
        print(f"   ⚠️  {ahead} commits AHEAD of origin/main (unpushed changes)")
    if (not behind or int(behind) == 0) and (not ahead or int(ahead) == 0):
        print("   ✅ In sync with origin/main")

    # 4. Check for emoji reaction fix
    print("\n4️⃣ Critical Bug Fixes:")
    main_slack = Path("main_slack.py")
    if main_slack.exists():
        content = main_slack.read_text()
        if "timestamp=event_ts" in content:
            print("   ✅ Emoji reaction fix present (event_ts)")
        elif "timestamp=event_data" in content:
            print("   ❌ OLD CODE DETECTED (event_data) - NEED TO RESET!")
        else:
            print("   ⚠️  Could not verify emoji reaction code")

    # 5. Check for conversation_history integration
    if "from integrations.supabase_client import is_bot_participating_in_thread" in content:
        print("   ✅ Thread persistence enabled (conversation_history)")
    else:
        print("   ❌ Missing thread persistence import")

    # 6. Check Supabase connection
    print("\n5️⃣ Environment Variables:")
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'ANTHROPIC_API_KEY',
        'SLACK_BOT_TOKEN',
        'SLACK_SIGNING_SECRET'
    ]

    missing = []
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var}")
        else:
            print(f"   ❌ {var} (MISSING)")
            missing.append(var)

    # 7. Check Python cache
    print("\n6️⃣ Python Cache:")
    pycache = run_cmd("find . -type d -name '__pycache__' | wc -l")
    pyc_files = run_cmd("find . -name '*.pyc' | wc -l")
    print(f"   __pycache__ dirs: {pycache}")
    print(f"   .pyc files: {pyc_files}")
    if int(pycache) > 0 or int(pyc_files) > 0:
        print("   💡 TIP: Run cleanup command to remove cached files")

    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")

    issues = []
    if status:
        issues.append("Uncommitted changes")
    if behind and int(behind) > 0:
        issues.append("Behind origin/main")
    if ahead and int(ahead) > 0:
        issues.append("Ahead of origin/main")
    if "timestamp=event_data" in content:
        issues.append("OLD CODE RUNNING")
    if missing:
        issues.append(f"Missing env vars: {', '.join(missing)}")

    if not issues:
        print("✅ Deployment looks good!")
    else:
        print("⚠️  Issues detected:")
        for issue in issues:
            print(f"   • {issue}")

        print("\n🔧 RECOMMENDED FIXES:")
        if "OLD CODE RUNNING" in str(issues) or (ahead and int(ahead) > 0):
            print("   Run: git reset --hard origin/main")
        if int(pycache) > 0 or int(pyc_files) > 0:
            print("   Run: find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null")
            print("   Run: find . -name '*.pyc' -delete")
        if missing:
            print(f"   Set environment variables: {', '.join(missing)}")

    print("=" * 60)

if __name__ == "__main__":
    verify_deployment()

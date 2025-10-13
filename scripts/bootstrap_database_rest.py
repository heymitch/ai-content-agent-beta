#!/usr/bin/env python3
"""
Bootstrap Database Setup (REST API Version)

Automatically sets up the user's Supabase database on first run.
Uses Supabase REST API instead of direct PostgreSQL connection.

This is more reliable for Replit environments where direct PostgreSQL
connections often fail due to network restrictions.

Requirements:
- SUPABASE_URL in environment
- SUPABASE_KEY in environment

Usage:
- Runs automatically via package.json prestart hook on Replit
- Can also run manually: python3 scripts/bootstrap_database_rest.py
- Safe to run multiple times (checks if tables exist)
"""

import os
import sys
from supabase import create_client, Client

# Color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BRIGHT = '\033[1m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'

def log(emoji: str, message: str, color: str = Colors.RESET):
    """Print colored log message"""
    print(f"{color}{emoji} {message}{Colors.RESET}")

def check_table_exists(supabase: Client, table_name: str) -> bool:
    """Check if a table exists by trying to query it"""
    try:
        result = supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if "does not exist" in error_msg or "relation" in error_msg:
            return False
        # If it's a different error, table might exist
        return True

def bootstrap_database():
    """Bootstrap the Supabase database with required tables"""

    log("🚀", "Starting database bootstrap (REST API mode)...", Colors.CYAN)

    # Check environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        log("❌", "Missing SUPABASE_URL or SUPABASE_KEY in environment", Colors.RED)
        log("ℹ️", "Please add these secrets in Replit or your .env file", Colors.YELLOW)
        sys.exit(1)

    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        log("✅", "Connected to Supabase", Colors.GREEN)

        # Check if key tables exist
        tables_to_check = [
            'content_examples',
            'research',
            'company_documents',
            'generated_posts',
            'conversation_history'
        ]

        log("🔍", "Checking if database is already set up...", Colors.BLUE)

        all_exist = True
        for table in tables_to_check:
            exists = check_table_exists(supabase, table)
            if exists:
                log("✅", f"Table '{table}' exists", Colors.GREEN)
            else:
                log("⚠️", f"Table '{table}' missing", Colors.YELLOW)
                all_exist = False

        if all_exist:
            log("🎉", "Database already set up! Skipping bootstrap.", Colors.GREEN)
            log("ℹ️", "If you need to re-import data, please use the Supabase SQL Editor", Colors.CYAN)
            return

        # Tables missing - need to set up
        log("📋", "Database needs setup. Please follow these steps:", Colors.YELLOW)
        log("", "", Colors.RESET)
        log("1️⃣", "Go to your Supabase dashboard: https://supabase.com/dashboard", Colors.BRIGHT)
        log("2️⃣", "Select your project", Colors.BRIGHT)
        log("3️⃣", "Go to the SQL Editor", Colors.BRIGHT)
        log("4️⃣", "Copy the contents of: sql/001_full_database.sql", Colors.BRIGHT)
        log("5️⃣", "Paste into SQL Editor and click 'Run'", Colors.BRIGHT)
        log("", "", Colors.RESET)
        log("💡", "This one-time setup loads your database schema + 741 content examples", Colors.CYAN)
        log("⏱️", "Takes about 30 seconds to run", Colors.CYAN)
        log("", "", Colors.RESET)

        # Check if sql file exists to show file size
        sql_file = os.path.join(os.path.dirname(__file__), '..', 'sql', '001_full_database.sql')
        if os.path.exists(sql_file):
            size_mb = os.path.getsize(sql_file) / (1024 * 1024)
            log("📄", f"File to import: sql/001_full_database.sql ({size_mb:.1f}MB)", Colors.BLUE)

        log("", "", Colors.RESET)
        log("⚠️", "Server will continue starting, but features won't work until database is set up", Colors.YELLOW)

    except Exception as e:
        log("❌", f"Bootstrap error: {e}", Colors.RED)
        log("⚠️", "Server will continue starting, but database may not be set up", Colors.YELLOW)

if __name__ == "__main__":
    try:
        bootstrap_database()
    except KeyboardInterrupt:
        log("⚠️", "Bootstrap interrupted", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        log("❌", f"Unexpected error: {e}", Colors.RED)
        sys.exit(1)

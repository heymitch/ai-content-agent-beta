#!/usr/bin/env python3
"""
Supabase Connection Diagnostic Tool

Helps diagnose Supabase connection issues, especially for EU regions.
Tests both API connection and direct database connection.

Usage:
    python tests/test_supabase_connection.py
"""

import os
import sys

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_supabase_connection():
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}SUPABASE CONNECTION DIAGNOSTIC{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # Step 1: Check environment variables
    print(f"{BLUE}Step 1: Checking Environment Variables{RESET}\n")

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    supabase_db_url = os.getenv('SUPABASE_DB_URL')

    all_set = True

    if supabase_url:
        print(f"  {GREEN}✓{RESET} SUPABASE_URL: {supabase_url}")

        # Check region
        if '.supabase.co' in supabase_url:
            # Extract project reference
            project = supabase_url.split('://')[1].split('.')[0]
            print(f"    Project: {project}")

            # Check if EU region
            if supabase_url.startswith('https://') and 'db.' not in supabase_url:
                print(f"    {YELLOW}ℹ{RESET} Region: Likely EU or non-US (affects DB URL)")
    else:
        print(f"  {RED}✗{RESET} SUPABASE_URL: Missing")
        all_set = False

    if supabase_key:
        masked_key = supabase_key[:20] + '...' if len(supabase_key) > 20 else supabase_key
        print(f"  {GREEN}✓{RESET} SUPABASE_KEY: {masked_key}")
    else:
        print(f"  {RED}✗{RESET} SUPABASE_KEY: Missing")
        all_set = False

    if supabase_db_url:
        # Mask password
        if '@' in supabase_db_url:
            parts = supabase_db_url.split('@')
            user_part = parts[0].split(':')[0]
            masked_db_url = f"{user_part}:***@{parts[1]}"
            print(f"  {GREEN}✓{RESET} SUPABASE_DB_URL: {masked_db_url}")

            # Parse connection details
            print(f"\n  {BLUE}DB Connection Details:{RESET}")

            # Extract port
            if ':6543/' in supabase_db_url:
                print(f"    {GREEN}✓{RESET} Port: 6543 (Transaction pooler - Correct!)")
            elif ':5432/' in supabase_db_url:
                print(f"    {YELLOW}⚠{RESET} Port: 5432 (Session pooler - May cause issues)")
                print(f"      {YELLOW}→{RESET} Try Transaction pooler instead (port 6543)")
            else:
                print(f"    {RED}✗{RESET} Port: Unknown")

            # Extract host
            if '@' in supabase_db_url and '/' in supabase_db_url:
                host_part = supabase_db_url.split('@')[1].split('/')[0]
                host = host_part.split(':')[0]
                print(f"    Host: {host}")

                # Check pooler type
                if 'db.' in host:
                    print(f"    {GREEN}✓{RESET} Pooler: Transaction pooler (db.xxx format)")
                elif 'aws-0' in host or 'pooler' in host:
                    print(f"    {YELLOW}⚠{RESET} Pooler: Session pooler (may not work with Replit)")
                else:
                    print(f"    {YELLOW}ℹ{RESET} Pooler: Check format")

    else:
        print(f"  {RED}✗{RESET} SUPABASE_DB_URL: Missing")
        all_set = False
        print(f"\n  {YELLOW}💡 How to get SUPABASE_DB_URL:{RESET}")
        print(f"     1. Go to https://supabase.com/dashboard")
        print(f"     2. Select your project")
        print(f"     3. Project Settings → Database → Connection String")
        print(f"     4. Select 'Transaction pooler' (NOT 'Session pooler')")
        print(f"     5. Copy the URI and replace [YOUR-PASSWORD]")

    if not all_set:
        print(f"\n{RED}✗ Missing required environment variables{RESET}")
        return False

    # Step 2: Test API connection (SUPABASE_URL + SUPABASE_KEY)
    print(f"\n{BLUE}Step 2: Testing Supabase API Connection{RESET}\n")

    try:
        from integrations.supabase_client import get_supabase_client

        print("  Connecting via Supabase client...")
        supabase = get_supabase_client()
        print(f"  {GREEN}✓{RESET} Client initialized")

        # Try a simple query
        print("  Testing query (generated_posts table)...")
        result = supabase.table('generated_posts').select('id').limit(1).execute()

        print(f"  {GREEN}✓{RESET} API connection works!")
        print(f"  {GREEN}✓{RESET} Can query tables")

    except Exception as e:
        print(f"  {RED}✗{RESET} API connection failed: {str(e)}")

        if "Invalid API key" in str(e):
            print(f"\n  {YELLOW}💡 Fix:{RESET} Check SUPABASE_KEY is correct")
            print(f"     Get it from: Project Settings → API → anon/public key")

        return False

    # Step 3: Test direct database connection (SUPABASE_DB_URL)
    print(f"\n{BLUE}Step 3: Testing Direct Database Connection{RESET}\n")

    try:
        import psycopg2
        from urllib.parse import urlparse

        print("  Parsing connection string...")

        # Parse the URL
        parsed = urlparse(supabase_db_url)

        print(f"  Connecting to {parsed.hostname}:{parsed.port}...")

        # Try to connect
        conn = psycopg2.connect(supabase_db_url)
        print(f"  {GREEN}✓{RESET} Database connection successful!")

        # Try a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  {GREEN}✓{RESET} PostgreSQL version: {version.split(',')[0]}")

        cursor.close()
        conn.close()

        print(f"\n{GREEN}✅ ALL TESTS PASSED!{RESET}")
        print(f"Your Supabase connection is configured correctly.\n")
        return True

    except ImportError:
        print(f"  {YELLOW}⚠{RESET} psycopg2 not installed (can't test direct connection)")
        print(f"  {GREEN}✓{RESET} But API connection works, which is enough for most operations")
        return True

    except Exception as e:
        error_str = str(e)
        print(f"  {RED}✗{RESET} Database connection failed: {error_str}")

        print(f"\n  {YELLOW}💡 Common Issues:{RESET}\n")

        if "password authentication failed" in error_str:
            print(f"  1. {RED}Incorrect password{RESET}")
            print(f"     → Check you replaced [YOUR-PASSWORD] with actual password")
            print(f"     → Get password from: Project Settings → Database → Database Password")
            print(f"     → You may need to reset the password")

        if "could not connect" in error_str or "timeout" in error_str:
            print(f"  2. {RED}Connection blocked{RESET}")
            print(f"     → Check Replit can reach Supabase")
            print(f"     → For EU regions, use Transaction pooler (port 6543)")

        if "5432" in supabase_db_url:
            print(f"  3. {YELLOW}Wrong pooler type{RESET}")
            print(f"     → You're using port 5432 (Session pooler)")
            print(f"     → Switch to port 6543 (Transaction pooler)")
            print(f"     → Get it from: Database → Connection String → Transaction pooler")

        print(f"\n  {YELLOW}📝 Correct format for EU regions:{RESET}")
        print(f"     postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:6543/postgres")
        print(f"     Note: Port is 6543, not 5432!")

        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)

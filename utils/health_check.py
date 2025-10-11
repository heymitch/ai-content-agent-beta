#!/usr/bin/env python3
"""
Simple health check utility for Content Agent
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import openai

def check_environment() -> bool:
    """Check if all required environment variables are set"""
    print("🔧 Checking environment variables...")

    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'OPENAI_API_KEY'
    ]

    optional_vars = [
        'SLACK_WEBHOOK_URL',
        'SLACK_BOT_TOKEN',
        'PLAN_DELIVERY_WEBHOOK_URL'
    ]

    all_good = True

    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Missing")
            all_good = False

    for var in optional_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ⚠️  {var}: Optional, not set")

    return all_good

def check_database_connection() -> bool:
    """Check Supabase connection and basic functionality"""
    print("\n🗄️  Checking database connection...")

    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Test basic query
        result = supabase.table('knowledge_base').select('id').limit(1).execute()
        print("  ✅ Database connection: Working")

        # Check table counts
        tables = {
            'knowledge_base': 'Strategic frameworks',
            'documents': 'General documents',
            'social_content': 'Social media content',
            'high_performing_content': 'Proven content'
        }

        for table, description in tables.items():
            try:
                result = supabase.table(table).select('id', count='exact').execute()
                embedded_result = supabase.table(table).select('id', count='exact').not_.is_('embedding', 'null').execute()

                total_count = result.count
                embedded_count = embedded_result.count

                print(f"  📊 {table}: {total_count} total, {embedded_count} with embeddings")

                if embedded_count == 0 and total_count > 0:
                    print(f"      ⚠️  No embeddings found - RAG search won't work")

            except Exception as e:
                print(f"  ❌ {table}: Error - {str(e)[:50]}...")

        return True

    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

def check_rag_functions() -> bool:
    """Check if RAG search functions are working"""
    print("\n🔍 Checking RAG search functions...")

    try:
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        functions = [
            'match_knowledge',
            'match_documents',
            'match_social_content',
            'match_high_performing_content'
        ]

        working_functions = 0
        dummy_embedding = [0.1] * 1536

        for func_name in functions:
            try:
                result = supabase.rpc(func_name, {
                    'query_embedding': dummy_embedding,
                    'match_threshold': 0.0,
                    'match_count': 1
                }).execute()

                result_count = len(result.data)
                print(f"  ✅ {func_name}: Working ({result_count} test results)")
                working_functions += 1

            except Exception as e:
                print(f"  ❌ {func_name}: Failed - {str(e)[:50]}...")

        if working_functions == len(functions):
            print(f"  🎯 All {len(functions)} RAG functions working!")
            return True
        else:
            print(f"  ⚠️  Only {working_functions}/{len(functions)} RAG functions working")
            return False

    except Exception as e:
        print(f"  ❌ RAG function check failed: {e}")
        return False

def check_openai_connection() -> bool:
    """Check OpenAI API connection"""
    print("\n🧠 Checking OpenAI connection...")

    try:
        openai.api_key = os.getenv('OPENAI_API_KEY')

        # Test simple embedding generation
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input="test"
        )

        if response.data and len(response.data[0].embedding) == 1536:
            print("  ✅ OpenAI API: Working (embedding test passed)")
            return True
        else:
            print("  ❌ OpenAI API: Unexpected response format")
            return False

    except Exception as e:
        print(f"  ❌ OpenAI API failed: {e}")
        return False

def check_agent_files() -> bool:
    """Check if core agent files are present"""
    print("\n📁 Checking agent files...")

    base_dir = Path(__file__).parent.parent
    required_files = [
        'main.py',
        'requirements.txt',
        'supabase_schema.sql'
    ]

    optional_files = [
        'setup/client_onboarding.py',
        'setup/setup_database.py',
        'utils/embedding_utils.py'
    ]

    all_good = True

    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}: Found")
        else:
            print(f"  ❌ {file_path}: Missing")
            all_good = False

    for file_path in optional_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}: Found")
        else:
            print(f"  ⚠️  {file_path}: Optional, not found")

    return all_good

def run_comprehensive_health_check() -> bool:
    """Run all health checks"""
    print("🏥 Content Agent Health Check")
    print("=" * 50)

    checks = [
        ("Environment Variables", check_environment),
        ("Agent Files", check_agent_files),
        ("Database Connection", check_database_connection),
        ("RAG Functions", check_rag_functions),
        ("OpenAI API", check_openai_connection)
    ]

    passed_checks = 0
    total_checks = len(checks)

    for check_name, check_func in checks:
        try:
            if check_func():
                passed_checks += 1
        except Exception as e:
            print(f"\n❌ {check_name} check failed with error: {e}")

    print(f"\n📊 Health Check Summary: {passed_checks}/{total_checks} checks passed")

    if passed_checks == total_checks:
        print("🎉 All systems operational! Your Content Agent is ready to deploy.")
        return True
    elif passed_checks >= total_checks - 1:
        print("⚠️  Minor issues detected. Agent should work but may have limited functionality.")
        return True
    else:
        print("❌ Critical issues detected. Please fix the errors above before deploying.")
        return False

def main():
    """Main health check CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="Health check for Content Agent")
    parser.add_argument("--env-file", help="Path to .env file", default=".env")
    parser.add_argument("--quick", action="store_true", help="Run quick checks only")

    args = parser.parse_args()

    # Load environment variables
    load_dotenv(args.env_file)

    if args.quick:
        print("🚀 Quick Health Check")
        print("=" * 30)
        env_ok = check_environment()
        files_ok = check_agent_files()

        if env_ok and files_ok:
            print("\n✅ Quick check passed!")
            return True
        else:
            print("\n❌ Quick check failed!")
            return False
    else:
        return run_comprehensive_health_check()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
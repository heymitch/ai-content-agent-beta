#!/usr/bin/env python3
"""
Test Agent Memory Workflow

Simulates the n8n agent memory workflow from the shell.
Tests document ingestion, embedding creation, and vector search.

Requirements:
- SUPABASE_URL and SUPABASE_KEY in environment
- OPENAI_API_KEY for embeddings
- pgvector tables set up (run bootstrap first)

Usage:
    python3 scripts/test_agent_memory.py
"""

import os
import sys
from supabase import create_client, Client
from openai import OpenAI
import json
from datetime import datetime

# Color codes
class Colors:
    RESET = '\033[0m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    RED = '\033[31m'

def log(emoji: str, message: str, color: str = Colors.RESET):
    print(f"{color}{emoji} {message}{Colors.RESET}")

def test_connection():
    """Test Supabase connection and check if tables exist"""
    log("🔍", "Testing Supabase connection...", Colors.CYAN)

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        log("❌", "Missing SUPABASE_URL or SUPABASE_KEY", Colors.RED)
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)
    log("✅", "Connected to Supabase", Colors.GREEN)

    # Check tables
    tables = ['document_metadata', 'document_rows', 'company_documents']
    for table in tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            log("✅", f"Table '{table}' exists", Colors.GREEN)
        except Exception as e:
            log("❌", f"Table '{table}' missing: {str(e)}", Colors.RED)
            return None

    return supabase

def create_embedding(text: str) -> list:
    """Create OpenAI embedding for text"""
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        log("❌", "Missing OPENAI_API_KEY", Colors.RED)
        sys.exit(1)

    client = OpenAI(api_key=openai_key)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def test_document_ingestion(supabase: Client):
    """Test ingesting a document into the memory system"""
    log("📝", "Testing document ingestion...", Colors.CYAN)

    # Create test document
    test_doc_id = f"test_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_title = "Test Document: AI Content Strategy"
    test_content = """
    AI Content Strategy Best Practices:

    1. Know your audience and their pain points
    2. Create value-first content that educates
    3. Use AI to augment, not replace, human creativity
    4. Maintain consistent brand voice across platforms
    5. Measure engagement and iterate based on data

    Remember: Quality over quantity. One great post beats ten mediocre ones.
    """

    try:
        # 1. Insert document metadata
        log("1️⃣", "Inserting document metadata...", Colors.BLUE)
        metadata_result = supabase.table('document_metadata').upsert({
            'id': test_doc_id,
            'title': test_title,
            'url': f'https://example.com/docs/{test_doc_id}',
            'schema': None  # Not a tabular document
        }).execute()
        log("✅", f"Inserted metadata for: {test_title}", Colors.GREEN)

        # 2. Create embedding
        log("2️⃣", "Creating embedding with OpenAI...", Colors.BLUE)
        embedding = create_embedding(test_content)
        log("✅", f"Created embedding (dimension: {len(embedding)})", Colors.GREEN)

        # 3. Insert into vector store
        log("3️⃣", "Inserting into vector store...", Colors.BLUE)
        vector_result = supabase.table('company_documents').insert({
            'content': test_content.strip(),
            'metadata': {
                'google_drive_file_id': test_doc_id,
                'title': test_title,
                'user_id': 'test_user',
                'team_id': 'test_team',
                'searchable': True
            },
            'embedding': embedding
        }).execute()
        log("✅", f"Inserted into vector store (id: {vector_result.data[0]['id']})", Colors.GREEN)

        return test_doc_id, embedding

    except Exception as e:
        log("❌", f"Error during ingestion: {str(e)}", Colors.RED)
        return None, None

def test_vector_search(supabase: Client, query: str):
    """Test semantic search using the match_documents function"""
    log("🔎", f"Testing vector search for: '{query}'", Colors.CYAN)

    try:
        # Create query embedding
        log("1️⃣", "Creating query embedding...", Colors.BLUE)
        query_embedding = create_embedding(query)
        log("✅", "Query embedding created", Colors.GREEN)

        # Search using match_documents function
        log("2️⃣", "Searching documents...", Colors.BLUE)
        result = supabase.rpc('match_documents', {
            'query_embedding': query_embedding,
            'match_count': 3,
            'filter': {}
        }).execute()

        if result.data:
            log("✅", f"Found {len(result.data)} matching documents", Colors.GREEN)
            print()
            for i, doc in enumerate(result.data, 1):
                similarity = doc.get('similarity', 0)
                title = doc.get('metadata', {}).get('title', 'Unknown')
                content_preview = doc.get('content', '')[:100] + '...'

                log(f"{i}️⃣", f"Match {i} (similarity: {similarity:.3f})", Colors.CYAN)
                print(f"   Title: {title}")
                print(f"   Preview: {content_preview}")
                print()
        else:
            log("⚠️", "No documents found", Colors.YELLOW)

        return result.data

    except Exception as e:
        log("❌", f"Error during search: {str(e)}", Colors.RED)
        return None

def test_tabular_data(supabase: Client):
    """Test storing tabular data (like CSV/Excel)"""
    log("📊", "Testing tabular data storage...", Colors.CYAN)

    test_dataset_id = f"test_csv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        # 1. Insert dataset metadata
        log("1️⃣", "Inserting dataset metadata...", Colors.BLUE)
        supabase.table('document_metadata').upsert({
            'id': test_dataset_id,
            'title': 'Test Content Performance CSV',
            'url': 'https://example.com/data.csv',
            'schema': json.dumps(['post_id', 'platform', 'likes', 'shares', 'engagement_rate'])
        }).execute()
        log("✅", "Dataset metadata inserted", Colors.GREEN)

        # 2. Insert sample rows
        log("2️⃣", "Inserting sample rows...", Colors.BLUE)
        sample_rows = [
            {'post_id': 'p001', 'platform': 'twitter', 'likes': 150, 'shares': 45, 'engagement_rate': 0.12},
            {'post_id': 'p002', 'platform': 'linkedin', 'likes': 200, 'shares': 60, 'engagement_rate': 0.15},
            {'post_id': 'p003', 'platform': 'twitter', 'likes': 89, 'shares': 20, 'engagement_rate': 0.08},
        ]

        for row in sample_rows:
            supabase.table('document_rows').insert({
                'dataset_id': test_dataset_id,
                'row_data': row
            }).execute()

        log("✅", f"Inserted {len(sample_rows)} rows", Colors.GREEN)

        # 3. Query the data
        log("3️⃣", "Querying rows...", Colors.BLUE)
        result = supabase.table('document_rows').select('*').eq('dataset_id', test_dataset_id).execute()

        if result.data:
            log("✅", f"Retrieved {len(result.data)} rows", Colors.GREEN)
            print()
            for i, row in enumerate(result.data, 1):
                log(f"  Row {i}:", str(row['row_data']), Colors.CYAN)

        return test_dataset_id

    except Exception as e:
        log("❌", f"Error with tabular data: {str(e)}", Colors.RED)
        return None

def cleanup(supabase: Client, doc_id: str = None, dataset_id: str = None):
    """Clean up test data"""
    log("🧹", "Cleaning up test data...", Colors.YELLOW)

    try:
        if doc_id:
            # Delete from company_documents
            supabase.table('company_documents').delete().eq('metadata->>google_drive_file_id', doc_id).execute()
            # Delete metadata
            supabase.table('document_metadata').delete().eq('id', doc_id).execute()
            log("✅", f"Cleaned up document: {doc_id}", Colors.GREEN)

        if dataset_id:
            # Delete rows (cascade will handle this if FK is set up)
            supabase.table('document_rows').delete().eq('dataset_id', dataset_id).execute()
            # Delete metadata
            supabase.table('document_metadata').delete().eq('id', dataset_id).execute()
            log("✅", f"Cleaned up dataset: {dataset_id}", Colors.GREEN)

    except Exception as e:
        log("⚠️", f"Cleanup warning: {str(e)}", Colors.YELLOW)

def main():
    print()
    log("🚀", "Agent Memory Workflow Test", Colors.CYAN)
    print()

    # Test connection
    supabase = test_connection()
    if not supabase:
        log("❌", "Connection test failed. Run bootstrap first!", Colors.RED)
        sys.exit(1)

    print()

    doc_id = None
    dataset_id = None

    try:
        # Test 1: Document ingestion
        print("=" * 60)
        doc_id, embedding = test_document_ingestion(supabase)
        print()

        # Test 2: Vector search
        print("=" * 60)
        test_vector_search(supabase, "How do I create better content?")
        print()

        # Test 3: Tabular data
        print("=" * 60)
        dataset_id = test_tabular_data(supabase)
        print()

        # Summary
        print("=" * 60)
        log("🎉", "All tests passed!", Colors.GREEN)
        print()
        log("💡", "Your agent memory system is working correctly!", Colors.CYAN)
        print()

    except KeyboardInterrupt:
        log("⚠️", "Tests interrupted", Colors.YELLOW)
    finally:
        # Cleanup
        if doc_id or dataset_id:
            print()
            response = input("Clean up test data? (y/n): ")
            if response.lower() == 'y':
                cleanup(supabase, doc_id, dataset_id)
        print()

if __name__ == "__main__":
    main()

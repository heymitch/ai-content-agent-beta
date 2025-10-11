#!/usr/bin/env python3
"""
Reusable embedding utilities for multi-client setup
"""
import os
import json
import time
import glob
from typing import List, Dict, Optional
import openai
from supabase import Client

def generate_embeddings_for_content(
    supabase: Client,
    table_name: str,
    content_fields: List[str],
    batch_size: int = 50,
    delay_seconds: float = 1.0
) -> Dict[str, int]:
    """
    Generate embeddings for content in any table

    Args:
        supabase: Supabase client
        table_name: Name of table to process
        content_fields: List of fields to combine for embedding
        batch_size: Number of items to process at once
        delay_seconds: Delay between batches for rate limiting

    Returns:
        Dict with success/failure counts
    """
    results = {"success": 0, "failed": 0, "skipped": 0}

    print(f"🔄 Processing {table_name} table...")

    # Get items without embeddings
    items_without_embeddings = supabase.table(table_name).select(
        f"id, {', '.join(content_fields)}"
    ).is_('embedding', 'null').limit(batch_size * 10).execute()

    print(f"Found {len(items_without_embeddings.data)} items to process")

    for i, item in enumerate(items_without_embeddings.data):
        try:
            # Combine content fields
            text_parts = []
            for field in content_fields:
                if item.get(field):
                    text_parts.append(str(item[field]))

            if not text_parts:
                results["skipped"] += 1
                continue

            full_text = ' '.join(text_parts)

            # Generate embedding
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=full_text[:8000]  # Limit to 8k chars
            )
            embedding = response.data[0].embedding

            # Update database
            supabase.table(table_name).update({
                'embedding': embedding
            }).eq('id', item['id']).execute()

            results["success"] += 1
            print(f"  ✅ {i+1}/{len(items_without_embeddings.data)}: {item.get('title', item.get('id'))}")

            # Rate limiting
            if i % 10 == 9:
                time.sleep(delay_seconds)

        except Exception as e:
            results["failed"] += 1
            print(f"  ❌ Failed to embed item {item['id']}: {e}")

    return results

def load_content_from_files(
    content_dir: str,
    file_patterns: List[str] = ["*.md", "*.txt"]
) -> List[Dict[str, str]]:
    """
    Load content from files in a directory

    Args:
        content_dir: Directory containing content files
        file_patterns: List of file patterns to match

    Returns:
        List of content items with metadata
    """
    content_items = []

    for pattern in file_patterns:
        files = glob.glob(os.path.join(content_dir, "**", pattern), recursive=True)

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract metadata from filename/path
                rel_path = os.path.relpath(file_path, content_dir)
                parts = rel_path.split(os.sep)

                item = {
                    'title': os.path.splitext(os.path.basename(file_path))[0],
                    'content': content,
                    'file_path': rel_path,
                    'category': parts[0] if len(parts) > 1 else 'general',
                    'metadata': {
                        'source': 'file_import',
                        'original_path': file_path,
                        'file_size': len(content)
                    }
                }

                content_items.append(item)

            except Exception as e:
                print(f"❌ Failed to load {file_path}: {e}")

    return content_items

def import_content_to_table(
    supabase: Client,
    table_name: str,
    content_items: List[Dict[str, str]],
    batch_size: int = 10
) -> Dict[str, int]:
    """
    Import content items to a Supabase table

    Args:
        supabase: Supabase client
        table_name: Target table name
        content_items: List of content items to import
        batch_size: Number of items to insert at once

    Returns:
        Dict with success/failure counts
    """
    results = {"success": 0, "failed": 0}

    print(f"📥 Importing {len(content_items)} items to {table_name}...")

    # Process in batches
    for i in range(0, len(content_items), batch_size):
        batch = content_items[i:i + batch_size]

        try:
            supabase.table(table_name).insert(batch).execute()
            results["success"] += len(batch)
            print(f"  ✅ Imported batch {i//batch_size + 1}: {len(batch)} items")

        except Exception as e:
            results["failed"] += len(batch)
            print(f"  ❌ Failed to import batch {i//batch_size + 1}: {e}")

    return results

def test_rag_search(
    supabase: Client,
    function_name: str,
    test_query: str = "content strategy",
    threshold: float = 0.0,
    count: int = 3
) -> bool:
    """
    Test if a RAG search function is working

    Args:
        supabase: Supabase client
        function_name: Name of the search function to test
        test_query: Query to test with
        threshold: Similarity threshold
        count: Number of results to return

    Returns:
        True if function works, False otherwise
    """
    try:
        # Generate test embedding
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=test_query
        )
        query_embedding = response.data[0].embedding

        # Test the function
        result = supabase.rpc(function_name, {
            'query_embedding': query_embedding,
            'match_threshold': threshold,
            'match_count': count
        }).execute()

        success = len(result.data) > 0
        print(f"  🧪 {function_name}: {'✅ Working' if success else '❌ No results'} ({len(result.data)} results)")

        return success

    except Exception as e:
        print(f"  ❌ {function_name}: Error - {e}")
        return False
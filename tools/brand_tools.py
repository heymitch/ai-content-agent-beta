"""
Brand voice and knowledge management tools
"""
import json
import os
from typing import Dict


def get_brand_voice(user_id: str) -> str:
    """
    Fetch user-specific brand voice guidelines

    Args:
        user_id: User identifier

    Returns:
        JSON string with brand voice guidelines
    """
    try:
        from supabase import create_client

        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Query brand voice
        result = supabase.table('brand_voice').select('*').eq('user_id', user_id).execute()

        if result.data:
            brand = result.data[0]
            return json.dumps({
                'success': True,
                'brand_name': brand.get('brand_name', 'Default'),
                'voice_description': brand.get('voice_description', ''),
                'do_list': brand.get('do_list', []),
                'dont_list': brand.get('dont_list', []),
                'tone': brand.get('tone', 'professional'),
                'example_content': brand.get('example_content', '')
            }, indent=2)
        else:
            # Return default brand voice
            return json.dumps({
                'success': True,
                'brand_name': 'Default',
                'voice_description': 'Professional, clear, and actionable. Focus on outcomes.',
                'do_list': [
                    'Use short sentences',
                    'Lead with outcomes',
                    'Be specific and concrete',
                    'Include examples'
                ],
                'dont_list': [
                    'Avoid jargon',
                    'No generic phrases',
                    'Skip buzzwords',
                    'Avoid passive voice'
                ],
                'tone': 'professional',
                'example_content': ''
            }, indent=2)

    except Exception as e:
        return json.dumps({
            'error': str(e)
        })


def save_to_knowledge_base(
    title: str,
    content: str,
    content_type: str = "example",
    metadata: Dict = None,
    user_id: str = "slack_user"
) -> str:
    """
    Save content to knowledge base for RAG

    Args:
        title: Content title
        content: Content text
        content_type: Type (example, strategy, voice, framework)
        metadata: Additional metadata
        user_id: User identifier

    Returns:
        JSON string with saved record ID
    """
    try:
        from openai import OpenAI
        from supabase import create_client

        # Initialize clients
        openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

        # Generate embedding
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        embedding = response.data[0].embedding

        # Save to database
        result = supabase.table('knowledge_base').insert({
            'title': title,
            'content': content,
            'content_type': content_type,
            'embedding': embedding,
            'metadata': metadata or {}
        }).execute()

        return json.dumps({
            'success': True,
            'id': result.data[0]['id'],
            'title': title,
            'content_type': content_type
        })

    except Exception as e:
        return json.dumps({
            'error': str(e)
        })

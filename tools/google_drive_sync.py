#!/usr/bin/env python3
"""
Google Drive Sync Tool
Syncs a Google Drive folder to the company_documents table with embeddings

Usage:
    python tools/google_drive_sync.py --folder-id YOUR_FOLDER_ID
    python tools/google_drive_sync.py --config  # Uses config/integrations.yaml
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

# Google Drive imports
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
except ImportError:
    print("⚠️  Google API libraries not installed. Run:")
    print("    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

# OpenAI for embeddings
from openai import OpenAI

# Supabase
from supabase import create_client, Client
from dotenv import load_dotenv

# Document parsers
import markdown
from pypdf import PdfReader
from docx import Document as DocxDocument

load_dotenv()


class GoogleDriveSync:
    def __init__(self, folder_id: str, user_id: str = None):
        self.folder_id = folder_id
        self.user_id = user_id or os.getenv('DEFAULT_USER_ID', 'default_user')

        # Initialize clients
        self.drive_service = self._init_drive_service()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.supabase: Client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

    def _init_drive_service(self):
        """Initialize Google Drive API service"""
        creds = None

        # Try service account first (recommended for server deployments)
        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        if service_account_file and os.path.exists(service_account_file):
            creds = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            print("✅ Using service account credentials")
        else:
            # Fall back to OAuth credentials
            token_file = 'token.json'
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file)
                print("✅ Using OAuth credentials")
            else:
                print("❌ No Google credentials found!")
                print("   Set GOOGLE_SERVICE_ACCOUNT_FILE in .env")
                print("   OR run: python tools/setup_google_auth.py")
                sys.exit(1)

        return build('drive', 'v3', credentials=creds)

    def list_files_in_folder(self) -> List[Dict]:
        """List all files in the Google Drive folder"""
        print(f"📂 Listing files in folder: {self.folder_id}")

        query = f"'{self.folder_id}' in parents and trashed=false"
        results = self.drive_service.files().list(
            q=query,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)",
            pageSize=100
        ).execute()

        files = results.get('files', [])
        print(f"   Found {len(files)} file(s)")
        return files

    def download_file_content(self, file_id: str, mime_type: str) -> str:
        """Download and extract text content from file"""

        # Handle Google Docs (export as markdown)
        if mime_type == 'application/vnd.google-apps.document':
            request = self.drive_service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            return file.getvalue().decode('utf-8')

        # Handle regular files
        request = self.drive_service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        content_bytes = file.getvalue()

        # Parse based on mime type
        if mime_type == 'text/plain' or mime_type == 'text/markdown':
            return content_bytes.decode('utf-8')

        elif mime_type == 'application/pdf':
            reader = PdfReader(io.BytesIO(content_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text

        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = DocxDocument(io.BytesIO(content_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text

        else:
            raise ValueError(f"Unsupported mime type: {mime_type}")

    def generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]  # Limit to avoid token limits
        )
        return response.data[0].embedding

    def infer_document_type(self, file_name: str, content: str) -> str:
        """Infer document type from filename and content"""
        name_lower = file_name.lower()
        content_lower = content.lower()[:500]

        if 'brand' in name_lower or 'voice' in name_lower:
            return 'brand_guide'
        elif 'case' in name_lower and 'study' in name_lower:
            return 'case_study'
        elif 'product' in name_lower or 'feature' in name_lower:
            return 'product_doc'
        elif 'about' in name_lower or 'company' in name_lower:
            return 'about_us'
        elif 'example' in name_lower or 'voice' in content_lower:
            return 'voice_example'
        else:
            return 'product_doc'  # Default

    async def sync_file(self, file: Dict) -> bool:
        """Sync a single file to company_documents table"""
        file_id = file['id']
        file_name = file['name']
        mime_type = file['mimeType']
        modified_time = file['modifiedTime']
        web_url = file['webViewLink']

        print(f"\n📄 Processing: {file_name}")

        # Check if file already exists in DB
        existing = self.supabase.table('company_documents').select('*').eq(
            'google_drive_file_id', file_id
        ).execute()

        if existing.data:
            existing_doc = existing.data[0]
            # Check if file was modified since last sync
            last_synced = datetime.fromisoformat(existing_doc['last_synced'].replace('Z', '+00:00'))
            file_modified = datetime.fromisoformat(modified_time.replace('Z', '+00:00'))

            if file_modified <= last_synced:
                print(f"   ⏭️  Skipping (not modified since last sync)")
                return True

            print(f"   🔄 File modified, re-syncing...")

        # Download and extract content
        try:
            content = self.download_file_content(file_id, mime_type)
            print(f"   ✓ Downloaded ({len(content)} chars)")
        except Exception as e:
            print(f"   ❌ Failed to download: {e}")
            return False

        # Generate embedding
        try:
            embedding = self.generate_embedding(content)
            print(f"   ✓ Generated embedding")
        except Exception as e:
            print(f"   ❌ Failed to generate embedding: {e}")
            return False

        # Infer document type
        document_type = self.infer_document_type(file_name, content)

        # Prepare document data
        doc_data = {
            'title': file_name,
            'content': content,
            'document_type': document_type,
            'google_drive_file_id': file_id,
            'google_drive_url': web_url,
            'file_name': file_name,
            'mime_type': mime_type,
            'last_synced': datetime.now().isoformat(),
            'user_id': self.user_id,
            'searchable': True,
            'embedding': embedding,
            'status': 'active'
        }

        # Insert or update
        if existing.data:
            # Update existing
            result = self.supabase.table('company_documents').update(doc_data).eq(
                'google_drive_file_id', file_id
            ).execute()
            print(f"   ✅ Updated in database")
        else:
            # Insert new
            result = self.supabase.table('company_documents').insert(doc_data).execute()
            print(f"   ✅ Inserted to database")

        return True

    async def sync_all(self):
        """Sync all files from Google Drive folder"""
        print(f"\n🚀 Starting Google Drive sync...")
        print(f"   Folder ID: {self.folder_id}")
        print(f"   User ID: {self.user_id}")

        # Get list of files
        files = self.list_files_in_folder()

        if not files:
            print("   No files found in folder")
            return

        # Sync each file
        success_count = 0
        fail_count = 0

        for file in files:
            # Skip unsupported file types
            if file['mimeType'] in [
                'text/plain',
                'text/markdown',
                'application/pdf',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.google-apps.document'
            ]:
                success = await self.sync_file(file)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            else:
                print(f"\n⏭️  Skipping unsupported file type: {file['name']} ({file['mimeType']})")

        # Mark deleted files as archived
        self._archive_deleted_files([f['id'] for f in files])

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Sync complete!")
        print(f"   Success: {success_count}")
        print(f"   Failed: {fail_count}")
        print(f"{'='*60}\n")

    def _archive_deleted_files(self, active_file_ids: List[str]):
        """Mark files as archived if they were deleted from Drive"""
        # Get all docs with google_drive_file_id for this user
        all_docs = self.supabase.table('company_documents').select('id, google_drive_file_id').eq(
            'user_id', self.user_id
        ).not_.is_('google_drive_file_id', 'null').execute()

        archived_count = 0
        for doc in all_docs.data:
            if doc['google_drive_file_id'] not in active_file_ids:
                # File was deleted from Drive, archive it
                self.supabase.table('company_documents').update({
                    'status': 'archived'
                }).eq('id', doc['id']).execute()
                archived_count += 1

        if archived_count > 0:
            print(f"   📦 Archived {archived_count} deleted file(s)")


def load_config() -> Dict:
    """Load configuration from config/integrations.yaml"""
    config_path = Path('config/integrations.yaml')
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("   Create it with Google Drive folder ID:")
        print("   google_drive:")
        print("     folder_id: 'YOUR_FOLDER_ID'")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return config


async def main():
    parser = argparse.ArgumentParser(description='Sync Google Drive folder to Supabase')
    parser.add_argument('--folder-id', help='Google Drive folder ID')
    parser.add_argument('--user-id', help='User ID (defaults to env variable)')
    parser.add_argument('--config', action='store_true', help='Use config/integrations.yaml')

    args = parser.parse_args()

    folder_id = None
    user_id = args.user_id

    if args.config:
        config = load_config()
        folder_id = config.get('google_drive', {}).get('folder_id')
        if not folder_id:
            print("❌ No folder_id found in config/integrations.yaml")
            sys.exit(1)
        user_id = user_id or config.get('google_drive', {}).get('user_id')
    elif args.folder_id:
        folder_id = args.folder_id
    else:
        print("❌ Provide --folder-id or use --config")
        print("   Example: python tools/google_drive_sync.py --folder-id 1ABC...")
        sys.exit(1)

    syncer = GoogleDriveSync(folder_id, user_id)
    await syncer.sync_all()


if __name__ == '__main__':
    asyncio.run(main())

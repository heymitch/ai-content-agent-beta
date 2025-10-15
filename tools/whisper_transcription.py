"""
OpenAI Whisper Voice Transcription
Handles audio transcription for Slack voice messages
"""
import os
import tempfile
from typing import Dict, Optional
import requests
from openai import OpenAI
from pathlib import Path


# File size limit for Whisper API (25MB)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB in bytes

# Supported audio formats
SUPPORTED_FORMATS = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']

# Supported mimetypes for audio files
AUDIO_MIMETYPES = [
    'audio/webm',
    'audio/mp4',
    'audio/m4a',
    'audio/mpeg',
    'audio/wav',
    'audio/x-m4a',
    'audio/mp3'
]


def is_audio_file(mimetype: str, filetype: str) -> bool:
    """
    Check if file is an audio file that can be transcribed

    Args:
        mimetype: File MIME type from Slack
        filetype: File type from Slack

    Returns:
        True if file is audio
    """
    return (
        mimetype in AUDIO_MIMETYPES or
        filetype in SUPPORTED_FORMATS or
        mimetype.startswith('audio/')
    )


def download_slack_file(url_private: str, bot_token: str) -> Optional[bytes]:
    """
    Download file from Slack using private URL and bot token

    Args:
        url_private: Private file URL from Slack
        bot_token: Slack bot token (xoxb-...)

    Returns:
        File bytes or None if download fails
    """
    try:
        print(f"📥 Downloading file from Slack...")

        # Use Bearer token authentication
        headers = {
            'Authorization': f'Bearer {bot_token}'
        }

        response = requests.get(url_private, headers=headers, timeout=30)
        response.raise_for_status()

        file_bytes = response.content
        file_size = len(file_bytes)

        print(f"✅ Downloaded {file_size:,} bytes")

        # Check file size
        if file_size > MAX_FILE_SIZE:
            print(f"⚠️ File size ({file_size:,} bytes) exceeds Whisper limit ({MAX_FILE_SIZE:,} bytes)")
            return None

        return file_bytes

    except requests.RequestException as e:
        print(f"❌ Failed to download file: {e}")
        return None


def transcribe_audio_file(
    file_bytes: bytes,
    filename: str,
    language: Optional[str] = None
) -> Dict[str, any]:
    """
    Transcribe audio file using OpenAI Whisper API

    Args:
        file_bytes: Audio file content as bytes
        filename: Original filename (for extension detection)
        language: Optional language code (e.g., 'en', 'es', 'fr')

    Returns:
        Dict with:
        - success: bool
        - text: str (transcript)
        - duration: float (seconds, if available)
        - error: str (if failed)
    """
    try:
        print(f"🎙️ Transcribing audio with Whisper...")

        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {
                'success': False,
                'text': '',
                'error': 'Missing OPENAI_API_KEY environment variable'
            }

        client = OpenAI(api_key=api_key)

        # Whisper API requires a file object, so create a temporary file
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_file_path = temp_file.name

        try:
            # Open the temp file and send to Whisper
            with open(temp_file_path, 'rb') as audio_file:
                # Call Whisper API
                transcript_params = {
                    'model': 'whisper-1',
                    'file': audio_file,
                    'response_format': 'verbose_json'  # Get more metadata
                }

                # Add language if specified
                if language:
                    transcript_params['language'] = language

                transcript = client.audio.transcriptions.create(**transcript_params)

            # Extract text and metadata
            text = transcript.text
            duration = getattr(transcript, 'duration', None)

            print(f"✅ Transcription complete: {len(text)} characters")

            result = {
                'success': True,
                'text': text,
                'error': None
            }

            if duration:
                result['duration'] = duration

            return result

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'text': '',
            'error': str(e)
        }


def format_transcript_message(
    transcript_text: str,
    duration: Optional[float] = None,
    filename: Optional[str] = None
) -> str:
    """
    Format transcript into a nice Slack message

    Args:
        transcript_text: The transcribed text
        duration: Audio duration in seconds (optional)
        filename: Original filename (optional)

    Returns:
        Formatted message string
    """
    message_parts = ["🎙️ *Voice Transcript:*\n"]

    # Add transcript text
    message_parts.append(transcript_text)

    # Add metadata
    metadata = []
    if duration:
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        if minutes > 0:
            metadata.append(f"Duration: {minutes}m {seconds}s")
        else:
            metadata.append(f"Duration: {seconds}s")

    if filename:
        metadata.append(f"File: {filename}")

    if metadata:
        message_parts.append(f"\n\n_{' • '.join(metadata)}_")

    return "\n".join(message_parts)


def get_slack_transcript_fallback(file_data: Dict) -> Optional[str]:
    """
    Extract Slack's native transcript as fallback

    Args:
        file_data: File object from Slack event

    Returns:
        Transcript text or None
    """
    # Check for Slack's native transcription
    transcription = file_data.get('transcription')

    if transcription:
        status = transcription.get('status')
        if status == 'complete':
            return transcription.get('text')

    return None

"""Groq Whisper transcription for Echo Mode.

Takes a short browser recording (mic capture of singing, humming, or a song
playing nearby) and returns the heard lyrics using Groq's free-tier
whisper-large-v3-turbo model.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

logger = logging.getLogger(__name__)

GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"
MAX_AUDIO_BYTES = 15 * 1024 * 1024  # ~15 MB; a 30s opus recording is well under 1 MB
REQUEST_TIMEOUT_SECONDS = 60


class TranscriptionError(RuntimeError):
    pass


def transcribe_audio(audio: bytes, filename: str, content_type: str) -> str:
    """Return the transcript text for a short audio clip."""
    if not audio:
        raise TranscriptionError("The recording was empty.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise TranscriptionError("The recording is too large — keep it under 30 seconds.")

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise TranscriptionError("GROQ_API_KEY is not configured on the server.")

    response = httpx.post(
        GROQ_TRANSCRIBE_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": (filename or "recording.webm", audio, content_type or "audio/webm")},
        data={
            "model": WHISPER_MODEL,
            "response_format": "json",
            "temperature": 0,
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if not response.is_success:
        logger.error("Groq transcription failed status=%s body=%r", response.status_code, response.text[:500])
        raise TranscriptionError("Transcription failed — please try recording again.")

    text = str(response.json().get("text") or "").strip()
    if not text:
        raise TranscriptionError("Couldn't hear any words in the recording — try singing a little louder.")
    return text

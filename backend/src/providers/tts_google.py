from __future__ import annotations

import asyncio

from src.config import settings
from src.providers.google_common import build_credentials


async def synthesize(
    *,
    text: str,
    voice_name: str,
    speaking_rate: float,
    pitch: float,
    timeout: float,
) -> bytes:
    credentials = build_credentials(settings.google_tts_credentials_json)
    if credentials is None:
        raise RuntimeError("Google TTS credentials are not configured")

    def _run() -> bytes:
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient(credentials=credentials)
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(language_code="en-US", name=voice_name),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=speaking_rate,
                pitch=pitch,
            ),
            timeout=timeout,
        )
        return bytes(response.audio_content)

    return await asyncio.to_thread(_run)

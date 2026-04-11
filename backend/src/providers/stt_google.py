from __future__ import annotations

import asyncio

from src.config import settings
from src.providers.google_common import build_credentials


async def transcribe(
    *,
    audio_bytes: bytes,
    model: str,
    timeout: float,
) -> str:
    credentials = build_credentials(settings.google_stt_credentials_json)
    if credentials is None or not settings.google_cloud_project:
        raise RuntimeError("Google STT credentials are not configured")

    def _run() -> str:
        from google.cloud.speech_v2 import SpeechClient
        from google.cloud.speech_v2.types import cloud_speech

        client = SpeechClient(credentials=credentials)
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model=model,
        )
        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{settings.google_cloud_project}/locations/global/recognizers/_",
            config=config,
            content=audio_bytes,
        )
        response = client.recognize(request=request, timeout=timeout)
        transcripts = []
        for result in response.results:
            if result.alternatives:
                transcripts.append(result.alternatives[0].transcript)
        return " ".join(item.strip() for item in transcripts if item.strip())

    return await asyncio.to_thread(_run)

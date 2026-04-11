from __future__ import annotations

from io import BytesIO

from src.config import settings


async def transcribe(
    *,
    audio_bytes: bytes,
    filename: str,
    content_type: str,
    model: str,
    timeout: float,
) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=timeout)
    file_obj = BytesIO(audio_bytes)
    file_obj.name = filename
    response = await client.audio.transcriptions.create(
        model=model,
        file=(filename, file_obj.read(), content_type),
    )
    return getattr(response, "text", "").strip()

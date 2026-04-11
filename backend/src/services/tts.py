from __future__ import annotations

from uuid import uuid4

from src.config import settings
from src.models import AudioGenerateResponse, Mood, ProviderHealth, VoiceGender, VoiceSpeed
from src.providers import tts_elevenlabs, tts_google
from src.services import storage
from src.services.errors import ProviderFailure
from src.services.llm_fallback import run_with_fallback
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.provider_config import get_elevenlabs_params, get_google_tts_params


_cb_primary = CircuitBreaker("tts_primary", settings.cb_failure_threshold, settings.cb_recovery_timeout_seconds)
_cb_fallback = CircuitBreaker("tts_fallback", settings.cb_failure_threshold, settings.cb_recovery_timeout_seconds)


async def generate_audio(
    *,
    text: str,
    mood: Mood,
    voice_gender: VoiceGender,
    voice_speed: VoiceSpeed,
    filename_prefix: str = "story",
) -> AudioGenerateResponse:
    async def _primary() -> dict[str, str | bytes]:
        return await _invoke(
            provider=settings.tts_primary_provider,
            model=settings.tts_primary_model,
            text=text,
            mood=mood,
            voice_gender=voice_gender,
            voice_speed=voice_speed,
        )

    async def _fallback() -> dict[str, str | bytes]:
        return await _invoke(
            provider=settings.tts_fallback_provider,
            model=settings.tts_fallback_model,
            text=text,
            mood=mood,
            voice_gender=voice_gender,
            voice_speed=voice_speed,
        )

    payload = await run_with_fallback(
        primary_cb=_cb_primary,
        fallback_cb=_cb_fallback,
        primary_call=_primary,
        fallback_call=_fallback,
    )
    filename = f"{filename_prefix}-{uuid4().hex}.mp3"
    audio_url = await storage.upload_audio(payload["audio_bytes"], filename)
    return AudioGenerateResponse(
        audio_url=audio_url,
        provider_used=str(payload["provider"]),
        model_used=str(payload["model"]),
        filename=filename,
    )


async def _invoke(
    *,
    provider: str,
    model: str,
    text: str,
    mood: Mood,
    voice_gender: VoiceGender,
    voice_speed: VoiceSpeed,
) -> dict[str, str | bytes]:
    if provider == "elevenlabs":
        params = get_elevenlabs_params(mood, voice_gender, voice_speed)
        audio_bytes = await tts_elevenlabs.synthesize(
            text=text,
            model=model,
            voice_id=str(params["voice_id"]),
            speed=float(params["speed"]),
            stability=float(params["stability"]),
            style=float(params["style"]),
            timeout=settings.tts_timeout_seconds,
        )
    elif provider == "google":
        params = get_google_tts_params(mood, voice_gender, voice_speed)
        audio_bytes = await tts_google.synthesize(
            text=text,
            voice_name=str(params["voice_name"]),
            speaking_rate=float(params["speaking_rate"]),
            pitch=float(params["pitch"]),
            timeout=settings.tts_timeout_seconds,
        )
    else:
        raise ProviderFailure(f"Unsupported TTS provider: {provider}")

    if not audio_bytes:
        raise ProviderFailure("Empty audio payload returned from TTS")
    return {"audio_bytes": audio_bytes, "provider": provider, "model": model}


def get_health() -> ProviderHealth:
    return ProviderHealth(
        primary_provider=settings.tts_primary_provider,
        primary_model=settings.tts_primary_model,
        primary_state=_cb_primary.get_state(),
        fallback_provider=settings.tts_fallback_provider,
        fallback_model=settings.tts_fallback_model,
        fallback_state=_cb_fallback.get_state(),
    )

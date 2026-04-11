from __future__ import annotations

from src.config import settings
from src.models import ProviderHealth
from src.providers import stt_google, stt_openai
from src.services.errors import ProviderFailure
from src.services.llm_fallback import run_with_fallback
from src.utils.circuit_breaker import CircuitBreaker


_cb_primary = CircuitBreaker("stt_primary", settings.cb_failure_threshold, settings.cb_recovery_timeout_seconds)
_cb_fallback = CircuitBreaker("stt_fallback", settings.cb_failure_threshold, settings.cb_recovery_timeout_seconds)


async def transcribe(*, audio_bytes: bytes, filename: str, content_type: str) -> dict[str, str]:
    async def _primary() -> dict[str, str]:
        return await _invoke(
            provider=settings.stt_primary_provider,
            model=settings.stt_primary_model,
            audio_bytes=audio_bytes,
            filename=filename,
            content_type=content_type,
        )

    async def _fallback() -> dict[str, str]:
        return await _invoke(
            provider=settings.stt_fallback_provider,
            model=settings.stt_fallback_model,
            audio_bytes=audio_bytes,
            filename=filename,
            content_type=content_type,
        )

    return await run_with_fallback(
        primary_cb=_cb_primary,
        fallback_cb=_cb_fallback,
        primary_call=_primary,
        fallback_call=_fallback,
    )


async def _invoke(
    *,
    provider: str,
    model: str,
    audio_bytes: bytes,
    filename: str,
    content_type: str,
) -> dict[str, str]:
    if provider == "openai":
        transcript = await stt_openai.transcribe(
            audio_bytes=audio_bytes,
            filename=filename,
            content_type=content_type,
            model=model,
            timeout=settings.stt_timeout_seconds,
        )
    elif provider == "google":
        transcript = await stt_google.transcribe(
            audio_bytes=audio_bytes,
            model=model,
            timeout=settings.stt_timeout_seconds,
        )
    else:
        raise ProviderFailure(f"Unsupported STT provider: {provider}")

    transcript = transcript.strip()
    if not transcript:
        raise ProviderFailure("Empty transcript returned from STT")
    return {"transcript": transcript, "provider": provider, "model": model}


def get_health() -> ProviderHealth:
    return ProviderHealth(
        primary_provider=settings.stt_primary_provider,
        primary_model=settings.stt_primary_model,
        primary_state=_cb_primary.get_state(),
        fallback_provider=settings.stt_fallback_provider,
        fallback_model=settings.stt_fallback_model,
        fallback_state=_cb_fallback.get_state(),
    )

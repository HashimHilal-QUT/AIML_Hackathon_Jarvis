from __future__ import annotations

from functools import lru_cache
from uuid import uuid4

from src.config import LLMOPS_DIR, settings
from src.models import Genre, Mood, ProviderHealth, StoryGenerateResponse, StoryLength
from src.providers import llm_google, llm_openai
from src.services.errors import ProviderFailure
from src.services.llm_fallback import run_with_fallback
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.json_payload import extract_json_object


WORD_COUNT_MAP = {
    StoryLength.short: 450,
    StoryLength.medium: 750,
    StoryLength.long: 1_500,
}

_cb_primary = CircuitBreaker("story_primary", settings.cb_failure_threshold, settings.cb_recovery_timeout_seconds)
_cb_fallback = CircuitBreaker("story_fallback", settings.cb_failure_threshold, settings.cb_recovery_timeout_seconds)


@lru_cache(maxsize=1)
def _system_prompt() -> str:
    return (LLMOPS_DIR / "system_prompt.txt").read_text(encoding="utf-8")


async def generate_story(*, genre: Genre, mood: Mood, length: StoryLength) -> StoryGenerateResponse:
    prompt = (
        f"Write a {genre.value} bedtime story with a {mood.value} mood. "
        f"Target around {WORD_COUNT_MAP[length]} words."
    )

    async def _primary() -> dict:
        return await _invoke(
            provider=settings.story_primary_provider,
            model=settings.story_primary_model,
            prompt=prompt,
            timeout=settings.story_timeout_seconds,
        )

    async def _fallback() -> dict:
        return await _invoke(
            provider=settings.story_fallback_provider,
            model=settings.story_fallback_model,
            prompt=prompt,
            timeout=settings.story_timeout_seconds,
        )

    payload = await run_with_fallback(
        primary_cb=_cb_primary,
        fallback_cb=_cb_fallback,
        primary_call=_primary,
        fallback_call=_fallback,
    )
    return StoryGenerateResponse(
        story_id=uuid4().hex,
        title=payload["title"],
        body=payload["body"],
        provider_used=payload["_provider"],
        model_used=payload["_model"],
    )


async def _invoke(*, provider: str, model: str, prompt: str, timeout: float) -> dict:
    if provider == "openai":
        raw = await llm_openai.generate_json(
            system_prompt=_system_prompt(),
            user_prompt=prompt,
            model=model,
            timeout=timeout,
        )
    elif provider == "google":
        raw = await llm_google.generate_json(
            system_prompt=_system_prompt(),
            user_prompt=prompt,
            model=model,
            timeout=timeout,
        )
    else:
        raise ProviderFailure(f"Unsupported story provider: {provider}")

    payload = extract_json_object(raw)
    title = str(payload.get("title", "")).strip()
    body = str(payload.get("body", "")).strip()
    if not title or not body:
        raise ProviderFailure("Story model returned incomplete JSON")
    payload["_provider"] = provider
    payload["_model"] = model
    return payload


def get_health() -> ProviderHealth:
    return ProviderHealth(
        primary_provider=settings.story_primary_provider,
        primary_model=settings.story_primary_model,
        primary_state=_cb_primary.get_state(),
        fallback_provider=settings.story_fallback_provider,
        fallback_model=settings.story_fallback_model,
        fallback_state=_cb_fallback.get_state(),
    )

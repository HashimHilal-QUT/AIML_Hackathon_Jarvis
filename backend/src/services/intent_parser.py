from __future__ import annotations

from functools import lru_cache

from src.config import LLMOPS_DIR, settings
from src.models import ActionType, IntentResult, PhaseResult, ProviderHealth, VoiceMode, VoiceUIContext
from src.providers import llm_google, llm_openai
from src.services.errors import ProviderFailure
from src.services.llm_fallback import run_with_fallback
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.json_payload import extract_json_object


_cb_primary = CircuitBreaker("reasoning_primary", settings.cb_failure_threshold, settings.cb_recovery_timeout_seconds)
_cb_fallback = CircuitBreaker("reasoning_fallback", settings.cb_failure_threshold, settings.cb_recovery_timeout_seconds)


@lru_cache(maxsize=1)
def _wake_prompt() -> str:
    return (LLMOPS_DIR / "wake_prompt.txt").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _intent_prompt() -> str:
    return (LLMOPS_DIR / "intent_prompt.txt").read_text(encoding="utf-8")


async def detect_wake(transcript: str) -> dict:
    async def _primary() -> dict:
        return await _invoke(
            provider=settings.reasoning_primary_provider,
            model=settings.reasoning_primary_model,
            system_prompt=_wake_prompt(),
            user_prompt=f"Transcript: {transcript}",
        )

    async def _fallback() -> dict:
        return await _invoke(
            provider=settings.reasoning_fallback_provider,
            model=settings.reasoning_fallback_model,
            system_prompt=_wake_prompt(),
            user_prompt=f"Transcript: {transcript}",
        )

    payload = await run_with_fallback(
        primary_cb=_cb_primary,
        fallback_cb=_cb_fallback,
        primary_call=_primary,
        fallback_call=_fallback,
    )
    return {
        "wake_detected": bool(payload.get("wake_detected")),
        "confidence": float(payload.get("confidence", 0.0)),
        "spoken_response": payload.get("spoken_response") or "Jarvis is awake.",
        "provider": payload["_provider"],
        "model": payload["_model"],
    }


async def parse_intent(*, transcript: str, mode: VoiceMode, ui_context: VoiceUIContext) -> IntentResult:
    user_prompt = (
        f"Mode: {mode.value}\n"
        f"Transcript: {transcript}\n"
        f"UI context JSON: {ui_context.model_dump_json()}\n"
        "Return one valid action."
    )

    async def _primary() -> dict:
        return await _invoke(
            provider=settings.reasoning_primary_provider,
            model=settings.reasoning_primary_model,
            system_prompt=_intent_prompt(),
            user_prompt=user_prompt,
        )

    async def _fallback() -> dict:
        return await _invoke(
            provider=settings.reasoning_fallback_provider,
            model=settings.reasoning_fallback_model,
            system_prompt=_intent_prompt(),
            user_prompt=user_prompt,
        )

    payload = await run_with_fallback(
        primary_cb=_cb_primary,
        fallback_cb=_cb_fallback,
        primary_call=_primary,
        fallback_call=_fallback,
    )
    action_value = payload.get("action", ActionType.none.value)
    try:
        action = ActionType(action_value)
    except ValueError as exc:
        raise ProviderFailure(f"Unsupported action returned by reasoning model: {action_value}") from exc

    confidence = float(payload.get("confidence", 0.0))
    return IntentResult(
        action=action,
        arguments=payload.get("arguments") or {},
        confidence=confidence,
        needs_clarification=bool(payload.get("needs_clarification", False)),
        spoken_response=payload.get("spoken_response"),
        phase_result=PhaseResult.command_detected if action != ActionType.none else PhaseResult.rejected,
        provider_used=payload["_provider"],
        model_used=payload["_model"],
    )


async def _invoke(*, provider: str, model: str, system_prompt: str, user_prompt: str) -> dict:
    if provider == "openai":
        raw = await llm_openai.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            timeout=settings.reasoning_timeout_seconds,
        )
    elif provider == "google":
        raw = await llm_google.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            timeout=settings.reasoning_timeout_seconds,
        )
    else:
        raise ProviderFailure(f"Unsupported reasoning provider: {provider}")

    payload = extract_json_object(raw)
    payload["_provider"] = provider
    payload["_model"] = model
    return payload


def get_health() -> ProviderHealth:
    return ProviderHealth(
        primary_provider=settings.reasoning_primary_provider,
        primary_model=settings.reasoning_primary_model,
        primary_state=_cb_primary.get_state(),
        fallback_provider=settings.reasoning_fallback_provider,
        fallback_model=settings.reasoning_fallback_model,
        fallback_state=_cb_fallback.get_state(),
    )

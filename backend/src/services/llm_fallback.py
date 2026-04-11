from __future__ import annotations

from typing import Awaitable, Callable

from src.services.errors import ProviderFailure
from src.utils.circuit_breaker import CircuitBreaker


async def run_with_fallback(
    *,
    primary_cb: CircuitBreaker,
    fallback_cb: CircuitBreaker,
    primary_call: Callable[[], Awaitable[dict]],
    fallback_call: Callable[[], Awaitable[dict]],
) -> dict:
    try:
        return await primary_cb.call(primary_call)
    except Exception as primary_exc:
        try:
            return await fallback_cb.call(fallback_call)
        except Exception as fallback_exc:
            raise ProviderFailure(
                f"Primary provider failed ({primary_exc}); fallback provider failed ({fallback_exc})"
            ) from fallback_exc

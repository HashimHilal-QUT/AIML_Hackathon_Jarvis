import asyncio

import pytest

from src.utils.circuit_breaker import CircuitBreaker, CircuitOpenError


@pytest.mark.asyncio
async def test_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker("test", failure_threshold=2, recovery_timeout=0.01)

    async def fail() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await breaker.call(fail)
    with pytest.raises(RuntimeError):
        await breaker.call(fail)

    assert breaker.get_state() == "OPEN"

    with pytest.raises(CircuitOpenError):
        await breaker.call(fail)


@pytest.mark.asyncio
async def test_half_open_closes_on_success() -> None:
    breaker = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.01)

    async def fail() -> None:
        raise RuntimeError("boom")

    async def succeed() -> str:
        return "ok"

    with pytest.raises(RuntimeError):
        await breaker.call(fail)

    await asyncio.sleep(0.02)

    result = await breaker.call(succeed)

    assert result == "ok"
    assert breaker.get_state() == "CLOSED"


@pytest.mark.asyncio
async def test_half_open_reopens_on_failure() -> None:
    breaker = CircuitBreaker("test", failure_threshold=1, recovery_timeout=0.01)

    async def fail() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await breaker.call(fail)

    await asyncio.sleep(0.02)

    with pytest.raises(RuntimeError):
        await breaker.call(fail)

    assert breaker.get_state() == "OPEN"

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any, Awaitable, Callable, TypeVar


T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    """Raised when a circuit is open and calls are blocked."""


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int, recovery_timeout: float) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._state = "CLOSED"
        self._opened_at: datetime | None = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        async with self._lock:
            self._refresh_state_locked()
            if self._state == "OPEN":
                raise CircuitOpenError(f"Circuit '{self.name}' is open")

        try:
            result = await func(*args, **kwargs)
        except Exception:
            async with self._lock:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold or self._state == "HALF_OPEN":
                    self._state = "OPEN"
                    self._opened_at = datetime.now(UTC)
            raise

        async with self._lock:
            self._failure_count = 0
            self._state = "CLOSED"
            self._opened_at = None
        return result

    def get_state(self) -> str:
        self._refresh_state()
        return self._state

    def _refresh_state(self) -> None:
        if self._state != "OPEN" or self._opened_at is None:
            return
        if datetime.now(UTC) - self._opened_at >= timedelta(seconds=self.recovery_timeout):
            self._state = "HALF_OPEN"

    def _refresh_state_locked(self) -> None:
        self._refresh_state()

"""Supabase client singleton (service-role, backend-only).

The service role key bypasses Row Level Security. NEVER expose it in frontend code
or responses. All row filtering must be done explicitly in our queries.
"""
from __future__ import annotations

import os
from functools import lru_cache

from supabase import Client, create_client


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required env var: {name}. "
            f"Set it in /Users/karolbhandari/jarvis-recovered/.env"
        )
    return value


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a process-wide singleton Supabase client using the service role key."""
    url = os.getenv("SUPABASE_URL") or _require_env("NEXT_PUBLIC_SUPABASE_URL")
    key = _require_env("SUPABASE_SERVICE_ROLE_KEY")

    # Defensive: never accept a publishable/anon key as the service key.
    if key.startswith("sb_publishable_"):
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY looks like a publishable key. "
            "Backend must use the sb_secret_* service role key."
        )
    return create_client(url, key)


def get_supabase_url() -> str:
    """Project URL — used by auth.py for /auth/v1/user calls."""
    return os.getenv("SUPABASE_URL") or _require_env("NEXT_PUBLIC_SUPABASE_URL")


def get_supabase_anon_key() -> str:
    """Anon / publishable key — used as the `apikey` header on /auth/v1/user."""
    return (
        os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
        or _require_env("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    )

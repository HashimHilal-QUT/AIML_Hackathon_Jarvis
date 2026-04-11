"""Supabase user auth dependency.

We validate the bearer token by calling Supabase's /auth/v1/user endpoint.
Simpler than decoding JWTs ourselves (no JWKS / crypto dance) and works with
both legacy HS256 tokens and the new ES256 keys.
"""
from __future__ import annotations

import httpx
from fastapi import Header, HTTPException, status

from src.supabase_client import get_supabase_anon_key, get_supabase_url


async def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    """FastAPI dependency: returns the caller's auth.users.id (== profiles.id).

    Raises 401 on any auth failure. Safe to use on every /admin/* endpoint.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header (expected 'Bearer <token>').",
        )

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty bearer token.",
        )

    url = f"{get_supabase_url()}/auth/v1/user"
    anon_key = get_supabase_anon_key()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": anon_key,
                },
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not reach Supabase auth: {exc}",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    data = response.json()
    user_id = data.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase user response missing id.",
        )
    return user_id

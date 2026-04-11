"""Supabase Storage helper — manages the `course-materials` bucket.

Everything is scoped under `{user_id}/{subject_id}/{material_id}.{ext}` so that
deleting a subject or user can cleanly sweep their files with a prefix delete.
We use the service-role key on the backend so RLS is bypassed; we still
enforce ownership in our own admin/subjects route handlers by filtering every
query with the authenticated `user_id`.
"""
from __future__ import annotations

import mimetypes
from pathlib import PurePosixPath
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from src.supabase_client import get_supabase

BUCKET_NAME = "course-materials"

_bucket_ready = False


def ensure_bucket() -> None:
    """Idempotently create the course-materials bucket.

    Called lazily on first upload (not at import time) so module import
    stays fast and the backend can still boot if Supabase Storage is
    momentarily unavailable.
    """
    global _bucket_ready
    if _bucket_ready:
        return
    sb = get_supabase()
    try:
        # list_buckets returns [{'id': 'name', 'name': 'name', 'public': ...}, ...]
        existing = sb.storage.list_buckets()
        names = {
            (b.get("name") if isinstance(b, dict) else getattr(b, "name", None))
            for b in (existing or [])
        }
        if BUCKET_NAME not in names:
            sb.storage.create_bucket(
                BUCKET_NAME,
                options={
                    "public": False,
                    "file_size_limit": 25 * 1024 * 1024,  # 25 MB per file
                },
            )
    except Exception as exc:  # pragma: no cover — defensive
        # Bucket may already exist, or the SDK may return a non-fatal error
        # if called concurrently. We only raise if a subsequent upload fails.
        msg = str(exc).lower()
        if "already exists" not in msg and "duplicate" not in msg:
            raise HTTPException(
                500,
                f"Could not ensure Supabase Storage bucket '{BUCKET_NAME}': {exc}",
            )
    _bucket_ready = True


def _guess_extension(filename: str | None, content_type: str | None) -> str:
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if 0 < len(ext) <= 10:
            return ext
    if content_type:
        guess = mimetypes.guess_extension(content_type)
        if guess:
            return guess.lstrip(".")
    return "bin"


def build_object_path(
    user_id: str,
    subject_id: str,
    material_id: str,
    filename: str | None,
    content_type: str | None,
) -> str:
    """Canonical path inside the bucket for a single material file."""
    ext = _guess_extension(filename, content_type)
    return f"{user_id}/{subject_id}/{material_id}.{ext}"


def upload_bytes(
    object_path: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    upsert: bool = True,
) -> str:
    """Upload raw bytes to the bucket. Returns the stored object path."""
    ensure_bucket()
    sb = get_supabase()
    try:
        sb.storage.from_(BUCKET_NAME).upload(
            path=object_path,
            file=data,
            file_options={
                "content-type": content_type,
                "upsert": "true" if upsert else "false",
            },
        )
    except Exception as exc:  # pragma: no cover — defensive
        raise HTTPException(500, f"Storage upload failed: {exc}")
    return object_path


def create_signed_url(object_path: str, expires_in: int = 3600) -> str | None:
    """Return a short-lived signed download URL, or None on failure."""
    ensure_bucket()
    sb = get_supabase()
    try:
        resp = sb.storage.from_(BUCKET_NAME).create_signed_url(
            path=object_path, expires_in=expires_in
        )
        # The SDK returns {'signedURL': '...'} or {'signedUrl': '...'} depending
        # on version. Cover both.
        if isinstance(resp, dict):
            return resp.get("signedURL") or resp.get("signedUrl") or resp.get("signed_url")
        return None
    except Exception:
        return None


def delete_object(object_path: str) -> None:
    """Fire-and-forget delete. Never raises."""
    try:
        ensure_bucket()
        sb = get_supabase()
        sb.storage.from_(BUCKET_NAME).remove([object_path])
    except Exception:
        pass


def generate_material_id() -> str:
    return str(uuid4())


def filename_from_object(path: str) -> str:
    return PurePosixPath(path).name

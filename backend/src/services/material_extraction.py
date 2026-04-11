"""Extract searchable text from uploaded course materials.

When a student uploads a syllabus screenshot, a slide deck PDF, or a
marking rubric image, we want to capture the **text** so Jarvis can quote
it mid-conversation without re-downloading the file. This service handles
that at upload time.

Strategy:
  * PDF           → pypdf.PdfReader, concatenate page text
  * Image         → Claude Vision (claude-sonnet-4-6 multimodal) with a
                    strict "transcribe verbatim" prompt
  * Plain text    → passthrough
  * Other         → skip, store file only

Everything is synchronous and best-effort: if extraction fails, the
material row is still created with whatever text we managed to produce.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
from typing import Any

import httpx
from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 60_000  # guard against pathological PDFs
VISION_MODEL = os.getenv("ANTHROPIC_VISION_MODEL", "claude-sonnet-4-6")

# Reuse the existing ANTHROPIC_API_KEY that chat.py already loads from .env.
# Loaded lazily so import succeeds if the key is missing (extraction just
# returns empty text instead of crashing).


def _get_anthropic_key() -> str | None:
    return os.getenv("ANTHROPIC_API_KEY")


def extract_from_pdf(data: bytes) -> str:
    """Extract text from a PDF byte blob. Returns empty string on failure."""
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        logger.warning("pypdf could not open PDF: %s", exc)
        return ""

    pages_text: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover
            logger.warning("pypdf page %d extraction failed: %s", i, exc)
            txt = ""
        if txt.strip():
            pages_text.append(f"--- Page {i + 1} ---\n{txt.strip()}")
        if sum(len(p) for p in pages_text) > MAX_TEXT_CHARS:
            pages_text.append("\n[… truncated …]")
            break
    return "\n\n".join(pages_text)


def _guess_vision_media_type(content_type: str | None, filename: str | None) -> str:
    """Claude Vision accepts image/jpeg, image/png, image/gif, image/webp."""
    ct = (content_type or "").lower()
    if ct in {"image/jpeg", "image/jpg"}:
        return "image/jpeg"
    if ct in {"image/png", "image/gif", "image/webp"}:
        return ct
    name = (filename or "").lower()
    if name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".gif"):
        return "image/gif"
    if name.endswith(".webp"):
        return "image/webp"
    return "image/png"  # reasonable default for screenshots


def extract_from_image(
    data: bytes,
    content_type: str | None = None,
    filename: str | None = None,
    hint: str | None = None,
) -> str:
    """Transcribe an image via Claude Vision. Returns empty string on failure."""
    api_key = _get_anthropic_key()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY missing; skipping vision OCR")
        return ""

    media_type = _guess_vision_media_type(content_type, filename)
    b64 = base64.standard_b64encode(data).decode("ascii")

    system = (
        "You are a precise OCR transcription assistant for university course "
        "materials (syllabi, lecture slides, marking rubrics, assignment "
        "briefs). Transcribe ALL visible text from the image exactly as it "
        "appears, preserving section headers, bullet points, and tables as "
        "plain text. Do not summarise. Do not add commentary. If the image "
        "is not text-heavy, briefly describe what it shows in one sentence."
    )
    user_text = (
        f"Context hint from the uploader: {hint}\n\n" if hint else ""
    ) + "Transcribe this image."

    body: dict[str, Any] = {
        "model": VISION_MODEL,
        "max_tokens": 4096,
        "system": system,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    }

    try:
        with httpx.Client(timeout=60) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=body,
            )
    except httpx.HTTPError as exc:
        logger.warning("Claude Vision call failed: %s", exc)
        return ""

    if response.status_code != 200:
        logger.warning(
            "Claude Vision returned %s: %s",
            response.status_code,
            response.text[:300],
        )
        return ""

    try:
        result = response.json()
    except json.JSONDecodeError:
        return ""

    blocks = result.get("content") or []
    parts = [
        b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"
    ]
    return "\n".join(p for p in parts if p).strip()[:MAX_TEXT_CHARS]


def extract_text(
    data: bytes,
    content_type: str | None = None,
    filename: str | None = None,
    hint: str | None = None,
) -> str:
    """Dispatch to the right extractor based on content type / filename."""
    ct = (content_type or "").lower()
    name = (filename or "").lower()

    if ct == "application/pdf" or name.endswith(".pdf"):
        return extract_from_pdf(data)

    if ct.startswith("image/") or name.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return extract_from_image(data, content_type=ct, filename=filename, hint=hint)

    if ct.startswith("text/") or name.endswith((".txt", ".md")):
        try:
            return data.decode("utf-8", errors="ignore")[:MAX_TEXT_CHARS]
        except Exception:
            return ""

    # Unknown type — skip extraction, caller will still save the file.
    return ""

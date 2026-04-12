"""Subjects router — CRUD for subjects, their materials, and file uploads.

Router prefix is `/api/subjects` so the Vite dev proxy (no rewrite) forwards
`/api/subjects/...` to the backend verbatim, matching this router.

All endpoints require a signed-in user via `get_current_user_id` — never
trust a client-supplied user_id.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from src.auth import get_current_user_id
from src.services import material_extraction, storage
from src.services.calendar_sync import ensure_profile_row
from src.supabase_client import get_supabase

router = APIRouter(prefix="/api/subjects", tags=["subjects"])

# Full canonical UUID pattern (8-4-4-4-12 hex).
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# Path to the one-time migration SQL — served to the frontend so users can
# copy it into the Supabase dashboard with one click.
SETUP_SQL_PATH = Path(__file__).resolve().parents[2] / "sql" / "001_subjects.sql"


def _is_missing_table_error(exc: Exception) -> bool:
    """Heuristic: did this exception come from Postgres telling us a required
    table doesn't exist yet? Supabase-py raises APIError with a dict body that
    includes `code='PGRST205'` (PostgREST 'relation not found') and/or
    `message` text containing 'schema cache'/'does not exist'."""
    text = f"{type(exc).__name__}: {exc}".lower()
    return (
        "pgrst205" in text
        or "schema cache" in text
        or "does not exist" in text
        or "not find the table" in text
    )


def _schema_not_ready() -> HTTPException:
    return HTTPException(
        status_code=412,
        detail={
            "error": "schema_not_ready",
            "message": (
                "The Subjects feature needs a one-time database migration. "
                "Run backend/sql/001_subjects.sql in the Supabase SQL editor."
            ),
            "sql_path": "backend/sql/001_subjects.sql",
            "setup_endpoint": "/api/subjects/setup-sql",
            "dashboard_url": (
                "https://supabase.com/dashboard/project/"
                "eredinmxmdlgeqfmgtsm/sql/new"
            ),
        },
    )


# -------- Schemas --------


SUBJECT_COLUMNS = "id,user_id,name,code,color,description,term,created_at,updated_at"
MATERIAL_COLUMNS = (
    "id,subject_id,user_id,kind,title,content_text,file_path,file_name,"
    "file_type,file_size,metadata,created_at,updated_at"
)

MATERIAL_KIND = Literal["syllabus", "module", "rubric", "assignment", "file", "note"]


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    code: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=16)
    description: str | None = None
    term: str | None = Field(default=None, max_length=40)


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    code: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=16)
    description: str | None = None
    term: str | None = Field(default=None, max_length=40)


class MaterialTextCreate(BaseModel):
    kind: MATERIAL_KIND
    title: str | None = Field(default=None, max_length=200)
    content_text: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None


# -------- Helpers --------


def _find_subject_by_ref(
    sb, subject_ref: str, user_id: str
) -> dict[str, Any] | None:
    """Resolve a subject reference to the full DB row owned by user_id.

    Accepts any of:
      * Full canonical UUID (36 chars)
      * UUID prefix (Sage/OpenAI Realtime sometimes truncates opaque IDs
        to the first 8 hex chars when echoing them back as tool arguments)
      * Exact / partial case-insensitive match on `code` or `name`

    Returns the full subject row dict, or None if nothing matches. A single
    query fetches all the user's subjects (tiny table per user — typically
    < 20 rows) and the matching happens in-process, avoiding fragile Postgres
    UUID casts and staying robust to any weird input the model produces.
    """
    ref = (subject_ref or "").strip()
    if not ref:
        return None

    try:
        resp = (
            sb.table("subjects")
            .select(SUBJECT_COLUMNS)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise

    subjects: list[dict[str, Any]] = resp.data or []
    if not subjects:
        return None

    ref_lower = ref.lower()

    # 1. Exact UUID match
    if _UUID_RE.match(ref):
        for s in subjects:
            if (s.get("id") or "").lower() == ref_lower:
                return s
        # Full UUID that the user doesn't own → not found
        return None

    # 2. UUID prefix: hex-only (with or without dashes), at least 6 chars.
    #    Sage tends to truncate to the first 8 hex chars of the canonical
    #    UUID — we accept anywhere from 6 up to a full UUID prefix.
    hex_only = ref_lower.replace("-", "")
    if len(hex_only) >= 6 and all(c in "0123456789abcdef" for c in hex_only):
        prefix_matches = [
            s
            for s in subjects
            if (s.get("id") or "").lower().startswith(ref_lower)
        ]
        if len(prefix_matches) == 1:
            return prefix_matches[0]
        # If 2+ match, the prefix is ambiguous — fall through to
        # name/code matching in case the ref happens to be a code like
        # "ABC123" that also looks hex-ish.

    # 3. Exact code match (case-insensitive)
    for s in subjects:
        if (s.get("code") or "").strip().lower() == ref_lower:
            return s

    # 4. Exact name match
    for s in subjects:
        if (s.get("name") or "").strip().lower() == ref_lower:
            return s

    # 5. Substring match on code or name
    for s in subjects:
        code = (s.get("code") or "").lower()
        name = (s.get("name") or "").lower()
        if ref_lower in code or ref_lower in name:
            return s

    return None


def _assert_owns_subject(sb, subject_ref: str, user_id: str) -> dict[str, Any]:
    """Look up a subject owned by user_id. Accepts a full UUID, a UUID prefix,
    or a name/code reference. Raises 404 if no match.

    Callers should use the returned row's `id` for any downstream `eq("id", …)`
    queries — the raw `subject_ref` may be a non-UUID string that Postgres
    will reject with 22P02 if passed verbatim to a uuid column.
    """
    row = _find_subject_by_ref(sb, subject_ref, user_id)
    if not row:
        raise HTTPException(404, "Subject not found")
    return row


def _material_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Post-process a DB row before returning to the frontend: attach a signed
    URL for `file_path` so the UI can download without re-auth."""
    out = dict(row)
    file_path = out.get("file_path")
    if file_path:
        out["signed_url"] = storage.create_signed_url(file_path)
    return out


# -------- Subject CRUD --------


@router.get("")
async def list_subjects(
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    ensure_profile_row(user_id)
    sb = get_supabase()
    try:
        resp = (
            sb.table("subjects")
            .select(SUBJECT_COLUMNS)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    return {"subjects": resp.data or []}


@router.post("")
async def create_subject(
    body: SubjectCreate,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    ensure_profile_row(user_id)
    sb = get_supabase()
    row = body.model_dump(exclude_none=True)
    row["user_id"] = user_id
    try:
        resp = sb.table("subjects").insert(row).execute()
    except Exception as exc:
        if _is_missing_table_error(exc):
            raise _schema_not_ready()
        raise
    created = (resp.data or [None])[0]
    if not created:
        raise HTTPException(500, "Failed to create subject")
    return created


@router.get("/setup-sql", response_class=PlainTextResponse)
async def get_setup_sql() -> str:
    """Return the one-time migration SQL as plain text so the frontend can
    show a copy button. Intentionally NOT auth-gated — the SQL is the same
    for every instance and isn't sensitive."""
    try:
        return SETUP_SQL_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(500, "setup SQL file missing on server")


@router.get("/{subject_id}")
async def get_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    subject = _assert_owns_subject(sb, subject_id, user_id)
    canonical_id = subject["id"]
    # Attach materials as a convenience for the detail page
    mat_resp = (
        sb.table("subject_materials")
        .select(MATERIAL_COLUMNS)
        .eq("subject_id", canonical_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    materials = [_material_to_dict(r) for r in (mat_resp.data or [])]
    return {"subject": subject, "materials": materials}


@router.put("/{subject_id}")
async def update_subject(
    subject_id: str,
    body: SubjectUpdate,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    subject = _assert_owns_subject(sb, subject_id, user_id)
    canonical_id = subject["id"]
    update = body.model_dump(exclude_unset=True)
    if not update:
        return subject
    sb.table("subjects").update(update).eq("id", canonical_id).eq("user_id", user_id).execute()
    return _assert_owns_subject(sb, canonical_id, user_id)


@router.delete("/{subject_id}")
async def delete_subject(
    subject_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, str]:
    sb = get_supabase()
    subject = _assert_owns_subject(sb, subject_id, user_id)
    canonical_id = subject["id"]

    # Delete storage objects first — if this fails, DB rows remain and can be
    # retried. Foreign-key cascade handles the subject_materials rows.
    mat_resp = (
        sb.table("subject_materials")
        .select("file_path")
        .eq("subject_id", canonical_id)
        .eq("user_id", user_id)
        .execute()
    )
    for row in mat_resp.data or []:
        if row.get("file_path"):
            storage.delete_object(row["file_path"])

    sb.table("subjects").delete().eq("id", canonical_id).eq("user_id", user_id).execute()
    return {"deleted": canonical_id}


# -------- Material CRUD --------


@router.post("/{subject_id}/materials/text")
async def create_material_text(
    subject_id: str,
    body: MaterialTextCreate,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Create a text-only material (no file upload)."""
    sb = get_supabase()
    subject = _assert_owns_subject(sb, subject_id, user_id)
    canonical_id = subject["id"]
    row = {
        "subject_id": canonical_id,
        "user_id": user_id,
        "kind": body.kind,
        "title": body.title or body.kind.capitalize(),
        "content_text": body.content_text,
        "metadata": body.metadata or {},
    }
    resp = sb.table("subject_materials").insert(row).execute()
    created = (resp.data or [None])[0]
    if not created:
        raise HTTPException(500, "Failed to create material")
    return _material_to_dict(created)


@router.post("/{subject_id}/materials/upload")
async def create_material_upload(
    subject_id: str,
    file: UploadFile = File(...),
    kind: MATERIAL_KIND = Form(...),
    title: str | None = Form(default=None),
    hint: str | None = Form(default=None),
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Upload a file (PDF, image, text) and extract its text for chat context."""
    sb = get_supabase()
    subject = _assert_owns_subject(sb, subject_id, user_id)
    canonical_id = subject["id"]

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 25 MB limit")

    material_id = storage.generate_material_id()
    object_path = storage.build_object_path(
        user_id=user_id,
        subject_id=canonical_id,
        material_id=material_id,
        filename=file.filename,
        content_type=file.content_type,
    )
    storage.upload_bytes(
        object_path=object_path,
        data=data,
        content_type=file.content_type or "application/octet-stream",
    )

    extracted = material_extraction.extract_text(
        data=data,
        content_type=file.content_type,
        filename=file.filename,
        hint=hint,
    )

    row = {
        "id": material_id,
        "subject_id": canonical_id,
        "user_id": user_id,
        "kind": kind,
        "title": title or (file.filename or kind.capitalize()),
        "content_text": extracted or None,
        "file_path": object_path,
        "file_name": file.filename,
        "file_type": file.content_type,
        "file_size": len(data),
        "metadata": {"extracted": bool(extracted)},
    }
    try:
        resp = sb.table("subject_materials").insert(row).execute()
    except Exception as exc:
        # If the DB insert fails, clean up the orphan file so we don't waste
        # storage quota.
        storage.delete_object(object_path)
        raise HTTPException(500, f"Failed to persist material: {exc}")
    created = (resp.data or [None])[0]
    if not created:
        storage.delete_object(object_path)
        raise HTTPException(500, "Insert returned no row")
    return _material_to_dict(created)


@router.get("/{subject_id}/materials")
async def list_materials(
    subject_id: str,
    kind: MATERIAL_KIND | None = None,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    sb = get_supabase()
    subject = _assert_owns_subject(sb, subject_id, user_id)
    canonical_id = subject["id"]
    query = (
        sb.table("subject_materials")
        .select(MATERIAL_COLUMNS)
        .eq("subject_id", canonical_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
    )
    if kind:
        query = query.eq("kind", kind)
    resp = query.execute()
    return {"materials": [_material_to_dict(r) for r in (resp.data or [])]}


@router.delete("/{subject_id}/materials/{material_id}")
async def delete_material(
    subject_id: str,
    material_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict[str, str]:
    sb = get_supabase()
    subject = _assert_owns_subject(sb, subject_id, user_id)
    canonical_id = subject["id"]
    resp = (
        sb.table("subject_materials")
        .select("file_path")
        .eq("id", material_id)
        .eq("subject_id", canonical_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    existing = resp.data if resp else None
    if not existing:
        raise HTTPException(404, "Material not found")
    if existing.get("file_path"):
        storage.delete_object(existing["file_path"])
    sb.table("subject_materials").delete().eq("id", material_id).eq(
        "user_id", user_id
    ).execute()
    return {"deleted": material_id}


# -------- Subject context helper (used by chat.py) --------


def build_subjects_summary(user_id: str, max_chars: int = 2_500) -> str:
    """Lightweight subject list for session instructions / chat context.

    This is the short version — just name / code / term / id / material
    count. Call `build_subject_context(subject_id)` to get the full dossier
    with extracted content for a specific subject.
    """
    sb = get_supabase()
    try:
        resp = (
            sb.table("subjects")
            .select("id,name,code,term,description")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception:
        return ""
    subjects = resp.data or []
    if not subjects:
        return ""

    # Per-subject material counts (one query, bucketed in-process)
    try:
        mat_resp = (
            sb.table("subject_materials")
            .select("subject_id,kind")
            .eq("user_id", user_id)
            .execute()
        )
        counts: dict[str, dict[str, int]] = {}
        for m in mat_resp.data or []:
            sid = m["subject_id"]
            counts.setdefault(sid, {})
            counts[sid][m["kind"]] = counts[sid].get(m["kind"], 0) + 1
    except Exception:
        counts = {}

    lines = [
        "# SUBJECTS (short list — call get_subject_context for full dossier)"
    ]
    for s in subjects:
        bits: list[str] = [s["name"]]
        if s.get("code"):
            bits.append(f"[{s['code']}]")
        if s.get("term"):
            bits.append(f"· {s['term']}")
        material_counts = counts.get(s["id"], {})
        if material_counts:
            kind_summary = ", ".join(
                f"{kind}×{n}" for kind, n in sorted(material_counts.items())
            )
            bits.append(f"· {kind_summary}")
        bits.append(f"· id={s['id'][:8]}…")
        lines.append(f"- {' '.join(bits)}")
        if s.get("description"):
            desc = s["description"].strip().replace("\n", " ")
            if len(desc) > 120:
                desc = desc[:117] + "…"
            lines.append(f"    {desc}")

    blob = "\n".join(lines)
    if len(blob) > max_chars:
        blob = blob[:max_chars] + "\n[… truncated …]"
    return blob


def resolve_subject_id(user_id: str, subject_ref: str) -> str | None:
    """Resolve a UUID, UUID prefix, exact code, or partial name to a subject id.

    Used by chat/voice tools that take a friendly string like
    `subject="Machine Learning"`, `subject="IFN680"`, or a UUID prefix the
    voice model truncated. Returns None if nothing matches. Delegates to
    `_find_subject_by_ref` so there's one canonical matching algorithm.
    """
    sb = get_supabase()
    try:
        row = _find_subject_by_ref(sb, subject_ref, user_id)
    except HTTPException:
        # _find_subject_by_ref raises 412 if the subjects table is missing —
        # swallow it here and return None so the caller (voice/chat tool)
        # can gracefully report "no subjects found" instead of crashing.
        return None
    return row["id"] if row else None


def search_subject_materials(
    user_id: str, query: str, subject_id: str | None = None, limit: int = 5
) -> list[dict[str, Any]]:
    """Simple substring search across a user's subject materials.

    Returns snippets with ~100 chars of context around the match. Good
    enough for hackathon — production would use a real full-text index.
    """
    query = (query or "").strip()
    if not query:
        return []
    sb = get_supabase()
    try:
        q = (
            sb.table("subject_materials")
            .select(
                "id,subject_id,kind,title,content_text,subjects(name,code)"
            )
            .eq("user_id", user_id)
            .ilike("content_text", f"%{query}%")
            .limit(limit)
        )
        if subject_id:
            q = q.eq("subject_id", subject_id)
        resp = q.execute()
    except Exception:
        return []

    results: list[dict[str, Any]] = []
    lower = query.lower()
    for r in resp.data or []:
        content = r.get("content_text") or ""
        idx = content.lower().find(lower)
        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(content), idx + len(query) + 240)
            snippet = content[start:end].replace("\n", " ").strip()
            if start > 0:
                snippet = "…" + snippet
            if end < len(content):
                snippet = snippet + "…"
        else:
            snippet = content[:300].replace("\n", " ").strip()
        subj = r.get("subjects") or {}
        results.append(
            {
                "material_id": r["id"],
                "subject_id": r["subject_id"],
                "subject_name": subj.get("name"),
                "subject_code": subj.get("code"),
                "kind": r["kind"],
                "title": r.get("title"),
                "snippet": snippet,
            }
        )
    return results


def build_subject_context(subject_ref: str, user_id: str, max_chars: int = 30_000) -> str:
    """Assemble a compact plain-text dossier about a subject for Claude.

    Accepts any of: a full UUID, a truncated UUID prefix (voice models often
    do this), an exact or partial name/code. Returns an empty string if
    nothing matches or the user doesn't own the subject. Silently truncates
    to keep the prompt under `max_chars`.
    """
    sb = get_supabase()
    try:
        subject = _find_subject_by_ref(sb, subject_ref, user_id)
    except HTTPException:
        # Schema-not-ready bubbles up as an HTTPException — callers in
        # chat.py / realtime expect a plain string here, so degrade to empty.
        return ""
    if not subject:
        return ""
    canonical_id = subject["id"]

    mat_resp = (
        sb.table("subject_materials")
        .select("kind,title,content_text,file_name,file_type")
        .eq("subject_id", canonical_id)
        .eq("user_id", user_id)
        .order("kind")
        .execute()
    )
    materials = mat_resp.data or []

    lines: list[str] = []
    lines.append(f"# SUBJECT: {subject['name']}")
    if subject.get("code"):
        lines.append(f"Code: {subject['code']}")
    if subject.get("term"):
        lines.append(f"Term: {subject['term']}")
    if subject.get("description"):
        lines.append(f"Description: {subject['description']}")
    lines.append("")

    # Group by kind for cleanliness
    by_kind: dict[str, list[dict[str, Any]]] = {}
    for m in materials:
        by_kind.setdefault(m["kind"], []).append(m)

    kind_order = ["syllabus", "module", "assignment", "rubric", "note", "file"]
    for kind in kind_order:
        items = by_kind.get(kind, [])
        if not items:
            continue
        lines.append(f"## {kind.upper()}S")
        for m in items:
            title = m.get("title") or m.get("file_name") or "(untitled)"
            lines.append(f"### {title}")
            content = (m.get("content_text") or "").strip()
            if content:
                lines.append(content)
            elif m.get("file_name"):
                lines.append(f"[binary file stored as {m['file_name']}, text not extracted]")
            lines.append("")

    blob = "\n".join(lines).strip()
    if len(blob) > max_chars:
        blob = blob[:max_chars] + "\n\n[… subject context truncated …]"
    return blob

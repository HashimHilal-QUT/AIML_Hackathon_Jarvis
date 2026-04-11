#!/usr/bin/env bash
# ============================================================================
# JARVIS — local dev launcher
# ============================================================================
# Boots the FastAPI backend and the Vite frontend concurrently and streams
# their logs to your terminal. Ctrl-C once and both processes stop cleanly.
#
# Prereqs (run once — see SETUP.md for full instructions):
#   - Python 3.11+ on PATH (python3.11 or python3)
#   - Node 20+ on PATH
#   - backend/.venv set up via  `python3 -m venv backend/.venv`
#   - backend deps installed via  `backend/.venv/bin/pip install -r backend/requirements.txt`
#   - frontend deps installed via `cd frontend && npm install`
#   - .env at repo root (copied from backend/.env.example and filled in)
#   - frontend/.env.local (copied from frontend/.env.example and filled in)
#   - SQL migrations applied in your Supabase project
#
# Usage:
#   ./scripts/start-dev.sh
# ============================================================================

set -euo pipefail

# Resolve the repo root regardless of where you invoke the script from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
VENV_PY="$BACKEND_DIR/.venv/bin/python"

# --- sanity checks --------------------------------------------------------
fail() { echo "[start-dev] ERROR: $*" >&2; exit 1; }

[[ -f "$REPO_ROOT/.env" ]] || fail ".env missing at repo root. Run: cp backend/.env.example .env && edit it"
[[ -f "$FRONTEND_DIR/.env.local" ]] || fail "frontend/.env.local missing. Run: cp frontend/.env.example frontend/.env.local && edit it"
[[ -x "$VENV_PY" ]] || fail "backend/.venv not found. Run: python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt"
[[ -d "$FRONTEND_DIR/node_modules" ]] || fail "frontend/node_modules not found. Run: (cd frontend && npm install)"

# --- signal handling ------------------------------------------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "[start-dev] shutting down..."
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  echo "[start-dev] bye."
}
trap cleanup EXIT INT TERM

# --- boot backend ---------------------------------------------------------
echo "[start-dev] starting backend on http://127.0.0.1:8000"
cd "$BACKEND_DIR"
"$VENV_PY" -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
cd "$REPO_ROOT"

# Give uvicorn a second to bind the port before Vite proxies the first request.
sleep 1

# --- boot frontend --------------------------------------------------------
echo "[start-dev] starting frontend on http://127.0.0.1:5173"
cd "$FRONTEND_DIR"
npm run dev -- --port 5173 --host 127.0.0.1 &
FRONTEND_PID=$!
cd "$REPO_ROOT"

echo ""
echo "============================================================"
echo "  JARVIS is starting up"
echo "  Backend:  http://127.0.0.1:8000/health"
echo "  Frontend: http://127.0.0.1:5173"
echo "  Logs:     streamed below — Ctrl-C to stop both processes"
echo "============================================================"
echo ""

# Wait for either process to exit. If one dies, the trap kills the other.
wait -n "$BACKEND_PID" "$FRONTEND_PID"

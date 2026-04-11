"""JARVIS Backend - Main Application"""
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root BEFORE importing any module that reads env vars at
# import time (supabase_client, auth, etc.). main.py lives at backend/src/main.py,
# so project root is two levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.routes import admin, calendar_parser, chat, meal_buddy, realtime, subjects, voice

# Access log sink — plain text, one line per request. Uvicorn's own logs go
# to the terminal that launched it (not accessible from this process tree),
# so we keep our own tailable file at a well-known path for debugging.
ACCESS_LOG_PATH = Path("/tmp/jarvis_access.log")

app = FastAPI(
    title="JARVIS Backend",
    description="Voice-enabled calendar and AI assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    except Exception as exc:
        status = 500
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        ts = datetime.now(timezone.utc).isoformat()
        ua = request.headers.get("user-agent", "")[:80]
        origin = request.headers.get("origin", "")[:40]
        line = (
            f"{ts} {request.method:<6} {request.url.path:<40} "
            f"status={status} {elapsed_ms:7.1f}ms  "
            f"ua=\"{ua}\" origin=\"{origin}\"\n"
        )
        try:
            with ACCESS_LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass


app.include_router(calendar_parser.router)
app.include_router(voice.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(realtime.router)
app.include_router(subjects.router)
app.include_router(meal_buddy.router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "JARVIS Backend",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

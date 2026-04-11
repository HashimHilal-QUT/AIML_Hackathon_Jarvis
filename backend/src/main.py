from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config import LOCAL_MEDIA_DIR, settings
from src.routes import feedback, health, stories, voice


app = FastAPI(title="One Thousand and One Night Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(stories.router)
app.include_router(voice.router)
app.include_router(feedback.router)

app.mount(settings.local_media_url_base, StaticFiles(directory=LOCAL_MEDIA_DIR), name="media")

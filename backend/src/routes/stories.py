from fastapi import APIRouter

from src.models import (
    AudioGenerateRequest,
    AudioGenerateResponse,
    StoryGenerateRequest,
    StoryGenerateResponse,
)
from src.services import story_generator, tts


router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.post("/generate", response_model=StoryGenerateResponse)
async def generate_story(payload: StoryGenerateRequest) -> StoryGenerateResponse:
    return await story_generator.generate_story(
        genre=payload.genre,
        mood=payload.mood,
        length=payload.length,
    )


@router.post("/audio", response_model=AudioGenerateResponse)
async def generate_audio(payload: AudioGenerateRequest) -> AudioGenerateResponse:
    return await tts.generate_audio(
        text=payload.story_text,
        mood=payload.mood,
        voice_gender=payload.voice_gender,
        voice_speed=payload.voice_speed,
        filename_prefix=payload.filename_prefix,
    )

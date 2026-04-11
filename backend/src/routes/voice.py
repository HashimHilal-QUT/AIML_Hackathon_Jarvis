"""Voice routes for TTS and STT"""
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/voice", tags=["voice"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment")


class TTSRequest(BaseModel):
    text: str
    voice: str = "fable"


@router.post("")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech using OpenAI TTS"""
    if not request.text or len(request.text) > 1500:
        raise HTTPException(status_code=400, detail="Text must be 1-1500 characters")

    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if request.voice not in valid_voices:
        raise HTTPException(status_code=400, detail=f"Invalid voice: {request.voice}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "tts-1",
                    "input": request.text,
                    "voice": request.voice
                },
                timeout=30
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to generate speech"
                )

            return StreamingResponse(
                iter([response.content]),
                media_type="audio/mpeg"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    """Transcribe audio using OpenAI Whisper"""
    try:
        audio_data = await file.read()

        async with httpx.AsyncClient() as client:
            files = {"file": (file.filename, audio_data, "audio/webm")}
            data = {"model": "whisper-1"}

            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to transcribe audio"
                )

            result = response.json()
            return {"text": result.get("text", "")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

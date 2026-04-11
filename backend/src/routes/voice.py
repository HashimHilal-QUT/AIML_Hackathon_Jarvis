from fastapi import APIRouter, File, Form, UploadFile

from src.models import (
    VoiceCommandResponse,
    VoiceMode,
    VoiceSessionStartRequest,
    VoiceSessionStartResponse,
    VoiceUIContext,
)
from src.services import voice_command, voice_session


router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/session/start", response_model=VoiceSessionStartResponse)
async def start_voice_session(payload: VoiceSessionStartRequest) -> VoiceSessionStartResponse:
    return await voice_session.start_session(payload)


@router.post("/command", response_model=VoiceCommandResponse)
async def command(
    audio_file: UploadFile = File(...),
    session_id: str = Form(...),
    mode: VoiceMode = Form(...),
    ui_context: str = Form("{}"),
    want_voice_response: bool = Form(False),
) -> VoiceCommandResponse:
    context = VoiceUIContext.model_validate_json(ui_context)
    return await voice_command.process_voice_command(
        audio_file=audio_file,
        session_id=session_id,
        mode=mode,
        ui_context=context,
        want_voice_response=want_voice_response,
    )

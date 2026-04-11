from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from src.models import (
    RealtimeVoiceSessionRequest,
    RealtimeVoiceSessionResponse,
    VoiceCommandResponse,
    VoiceMode,
    VoiceSessionStartRequest,
    VoiceSessionStartResponse,
    VoiceUIContext,
)
from src.services import realtime_voice, voice_command, voice_session


router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/session/start", response_model=VoiceSessionStartResponse)
async def start_voice_session(payload: VoiceSessionStartRequest) -> VoiceSessionStartResponse:
    return await voice_session.start_session(payload)


@router.post("/realtime/session", response_model=RealtimeVoiceSessionResponse)
async def start_realtime_voice_session(
    payload: RealtimeVoiceSessionRequest,
) -> RealtimeVoiceSessionResponse:
    return await realtime_voice.create_client_secret(payload)


@router.get("/realtime/test-page", response_class=HTMLResponse)
async def realtime_test_page() -> HTMLResponse:
    return HTMLResponse(realtime_voice.load_test_page())


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

from __future__ import annotations

from fastapi import UploadFile

from src.config import settings
from src.models import (
    ActionType,
    IntentResult,
    Mood,
    PhaseResult,
    VoiceCommandResponse,
    VoiceGender,
    VoiceMode,
    VoiceSpeed,
    VoiceUIContext,
)
from src.services import action_executor, intent_parser, stt, tts, voice_session
from src.services.errors import BusinessRuleError


MEANINGFUL_ACTIONS = {
    ActionType.activate_app,
    ActionType.generate_story,
    ActionType.regenerate_story,
    ActionType.generate_audio,
    ActionType.listening_on,
    ActionType.listening_off,
    ActionType.set_genre,
    ActionType.set_mood,
    ActionType.set_length,
    ActionType.set_voice_gender,
    ActionType.set_voice_speed,
}


async def process_voice_command(
    *,
    audio_file: UploadFile,
    session_id: str,
    mode: VoiceMode,
    ui_context: VoiceUIContext,
    want_voice_response: bool,
) -> VoiceCommandResponse:
    session = await voice_session.get_or_create(session_id)
    if not session["listening_enabled"] and mode == VoiceMode.command_mode:
        return VoiceCommandResponse(
            session_id=session_id,
            mode=mode,
            transcript="",
            phase_result=PhaseResult.ignored,
            spoken_response_text="Listening is currently off.",
            session_state_patch=voice_session.make_patch(
                app_activated=session["app_activated"],
                listening_enabled=session["listening_enabled"],
            ),
        )

    audio_bytes = await audio_file.read()
    if not audio_bytes:
        return VoiceCommandResponse(
            session_id=session_id,
            mode=mode,
            transcript="",
            phase_result=PhaseResult.rejected,
            spoken_response_text="No audio was provided.",
        )
    if len(audio_bytes) > settings.voice_max_audio_bytes:
        return VoiceCommandResponse(
            session_id=session_id,
            mode=mode,
            transcript="",
            phase_result=PhaseResult.rejected,
            spoken_response_text="That audio clip is too large for the demo.",
        )

    stt_result = await stt.transcribe(
        audio_bytes=audio_bytes,
        filename=audio_file.filename or "voice-command.webm",
        content_type=audio_file.content_type or "audio/webm",
    )
    transcript = stt_result["transcript"]
    provider_chain = {"stt": f'{stt_result["provider"]}:{stt_result["model"]}'}

    if mode == VoiceMode.command_mode and not session["app_activated"]:
        session = await voice_session.apply_patch(
            session_id,
            voice_session.make_patch(app_activated=True),
        )

    try:
        if mode == VoiceMode.wake_mode and not session["app_activated"]:
            wake_result = await intent_parser.detect_wake(transcript)
            provider_chain["reasoning"] = f'{wake_result["provider"]}:{wake_result["model"]}'
            if not wake_result["wake_detected"]:
                return VoiceCommandResponse(
                    session_id=session_id,
                    mode=mode,
                    transcript=transcript,
                    phase_result=PhaseResult.ignored,
                    confidence=wake_result["confidence"],
                    provider_chain=provider_chain,
                )

            execution = await action_executor.execute(
                session_id=session_id,
                intent=IntentResult(
                    action=ActionType.activate_app,
                    confidence=wake_result["confidence"],
                    spoken_response=wake_result["spoken_response"],
                    phase_result=PhaseResult.wake_detected,
                ),
                ui_context=ui_context,
            )
        else:
            intent = await intent_parser.parse_intent(transcript=transcript, mode=mode, ui_context=ui_context)
            provider_chain["reasoning"] = f"{intent.provider_used}:{intent.model_used}"
            execution = await action_executor.execute(
                session_id=session_id,
                intent=intent,
                ui_context=ui_context,
            )
    except BusinessRuleError as exc:
        execution = await action_executor.execute(
            session_id=session_id,
            intent=IntentResult(
                action=ActionType.none,
                confidence=0.0,
                needs_clarification=True,
                spoken_response=str(exc),
                phase_result=PhaseResult.rejected,
            ),
            ui_context=ui_context,
        )

    spoken_response_audio_url = None
    if execution.spoken_response_text and _should_generate_voice(
        action=execution.action,
        phase_result=execution.phase_result,
        want_voice_response=want_voice_response,
    ):
        voice_response = await tts.generate_audio(
            text=execution.spoken_response_text,
            mood=ui_context.mood or Mood.calm,
            voice_gender=ui_context.voice_gender or VoiceGender.female,
            voice_speed=ui_context.voice_speed or VoiceSpeed.normal,
            filename_prefix="assistant",
        )
        spoken_response_audio_url = voice_response.audio_url
        provider_chain["assistant_tts"] = f"{voice_response.provider_used}:{voice_response.model_used}"

    return VoiceCommandResponse(
        session_id=session_id,
        mode=mode,
        transcript=transcript,
        phase_result=execution.phase_result,
        action=execution.action,
        arguments=execution.arguments,
        confidence=execution.confidence,
        spoken_response_text=execution.spoken_response_text,
        spoken_response_audio_url=spoken_response_audio_url,
        ui_command=execution.ui_command,
        session_state_patch=execution.session_state_patch,
        provider_chain=provider_chain,
        result=execution.result,
    )


def _should_generate_voice(
    *,
    action: ActionType | None,
    phase_result: PhaseResult,
    want_voice_response: bool,
) -> bool:
    if want_voice_response:
        return True
    if phase_result in {PhaseResult.rejected, PhaseResult.wake_detected}:
        return True
    return action in MEANINGFUL_ACTIONS

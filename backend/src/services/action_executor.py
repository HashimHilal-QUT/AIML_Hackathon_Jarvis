from __future__ import annotations

from src.models import (
    ActionExecutionResult,
    ActionType,
    FeedbackRequest,
    FeedbackValue,
    Genre,
    IntentResult,
    Mood,
    PhaseResult,
    StoryLength,
    VoiceGender,
    VoiceSpeed,
    VoiceUIContext,
)
from src.services import feedback, story_generator, tts, voice_session
from src.services.errors import BusinessRuleError


UI_COMMANDS = {
    ActionType.play_audio,
    ActionType.pause_audio,
    ActionType.resume_audio,
    ActionType.stop_audio,
}


async def execute(
    *,
    session_id: str,
    intent: IntentResult,
    ui_context: VoiceUIContext,
) -> ActionExecutionResult:
    action = intent.action
    spoken_response = intent.spoken_response

    if action == ActionType.activate_app:
        patch = voice_session.make_patch(app_activated=True, last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.wake_detected,
            action=action,
            arguments=intent.arguments,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Jarvis is awake.",
            session_state_patch=patch,
        )

    if action == ActionType.listening_on:
        patch = voice_session.make_patch(listening_enabled=True, last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Listening is back on.",
            session_state_patch=patch,
        )

    if action == ActionType.listening_off:
        patch = voice_session.make_patch(listening_enabled=False, last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Listening is off.",
            session_state_patch=patch,
        )

    if action == ActionType.generate_story:
        genre = _maybe_enum(intent.arguments.get("genre") or ui_context.genre, Genre)
        mood = _maybe_enum(intent.arguments.get("mood") or ui_context.mood, Mood)
        length = _maybe_enum(intent.arguments.get("length") or ui_context.length, StoryLength)
        if not genre or not mood or not length:
            raise BusinessRuleError("Story generation requires genre, mood, and length")
        response = await story_generator.generate_story(genre=genre, mood=mood, length=length)
        patch = voice_session.make_patch(last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            arguments={"genre": genre, "mood": mood, "length": length},
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Generating your bedtime story now.",
            session_state_patch=patch,
            result=response.model_dump(),
        )

    if action == ActionType.regenerate_story:
        if not ui_context.genre or not ui_context.mood or not ui_context.length:
            raise BusinessRuleError("Cannot regenerate without the current story settings")
        response = await story_generator.generate_story(
            genre=ui_context.genre,
            mood=ui_context.mood,
            length=ui_context.length,
        )
        patch = voice_session.make_patch(last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Making another version of the story.",
            session_state_patch=patch,
            result=response.model_dump(),
        )

    if action == ActionType.generate_audio:
        if not ui_context.story_text:
            raise BusinessRuleError("There is no story available to narrate yet")
        mood = _maybe_enum(intent.arguments.get("mood") or ui_context.mood, Mood)
        voice_gender = _maybe_enum(intent.arguments.get("voice_gender") or ui_context.voice_gender, VoiceGender)
        voice_speed = _maybe_enum(intent.arguments.get("voice_speed") or ui_context.voice_speed, VoiceSpeed)
        if not mood or not voice_gender or not voice_speed:
            raise BusinessRuleError("Narration requires mood, voice gender, and voice speed")
        response = await tts.generate_audio(
            text=ui_context.story_text,
            mood=mood,
            voice_gender=voice_gender,
            voice_speed=voice_speed,
            filename_prefix="story",
        )
        patch = voice_session.make_patch(last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Narration is ready.",
            session_state_patch=patch,
            result=response.model_dump(),
        )

    if action == ActionType.feedback_like:
        await feedback.submit_feedback(
            FeedbackRequest(story_id=ui_context.story_id, feedback=FeedbackValue.like)
        )
        patch = voice_session.make_patch(last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Glad you liked it.",
            session_state_patch=patch,
        )

    if action == ActionType.feedback_dislike:
        await feedback.submit_feedback(
            FeedbackRequest(story_id=ui_context.story_id, feedback=FeedbackValue.dislike)
        )
        patch = voice_session.make_patch(last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Thanks, I will use that feedback.",
            session_state_patch=patch,
        )

    if action in {
        ActionType.set_genre,
        ActionType.set_mood,
        ActionType.set_length,
        ActionType.set_voice_gender,
        ActionType.set_voice_speed,
    }:
        patch = voice_session.make_patch(last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            arguments=intent.arguments,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Updated that setting.",
            session_state_patch=patch,
            result=intent.arguments,
        )

    if action in UI_COMMANDS:
        if not ui_context.audio_url:
            raise BusinessRuleError("There is no generated audio available for playback controls")
        patch = voice_session.make_patch(last_action=action)
        await voice_session.apply_patch(session_id, patch)
        return ActionExecutionResult(
            phase_result=PhaseResult.command_detected,
            action=action,
            confidence=intent.confidence,
            spoken_response_text=spoken_response or "Done.",
            ui_command=action.value,
            session_state_patch=patch,
        )

    return ActionExecutionResult(
        phase_result=PhaseResult.rejected,
        action=ActionType.none,
        confidence=intent.confidence,
        spoken_response_text=spoken_response or "I need a clearer command for that.",
    )


def _maybe_enum(value, enum_cls):
    if value is None or isinstance(value, enum_cls):
        return value
    return enum_cls(value)

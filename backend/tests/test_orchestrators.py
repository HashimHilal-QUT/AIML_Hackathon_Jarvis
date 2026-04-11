import pytest

from src.models import (
    ActionType,
    Genre,
    IntentResult,
    Mood,
    StoryLength,
    VoiceGender,
    VoiceMode,
    VoiceSpeed,
    VoiceUIContext,
)
from src.services import action_executor, intent_parser, story_generator, stt, tts
from src.services.errors import BusinessRuleError, ProviderFailure


@pytest.mark.asyncio
async def test_story_generator_primary_success(monkeypatch) -> None:
    async def fake_invoke(*, provider, model, prompt, timeout):
        return {"title": "Moonlight", "body": "A calm tale.", "_provider": provider, "_model": model}

    monkeypatch.setattr(story_generator, "_invoke", fake_invoke)

    response = await story_generator.generate_story(
        genre=Genre.fantasy,
        mood=Mood.cozy,
        length=StoryLength.short,
    )

    assert response.title == "Moonlight"
    assert response.provider_used == story_generator.settings.story_primary_provider


@pytest.mark.asyncio
async def test_stt_fallback_success(monkeypatch) -> None:
    async def fake_invoke(*, provider, model, audio_bytes, filename, content_type):
        if provider == stt.settings.stt_primary_provider:
            raise RuntimeError("primary failed")
        return {"transcript": "hey jarvis", "provider": provider, "model": model}

    monkeypatch.setattr(stt, "_invoke", fake_invoke)

    result = await stt.transcribe(audio_bytes=b"audio", filename="voice.wav", content_type="audio/wav")

    assert result["provider"] == stt.settings.stt_fallback_provider
    assert result["transcript"] == "hey jarvis"


@pytest.mark.asyncio
async def test_tts_raises_when_both_providers_fail(monkeypatch) -> None:
    async def fake_invoke(*, provider, model, text, mood, voice_gender, voice_speed):
        raise RuntimeError(f"{provider} failed")

    monkeypatch.setattr(tts, "_invoke", fake_invoke)

    with pytest.raises(ProviderFailure):
        await tts.generate_audio(
            text="hello",
            mood=Mood.calm,
            voice_gender=VoiceGender.female,
            voice_speed=VoiceSpeed.normal,
        )


@pytest.mark.asyncio
async def test_intent_parser_fallback_on_primary_failure(monkeypatch) -> None:
    async def fake_invoke(*, provider, model, system_prompt, user_prompt):
        if provider == intent_parser.settings.reasoning_primary_provider:
            raise RuntimeError("schema parse failed")
        return {
            "action": "set_mood",
            "arguments": {"mood": "calm"},
            "confidence": 0.92,
            "needs_clarification": False,
            "spoken_response": "Switching to calm.",
            "_provider": provider,
            "_model": model,
        }

    monkeypatch.setattr(intent_parser, "_invoke", fake_invoke)

    result = await intent_parser.parse_intent(
        transcript="make it calm",
        mode=VoiceMode.command_mode,
        ui_context=VoiceUIContext(),
    )

    assert result.action == ActionType.set_mood
    assert result.provider_used == intent_parser.settings.reasoning_fallback_provider


@pytest.mark.asyncio
async def test_action_executor_blocks_play_without_audio() -> None:
    with pytest.raises(BusinessRuleError):
        await action_executor.execute(
            session_id="session-1",
            intent=IntentResult(action=ActionType.play_audio, confidence=0.8),
            ui_context=VoiceUIContext(),
        )

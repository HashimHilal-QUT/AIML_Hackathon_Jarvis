from __future__ import annotations

from src.config import settings
from src.models import Mood, VoiceGender, VoiceSpeed


ELEVENLABS_VOICES = {
    VoiceGender.male: settings.elevenlabs_male_voice_id or "JBFqnCBsd6RMkjVDRZzb",
    VoiceGender.female: settings.elevenlabs_female_voice_id or "EXAVITQu4vr4xnSDxMaL",
}

GOOGLE_TTS_VOICES = {
    VoiceGender.male: "en-US-Neural2-D",
    VoiceGender.female: "en-US-Neural2-F",
}

SPEED_MAP = {
    VoiceSpeed.slow: 0.85,
    VoiceSpeed.normal: 1.0,
    VoiceSpeed.fast: 1.15,
}

MOOD_STABILITY_MAP = {
    Mood.cozy: (0.72, 0.28),
    Mood.calm: (0.8, 0.15),
    Mood.adventurous: (0.45, 0.55),
    Mood.fun: (0.38, 0.65),
    Mood.mysterious: (0.55, 0.42),
}

MOOD_PITCH_MAP = {
    Mood.cozy: -0.5,
    Mood.calm: -1.0,
    Mood.adventurous: 1.0,
    Mood.fun: 1.5,
    Mood.mysterious: -0.2,
}


def get_elevenlabs_params(mood: Mood, gender: VoiceGender, speed: VoiceSpeed) -> dict[str, float | str]:
    stability, style = MOOD_STABILITY_MAP[mood]
    return {
        "voice_id": ELEVENLABS_VOICES[gender],
        "speed": SPEED_MAP[speed],
        "stability": stability,
        "style": style,
    }


def get_google_tts_params(mood: Mood, gender: VoiceGender, speed: VoiceSpeed) -> dict[str, float | str]:
    return {
        "voice_name": GOOGLE_TTS_VOICES[gender],
        "speaking_rate": SPEED_MAP[speed],
        "pitch": MOOD_PITCH_MAP[mood],
    }

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())


class Genre(str, Enum):
    heartwarming = "heartwarming"
    horror = "horror"
    study = "study"
    fantasy = "fantasy"
    adventure = "adventure"
    scifi = "scifi"


class Mood(str, Enum):
    cozy = "cozy"
    calm = "calm"
    adventurous = "adventurous"
    fun = "fun"
    mysterious = "mysterious"


class StoryLength(str, Enum):
    short = "3"
    medium = "5"
    long = "10"


class VoiceGender(str, Enum):
    male = "male"
    female = "female"


class VoiceSpeed(str, Enum):
    slow = "slow"
    normal = "normal"
    fast = "fast"


class VoiceMode(str, Enum):
    wake_mode = "wake_mode"
    command_mode = "command_mode"


class AudioPlaybackState(str, Enum):
    idle = "idle"
    ready = "ready"
    playing = "playing"
    paused = "paused"
    stopped = "stopped"


class FeedbackValue(str, Enum):
    like = "like"
    dislike = "dislike"


class ActionType(str, Enum):
    activate_app = "activate_app"
    generate_story = "generate_story"
    regenerate_story = "regenerate_story"
    generate_audio = "generate_audio"
    set_genre = "set_genre"
    set_mood = "set_mood"
    set_length = "set_length"
    set_voice_gender = "set_voice_gender"
    set_voice_speed = "set_voice_speed"
    feedback_like = "feedback_like"
    feedback_dislike = "feedback_dislike"
    play_audio = "play_audio"
    pause_audio = "pause_audio"
    resume_audio = "resume_audio"
    stop_audio = "stop_audio"
    listening_on = "listening_on"
    listening_off = "listening_off"
    none = "none"


class PhaseResult(str, Enum):
    wake_detected = "wake_detected"
    command_detected = "command_detected"
    ignored = "ignored"
    rejected = "rejected"


class StoryGenerateRequest(APIModel):
    genre: Genre
    mood: Mood
    length: StoryLength


class StoryGenerateResponse(APIModel):
    story_id: str
    title: str
    body: str
    provider_used: str
    model_used: str


class AudioGenerateRequest(APIModel):
    story_text: str = Field(min_length=1)
    mood: Mood
    voice_gender: VoiceGender
    voice_speed: VoiceSpeed
    filename_prefix: str = "story"


class AudioGenerateResponse(APIModel):
    audio_url: str
    provider_used: str
    model_used: str
    filename: str


class FeedbackRequest(APIModel):
    story_id: str | None = None
    feedback: FeedbackValue
    notes: str | None = None


class FeedbackResponse(APIModel):
    status: str
    message: str


class VoiceUIContext(APIModel):
    model_config = ConfigDict(extra="ignore", protected_namespaces=())

    genre: Genre | None = None
    mood: Mood | None = None
    length: StoryLength | None = None
    voice_gender: VoiceGender | None = None
    voice_speed: VoiceSpeed | None = None
    story_id: str | None = None
    story_title: str | None = None
    story_text: str | None = None
    audio_url: str | None = None
    audio_playback_state: AudioPlaybackState = AudioPlaybackState.idle
    listening_enabled: bool = True
    app_activated: bool = False


class VoiceSessionStartRequest(APIModel):
    listening_enabled: bool = True
    app_activated: bool = False


class VoiceSessionStartResponse(APIModel):
    session_id: str
    listening_enabled: bool
    app_activated: bool
    wake_phrase: str


class RealtimeVoiceSessionRequest(APIModel):
    model: str | None = None
    voice: str | None = None
    instructions: str | None = None


class RealtimeVoiceSessionResponse(APIModel):
    provider: str = "openai"
    session_type: str = "realtime"
    session_id: str | None = None
    client_secret: str
    expires_at: int | None = None
    model: str
    voice: str
    instructions: str


class VoiceAction(APIModel):
    action: ActionType
    arguments: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    needs_clarification: bool = False
    spoken_response: str | None = None
    ui_command: str | None = None


class SessionStatePatch(APIModel):
    app_activated: bool | None = None
    listening_enabled: bool | None = None
    last_action: ActionType | None = None


class VoiceCommandResponse(APIModel):
    session_id: str
    mode: VoiceMode
    transcript: str
    phase_result: PhaseResult
    action: ActionType | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    spoken_response_text: str | None = None
    spoken_response_audio_url: str | None = None
    ui_command: str | None = None
    session_state_patch: SessionStatePatch | None = None
    provider_chain: dict[str, str] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


class ProviderHealth(APIModel):
    primary_provider: str
    primary_model: str
    primary_state: str
    fallback_provider: str
    fallback_model: str
    fallback_state: str


class HealthResponse(APIModel):
    status: str
    service: str = "bedtime-story-backend"
    voice_command_ready: bool
    story_generation_ready: bool
    providers: dict[str, ProviderHealth]


class IntentResult(APIModel):
    action: ActionType
    arguments: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    needs_clarification: bool = False
    spoken_response: str | None = None
    phase_result: PhaseResult = PhaseResult.command_detected
    provider_used: str | None = None
    model_used: str | None = None


class ActionExecutionResult(APIModel):
    phase_result: PhaseResult
    action: ActionType | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    spoken_response_text: str | None = None
    ui_command: str | None = None
    session_state_patch: SessionStatePatch | None = None
    result: dict[str, Any] = Field(default_factory=dict)

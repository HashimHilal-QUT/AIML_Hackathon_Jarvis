from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
LLMOPS_DIR = PROJECT_ROOT / "llmops" / "prompts"
LOCAL_MEDIA_DIR = BASE_DIR / "media"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    debug: bool = False
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGINS",
    )

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    google_tts_credentials_json: str | None = Field(default=None, alias="GOOGLE_TTS_CREDENTIALS_JSON")
    google_stt_credentials_json: str | None = Field(default=None, alias="GOOGLE_STT_CREDENTIALS_JSON")

    story_primary_provider: str = Field(default="openai", alias="STORY_PRIMARY_PROVIDER")
    story_primary_model: str = Field(default="gpt-5.4-mini", alias="STORY_PRIMARY_MODEL")
    story_fallback_provider: str = Field(default="google", alias="STORY_FALLBACK_PROVIDER")
    story_fallback_model: str = Field(default="gemma-4", alias="STORY_FALLBACK_MODEL")
    story_timeout_seconds: float = Field(default=45.0, alias="STORY_TIMEOUT_SECONDS")

    reasoning_primary_provider: str = Field(default="openai", alias="REASONING_PRIMARY_PROVIDER")
    reasoning_primary_model: str = Field(default="gpt-5.4-mini", alias="REASONING_PRIMARY_MODEL")
    reasoning_fallback_provider: str = Field(default="google", alias="REASONING_FALLBACK_PROVIDER")
    reasoning_fallback_model: str = Field(default="gemma-4", alias="REASONING_FALLBACK_MODEL")
    reasoning_timeout_seconds: float = Field(default=20.0, alias="REASONING_TIMEOUT_SECONDS")

    stt_primary_provider: str = Field(default="openai", alias="STT_PRIMARY_PROVIDER")
    stt_primary_model: str = Field(default="gpt-4o-transcribe", alias="STT_PRIMARY_MODEL")
    stt_fallback_provider: str = Field(default="google", alias="STT_FALLBACK_PROVIDER")
    stt_fallback_model: str = Field(default="chirp_2", alias="STT_FALLBACK_MODEL")
    stt_timeout_seconds: float = Field(default=20.0, alias="STT_TIMEOUT_SECONDS")

    tts_primary_provider: str = Field(default="elevenlabs", alias="TTS_PRIMARY_PROVIDER")
    tts_primary_model: str = Field(default="eleven_multilingual_v2", alias="TTS_PRIMARY_MODEL")
    tts_fallback_provider: str = Field(default="google", alias="TTS_FALLBACK_PROVIDER")
    tts_fallback_model: str = Field(default="Neural2", alias="TTS_FALLBACK_MODEL")
    tts_timeout_seconds: float = Field(default=30.0, alias="TTS_TIMEOUT_SECONDS")

    elevenlabs_api_key: str | None = Field(default=None, alias="ELEVENLABS_API_KEY")
    elevenlabs_male_voice_id: str | None = Field(default=None, alias="ELEVENLABS_MALE_VOICE_ID")
    elevenlabs_female_voice_id: str | None = Field(default=None, alias="ELEVENLABS_FEMALE_VOICE_ID")

    azure_storage_connection_string: str | None = Field(default=None, alias="AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_container: str = Field(default="story-audio", alias="AZURE_STORAGE_CONTAINER")
    azure_sas_expiry_hours: int = Field(default=24, alias="AZURE_SAS_EXPIRY_HOURS")
    local_media_url_base: str = Field(default="/media", alias="LOCAL_MEDIA_URL_BASE")

    voice_wake_phrase: str = Field(default="hey jarvis", alias="VOICE_WAKE_PHRASE")
    voice_require_wake_phrase: bool = Field(default=False, alias="VOICE_REQUIRE_WAKE_PHRASE")
    voice_command_confidence_threshold: float = Field(default=0.6, alias="VOICE_COMMAND_CONFIDENCE_THRESHOLD")
    voice_max_audio_bytes: int = Field(default=5_242_880, alias="VOICE_MAX_AUDIO_BYTES")

    cb_failure_threshold: int = Field(default=3, alias="CB_FAILURE_THRESHOLD")
    cb_recovery_timeout_seconds: float = Field(default=60.0, alias="CB_RECOVERY_TIMEOUT_SECONDS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            if value.strip().startswith("["):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return []

    def resolve_google_credentials(self, raw_value: str | None) -> dict[str, Any] | None:
        if not raw_value:
            return None
        potential_path = Path(raw_value)
        if potential_path.exists():
            return json.loads(potential_path.read_text(encoding="utf-8"))
        return json.loads(raw_value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    LOCAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    return Settings()


settings = get_settings()

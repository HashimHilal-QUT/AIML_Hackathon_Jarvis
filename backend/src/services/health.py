from __future__ import annotations

from src.models import HealthResponse
from src.services import intent_parser, story_generator, stt, tts


async def get_health() -> HealthResponse:
    providers = {
        "story_generation": story_generator.get_health(),
        "stt": stt.get_health(),
        "reasoning": intent_parser.get_health(),
        "tts": tts.get_health(),
    }
    primary_open = any(item.primary_state == "OPEN" for item in providers.values())
    status = "degraded" if primary_open else "healthy"
    return HealthResponse(
        status=status,
        voice_command_ready=True,
        story_generation_ready=True,
        providers=providers,
    )

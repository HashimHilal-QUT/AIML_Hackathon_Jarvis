from fastapi import APIRouter

from src.models import HealthResponse
from src.services import health


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    return await health.get_health()

from fastapi import APIRouter

from src.models import FeedbackRequest, FeedbackResponse
from src.services import feedback


router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    return await feedback.submit_feedback(payload)

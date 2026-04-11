from __future__ import annotations

import logging

from src.models import FeedbackRequest, FeedbackResponse


logger = logging.getLogger(__name__)


async def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    logger.info(
        "feedback_received story_id=%s feedback=%s notes=%s",
        payload.story_id,
        payload.feedback,
        payload.notes,
    )
    return FeedbackResponse(status="ok", message="Feedback recorded")

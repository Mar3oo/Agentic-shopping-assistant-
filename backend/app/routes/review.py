from fastapi import APIRouter

from backend.app.schemas.review import ReviewChatRequest, ReviewResponse, ReviewStartRequest
from backend.app.services.review_service import chat_review, start_review

router = APIRouter(prefix="/review", tags=["Review"])


@router.post("/start", response_model=ReviewResponse)
def start(request: ReviewStartRequest):
    return start_review(
        user_id=request.user_id,
        message=request.message,
        language=request.language,
    )


@router.post("/chat", response_model=ReviewResponse)
def chat(request: ReviewChatRequest):
    return chat_review(
        user_id=request.user_id,
        session_id=request.session_id,
        message=request.message,
        language=request.language,
    )

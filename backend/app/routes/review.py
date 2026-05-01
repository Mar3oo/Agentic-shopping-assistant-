from fastapi import APIRouter

from backend.app.schemas.review import ReviewChatRequest, ReviewStartRequest
from backend.app.services.review_service import chat_review, start_review

router = APIRouter(prefix="/review", tags=["Review"])


@router.post("/start")
def start(request: ReviewStartRequest):
    return start_review(user_id=request.user_id, message=request.message)


@router.post("/chat")
def chat(request: ReviewChatRequest):
    return chat_review(
        user_id=request.user_id,
        session_id=request.session_id,
        message=request.message,
    )

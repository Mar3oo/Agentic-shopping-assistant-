from fastapi import APIRouter

from backend.app.schemas.comparison import (
    ComparisonChatRequest,
    ComparisonStartRequest,
)
from backend.app.services.comparison_service import chat_comparison, start_comparison

router = APIRouter(prefix="/comparison", tags=["Comparison"])


@router.post("/start")
def start(request: ComparisonStartRequest):
    return start_comparison(user_id=request.user_id, message=request.message)


@router.post("/chat")
def chat(request: ComparisonChatRequest):
    return chat_comparison(
        user_id=request.user_id,
        message=request.message,
        session_id=request.session_id,
    )

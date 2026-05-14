from fastapi import APIRouter

from backend.app.schemas.comparison import (
    ComparisonChatRequest,
    ComparisonResponse,
    ComparisonStartRequest,
)
from backend.app.services.comparison_service import chat_comparison, start_comparison

router = APIRouter(prefix="/comparison", tags=["Comparison"])


@router.post("/start", response_model=ComparisonResponse)
def start(request: ComparisonStartRequest):
    return start_comparison(
        user_id=request.user_id,
        message=request.message,
        language=request.language,
    )


@router.post("/chat", response_model=ComparisonResponse)
def chat(request: ComparisonChatRequest):
    return chat_comparison(
        user_id=request.user_id,
        message=request.message,
        session_id=request.session_id,
        language=request.language,
    )

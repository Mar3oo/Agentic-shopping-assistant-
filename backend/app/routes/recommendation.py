from fastapi import APIRouter
from backend.app.schemas.recommendation import StartRequest, ChatRequest
from backend.app.services.recommendation_service import (
    start_recommendation,
    chat_recommendation,
)

router = APIRouter(prefix="/recommendation", tags=["Recommendation"])


@router.post("/start")
def start(request: StartRequest):
    return start_recommendation(user_id=request.user_id, message=request.message)


@router.post("/chat")
def chat(request: ChatRequest):
    return chat_recommendation(
        user_id=request.user_id,
        message=request.message,
        session_id=request.session_id,
    )

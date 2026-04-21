from fastapi import APIRouter
from backend.app.schemas.review import ReviewRequest
from backend.app.services.review_service import start_review, chat_review

router = APIRouter(prefix="/review", tags=["Review"])


@router.post("/start")
def start(request: ReviewRequest):
    return start_review(user_id="default_user", message=request.message)


@router.post("/chat")
def chat(request: ReviewRequest):
    return chat_review(user_id="default_user", message=request.message)

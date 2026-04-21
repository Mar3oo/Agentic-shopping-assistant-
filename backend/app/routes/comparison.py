from fastapi import APIRouter
from backend.app.schemas.comparison import ComparisonRequest
from backend.app.services.comparison_service import start_comparison, chat_comparison

router = APIRouter(prefix="/comparison", tags=["Comparison"])


@router.post("/start")
def start(request: ComparisonRequest):
    return start_comparison(user_id="default_user", message=request.message)


@router.post("/chat")
def chat(request: ComparisonRequest):
    return chat_comparison(user_id="default_user", message=request.message)

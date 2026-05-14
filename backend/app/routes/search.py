from fastapi import APIRouter

from backend.app.schemas.search import SearchRequest, SearchResponse
from backend.app.services.search_service import run_search

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse)
def search(request: SearchRequest):
    return run_search(
        user_id=request.user_id,
        message=request.message,
        language=request.language,
    )

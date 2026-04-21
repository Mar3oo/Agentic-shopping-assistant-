from fastapi import APIRouter
from backend.app.schemas.search import SearchRequest
from backend.app.services.search_service import run_search

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/")
def search(request: SearchRequest):
    return run_search(request.message)

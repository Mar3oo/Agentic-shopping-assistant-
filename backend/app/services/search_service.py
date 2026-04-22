import time
from threading import Lock

from Data_Base.search_history_repo import insert_search_history
from Data_Base.search_session_repo import upsert_search_session
from search_pipeline.pipeline import SearchPipeline

from backend.app.services.rate_limit_service import enforce_rate_limit
from backend.app.services.session_service import ensure_user

pipeline = SearchPipeline()
_SEARCH_CACHE: dict[str, dict] = {}
_CACHE_LOCK = Lock()
_SEARCH_CACHE_TTL_SECONDS = 10 * 60
_DEFAULT_SEARCH_LIMIT = 10
_DEFAULT_TOP_K = 5


def _normalize_query(query: str) -> str:
    return " ".join((query or "").strip().lower().split())


def _get_cached_products(normalized_query: str) -> list[dict] | None:
    now = time.time()

    with _CACHE_LOCK:
        entry = _SEARCH_CACHE.get(normalized_query)
        if not entry:
            return None

        if now - entry["timestamp"] > _SEARCH_CACHE_TTL_SECONDS:
            _SEARCH_CACHE.pop(normalized_query, None)
            return None

        return entry["data"]


def _set_cached_products(normalized_query: str, products: list[dict]) -> None:
    with _CACHE_LOCK:
        _SEARCH_CACHE[normalized_query] = {
            "data": products,
            "timestamp": time.time(),
        }


def _persist_search_artifacts(user_id: str, query: str, products: list[dict]) -> None:
    upsert_search_session(user_id=user_id, query=query, results=products)
    insert_search_history(user_id=user_id, query=query, results_count=len(products))


def _success_response(products: list[dict]) -> dict:
    return {
        "status": "success",
        "type": "search",
        "message": "Here are live search results",
        "data": {"products": products},
    }


def run_search(user_id: str, message: str) -> dict:
    enforce_rate_limit(user_id, "search", limit=20, window_seconds=60)
    ensure_user(user_id)

    query = (message or "").strip()
    normalized_query = _normalize_query(query)
    cached_products = _get_cached_products(normalized_query)

    if cached_products is not None:
        _persist_search_artifacts(user_id=user_id, query=query, products=cached_products)
        return _success_response(cached_products)

    try:
        products = pipeline.run(
            query=query,
            search_limit=_DEFAULT_SEARCH_LIMIT,
            top_k=_DEFAULT_TOP_K,
        )
        _set_cached_products(normalized_query, products)
        _persist_search_artifacts(user_id=user_id, query=query, products=products)
        return _success_response(products)
    except Exception as e:
        return {"status": "error", "type": "search", "message": str(e), "data": {}}

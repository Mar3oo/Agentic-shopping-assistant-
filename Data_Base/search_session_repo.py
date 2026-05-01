from datetime import datetime

from Data_Base.db import get_search_sessions_collection


def upsert_search_session(user_id: str, query: str, results: list[dict]) -> None:
    get_search_sessions_collection().update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "last_query": query,
                "last_results": results,
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )


def get_search_session(user_id: str) -> dict | None:
    return get_search_sessions_collection().find_one({"user_id": user_id}, {"_id": 0})

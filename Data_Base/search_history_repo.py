from datetime import datetime

from Data_Base.db import get_search_history_collection


def insert_search_history(user_id: str, query: str, results_count: int) -> None:
    get_search_history_collection().insert_one(
        {
            "user_id": user_id,
            "query": query,
            "results_count": results_count,
            "timestamp": datetime.utcnow(),
        }
    )


def list_search_history(user_id: str, limit: int = 20) -> list[dict]:
    return list(
        get_search_history_collection()
        .find({"user_id": user_id}, {"_id": 0})
        .sort("timestamp", -1)
        .limit(limit)
    )

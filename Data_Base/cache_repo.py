from datetime import datetime, timedelta

from Data_Base.db import get_cache_collection


def get_cache_entry(cache_key: str) -> dict | None:
    collection = get_cache_collection()
    now = datetime.utcnow()
    document = collection.find_one(
        {"cache_key": cache_key, "expires_at": {"$gt": now}},
        {"_id": 0},
    )
    if document:
        collection.update_one({"cache_key": cache_key}, {"$inc": {"hit_count": 1}})
    return document


def upsert_cache_entry(
    cache_key: str,
    namespace: str,
    request_fingerprint: dict,
    response: dict,
    ttl_seconds: int,
) -> None:
    now = datetime.utcnow()
    get_cache_collection().update_one(
        {"cache_key": cache_key},
        {
            "$set": {
                "namespace": namespace,
                "request_fingerprint": request_fingerprint,
                "response": response,
                "created_at": now,
                "expires_at": now + timedelta(seconds=ttl_seconds),
            },
            "$setOnInsert": {"hit_count": 0},
        },
        upsert=True,
    )

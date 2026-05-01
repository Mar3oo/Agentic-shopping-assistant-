from datetime import datetime
import uuid

from pymongo import DESCENDING, ReturnDocument

from Data_Base.db import get_sessions_collection


def create_session(
    user_id: str,
    agent_type: str,
    title: str | None = None,
    agent_state: dict | None = None,
) -> dict:
    collection = get_sessions_collection()
    now = datetime.utcnow()
    session = {
        "session_id": f"session_{uuid.uuid4().hex[:10]}",
        "user_id": user_id,
        "agent_type": agent_type,
        "status": "active",
        "title": (title or "").strip()[:120] or None,
        "last_sequence": 0,
        "message_count": 0,
        "version": 1,
        "agent_state": agent_state or {},
        "last_response_type": None,
        "last_error": None,
        "created_at": now,
        "updated_at": now,
        "last_message_at": now,
    }
    collection.insert_one(session)
    return session


def get_session(user_id: str, session_id: str) -> dict | None:
    return get_sessions_collection().find_one(
        {"user_id": user_id, "session_id": session_id},
        {"_id": 0},
    )


def list_user_sessions(user_id: str, limit: int = 20) -> list[dict]:
    return list(
        get_sessions_collection()
        .find({"user_id": user_id}, {"_id": 0, "agent_state": 0})
        .sort("updated_at", DESCENDING)
        .limit(limit)
    )


def update_session_state(
    user_id: str,
    session_id: str,
    agent_state: dict,
    last_response_type: str | None = None,
    status: str | None = None,
    last_error: str | None = None,
) -> None:
    updates = {
        "agent_state": agent_state,
        "updated_at": datetime.utcnow(),
        "last_error": last_error,
    }
    if last_response_type is not None:
        updates["last_response_type"] = last_response_type
    if status is not None:
        updates["status"] = status

    get_sessions_collection().update_one(
        {"user_id": user_id, "session_id": session_id},
        {"$set": updates, "$inc": {"version": 1}},
    )


def increment_message_counter(user_id: str, session_id: str) -> int:
    result = get_sessions_collection().find_one_and_update(
        {"user_id": user_id, "session_id": session_id},
        {
            "$inc": {"last_sequence": 1, "message_count": 1},
            "$set": {
                "updated_at": datetime.utcnow(),
                "last_message_at": datetime.utcnow(),
            },
        },
        projection={"last_sequence": 1},
        return_document=ReturnDocument.AFTER,
    )

    if not result:
        raise ValueError(f"Session not found: {session_id}")

    return result["last_sequence"]


def close_session(user_id: str, session_id: str) -> None:
    get_sessions_collection().update_one(
        {"user_id": user_id, "session_id": session_id},
        {"$set": {"status": "closed", "updated_at": datetime.utcnow()}},
    )

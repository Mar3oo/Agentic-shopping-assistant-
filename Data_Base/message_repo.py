from datetime import datetime
import uuid

from Data_Base.db import get_messages_collection
from Data_Base.session_repo import increment_message_counter


def add_message(
    user_id: str,
    session_id: str,
    agent_type: str,
    role: str,
    content: str,
    payload: object | None = None,
    metadata: dict | None = None,
) -> dict:
    sequence = increment_message_counter(user_id, session_id)
    message = {
        "message_id": f"msg_{uuid.uuid4().hex[:10]}",
        "user_id": user_id,
        "session_id": session_id,
        "agent_type": agent_type,
        "sequence": sequence,
        "role": role,
        "content": str(content),
        "payload": payload,
        "metadata": metadata,
        "created_at": datetime.utcnow(),
    }
    get_messages_collection().insert_one(message)
    return message


def get_session_messages(user_id: str, session_id: str, limit: int = 12) -> list[dict]:
    messages = list(
        get_messages_collection()
        .find({"user_id": user_id, "session_id": session_id}, {"_id": 0})
        .sort("sequence", -1)
        .limit(limit)
    )
    messages.reverse()
    return messages


def get_all_messages(user_id: str, session_id: str) -> list[dict]:
    return get_all_messages_limited(user_id, session_id, limit=None)


def get_all_messages_limited(
    user_id: str,
    session_id: str,
    limit: int | None = None,
) -> list[dict]:
    collection = get_messages_collection()
    query = {"user_id": user_id, "session_id": session_id}

    if limit is None:
        return list(collection.find(query, {"_id": 0}).sort("sequence", 1))

    messages = list(collection.find(query, {"_id": 0}).sort("sequence", -1).limit(limit))
    messages.reverse()
    return messages

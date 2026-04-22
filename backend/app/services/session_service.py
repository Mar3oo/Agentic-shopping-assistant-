from Data_Base.message_repo import (
    add_message,
    get_all_messages_limited,
    get_session_messages,
)
from Data_Base.session_repo import (
    close_session,
    create_session,
    get_session,
    list_user_sessions,
    update_session_state,
)
from Data_Base.user_repo import upsert_guest_user


def ensure_user(user_id: str) -> dict:
    return upsert_guest_user(user_id)


def open_session(user_id: str, agent_type: str, title: str) -> dict:
    ensure_user(user_id)
    return create_session(user_id=user_id, agent_type=agent_type, title=title)


def load_session(
    user_id: str,
    session_id: str,
    agent_type: str | None = None,
    require_active: bool = False,
) -> dict | None:
    session = get_session(user_id, session_id)
    if not session:
        return None
    if agent_type and session.get("agent_type") != agent_type:
        return None
    if require_active and session.get("status") != "active":
        return None
    return session


def append_user_message(
    user_id: str, session_id: str, agent_type: str, content: str
) -> dict:
    return add_message(user_id, session_id, agent_type, "user", content)


def append_assistant_message(
    user_id: str,
    session_id: str,
    agent_type: str,
    content: str,
    payload: object | None = None,
    metadata: dict | None = None,
) -> dict:
    return add_message(
        user_id,
        session_id,
        agent_type,
        "assistant",
        content,
        payload=payload,
        metadata=metadata,
    )


def recent_history(user_id: str, session_id: str, limit: int = 12) -> list[dict]:
    history = []
    for message in get_session_messages(user_id, session_id, limit=limit):
        history.append(
            {
                "role": message["role"],
                "content": str(message.get("content", ""))[:1000],
            }
        )
    return history


def persist_session_state(
    user_id: str,
    session_id: str,
    agent_state: dict,
    last_response_type: str | None = None,
    status: str | None = None,
    last_error: str | None = None,
) -> None:
    update_session_state(
        user_id=user_id,
        session_id=session_id,
        agent_state=agent_state,
        last_response_type=last_response_type,
        status=status,
        last_error=last_error,
    )


def list_sessions_for_user(user_id: str, limit: int = 20) -> list[dict]:
    return list_user_sessions(user_id, limit=limit)


def list_messages_for_session(
    user_id: str,
    session_id: str,
    limit: int | None = None,
) -> list[dict]:
    return get_all_messages_limited(user_id, session_id, limit=limit)


def close_session_for_user(user_id: str, session_id: str) -> None:
    close_session(user_id, session_id)

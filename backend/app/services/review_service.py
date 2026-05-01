from agents.reviews.agent import ReviewAgent

from backend.app.services.cache_service import load_cached_response, store_cached_response
from backend.app.services.rate_limit_service import enforce_rate_limit
from backend.app.services.session_service import (
    append_assistant_message,
    append_user_message,
    close_session_for_user,
    load_session,
    open_session,
    persist_session_state,
)


def _assistant_summary(result) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return result.get("summary", "Here are the reviews")
    return "Here are the reviews"


def _is_new_review_task(agent_state: dict, message: str) -> bool:
    normalized = " ".join(message.lower().strip().split())
    if normalized == "new_review":
        return True

    current_product = (agent_state.get("product") or "").strip().lower()
    if not current_product:
        return False

    candidate_product = ReviewAgent()._parse_product(message)
    return (
        ReviewAgent()._is_new_review(message)
        and bool(candidate_product)
        and candidate_product.strip().lower() != current_product
    )


def _open_empty_review_session(user_id: str, message: str) -> dict:
    session = open_session(user_id=user_id, agent_type="review", title=message)
    session_id = session["session_id"]
    prompt = "Ready for a new review search. Please enter a product."
    append_user_message(user_id, session_id, "review", message)
    persist_session_state(
        user_id,
        session_id,
        {},
        last_response_type="review_prompt",
        status="active",
        last_error=None,
    )
    append_assistant_message(
        user_id,
        session_id,
        "review",
        prompt,
        payload={"type": "review_prompt", "message": prompt},
        metadata={"reset": True},
    )
    return {
        "status": "success",
        "type": "reset",
        "message": prompt,
        "session_id": session_id,
        "data": {},
    }


def _start_review_session(
    user_id: str,
    message: str,
    enforce_limit_guard: bool = True,
) -> dict:
    if enforce_limit_guard:
        enforce_rate_limit(user_id, "review_start", limit=5, window_seconds=60)

    session = open_session(user_id=user_id, agent_type="review", title=message)
    session_id = session["session_id"]
    append_user_message(user_id, session_id, "review", message)

    try:
        fingerprint = {"message": message}
        cached = load_cached_response("review", fingerprint)

        if cached:
            result = cached["result"]
            agent_state = cached["agent_state"]
        else:
            agent = ReviewAgent()
            result = agent.start_review(message)
            agent_state = agent.to_state()
            if isinstance(result, dict) and agent_state.get("product"):
                store_cached_response(
                    "review",
                    fingerprint,
                    {"result": result, "agent_state": agent_state},
                )

        persist_session_state(
            user_id,
            session_id,
            agent_state,
            last_response_type="review",
            status="active",
            last_error=None,
        )
        append_assistant_message(
            user_id,
            session_id,
            "review",
            _assistant_summary(result),
            payload=result,
            metadata={"cached": bool(cached)},
        )

        return {
            "status": "success",
            "type": "review",
            "message": "Here are the reviews",
            "session_id": session_id,
            "data": result,
        }
    except Exception as exc:
        persist_session_state(
            user_id,
            session_id,
            {},
            status="error",
            last_error=str(exc),
        )
        append_assistant_message(
            user_id,
            session_id,
            "review",
            "Review request failed",
            payload={"error": str(exc)},
        )
        return {
            "status": "error",
            "type": "review",
            "message": str(exc),
            "session_id": session_id,
            "data": {},
        }


def start_review(user_id: str, message: str) -> dict:
    return _start_review_session(user_id, message, enforce_limit_guard=True)


def chat_review(user_id: str, session_id: str, message: str) -> dict:
    enforce_rate_limit(user_id, "review_chat", limit=12, window_seconds=60)

    session = load_session(
        user_id,
        session_id,
        agent_type="review",
        require_active=True,
    )
    if not session:
        return {
            "status": "error",
            "type": "review",
            "message": "Start review first",
            "data": {},
        }

    agent_state = session.get("agent_state", {})

    if _is_new_review_task(agent_state, message):
        close_session_for_user(user_id, session_id)
        if " ".join(message.lower().strip().split()) == "new_review":
            return _open_empty_review_session(user_id, message)
        return _start_review_session(user_id, message, enforce_limit_guard=False)

    append_user_message(user_id, session_id, "review", message)
    agent = ReviewAgent.from_state(agent_state)

    try:
        result = agent.handle_message(message)
    except Exception as exc:
        persist_session_state(
            user_id,
            session_id,
            agent_state,
            status="error",
            last_error=str(exc),
        )
        append_assistant_message(
            user_id,
            session_id,
            "review",
            "Review chat failed",
            payload={"error": str(exc)},
        )
        return {
            "status": "error",
            "type": "review",
            "message": str(exc),
            "session_id": session_id,
            "data": {},
        }

    persist_session_state(
        user_id,
        session_id,
        agent.to_state(),
        last_response_type="review",
        status="active",
        last_error=None,
    )
    append_assistant_message(
        user_id,
        session_id,
        "review",
        _assistant_summary(result),
        payload=result,
    )

    return {
        "status": "success",
        "type": "review",
        "message": "Updated review",
        "session_id": session_id,
        "data": result,
    }

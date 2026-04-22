from agents.comparison.agent import ComparisonAgent

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


def _assistant_summary(response) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        return response.get("summary", "Here is your comparison")
    return "Here is your comparison"


def _is_new_comparison_task(agent_state: dict, message: str) -> bool:
    normalized = message.strip().lower()
    if normalized == "new_comparison":
        return True

    current_products = [product.strip().lower() for product in agent_state.get("products") or []]
    if not current_products:
        return False

    candidate_products = [
        product.strip().lower()
        for product in ComparisonAgent()._parse_products(message)
        if product.strip()
    ]
    return len(candidate_products) >= 2 and candidate_products != current_products


def _open_empty_comparison_session(user_id: str, message: str) -> dict:
    session = open_session(user_id=user_id, agent_type="comparison", title=message)
    session_id = session["session_id"]
    prompt = "Ready for a new comparison. Please enter products."
    append_user_message(user_id, session_id, "comparison", message)
    persist_session_state(
        user_id,
        session_id,
        {},
        last_response_type="comparison_prompt",
        status="active",
        last_error=None,
    )
    append_assistant_message(
        user_id,
        session_id,
        "comparison",
        prompt,
        payload={"type": "comparison_prompt", "message": prompt},
        metadata={"reset": True},
    )
    return {
        "status": "success",
        "type": "reset",
        "message": prompt,
        "session_id": session_id,
        "data": {},
    }


def _start_comparison_session(
    user_id: str,
    message: str,
    enforce_limit_guard: bool = True,
) -> dict:
    if enforce_limit_guard:
        enforce_rate_limit(user_id, "comparison_start", limit=5, window_seconds=60)

    session = open_session(user_id=user_id, agent_type="comparison", title=message)
    session_id = session["session_id"]
    append_user_message(user_id, session_id, "comparison", message)

    try:
        fingerprint = {"message": message}
        cached = load_cached_response("comparison", fingerprint)

        if cached:
            response = cached["result"]
            agent_state = cached["agent_state"]
        else:
            agent = ComparisonAgent()
            response = agent.start_comparison(message)
            agent_state = agent.to_state()
            if isinstance(response, dict) and agent_state.get("comparison_active"):
                store_cached_response(
                    "comparison",
                    fingerprint,
                    {"result": response, "agent_state": agent_state},
                )

        persist_session_state(
            user_id,
            session_id,
            agent_state,
            last_response_type="comparison",
            status="active",
            last_error=None,
        )
        append_assistant_message(
            user_id,
            session_id,
            "comparison",
            _assistant_summary(response),
            payload=response,
            metadata={"cached": bool(cached)},
        )

        return {
            "status": "success",
            "type": "comparison",
            "message": "Here is your comparison",
            "session_id": session_id,
            "data": response,
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
            "comparison",
            "Comparison request failed",
            payload={"error": str(exc)},
        )
        return {
            "status": "error",
            "type": "comparison",
            "message": str(exc),
            "session_id": session_id,
            "data": {},
        }


def start_comparison(user_id: str, message: str) -> dict:
    return _start_comparison_session(user_id, message, enforce_limit_guard=True)


def chat_comparison(user_id: str, session_id: str, message: str) -> dict:
    enforce_rate_limit(user_id, "comparison_chat", limit=12, window_seconds=60)

    session = load_session(
        user_id,
        session_id,
        agent_type="comparison",
        require_active=True,
    )
    if not session:
        return {
            "status": "error",
            "type": "comparison",
            "message": "Start comparison first",
            "data": {},
        }

    agent_state = session.get("agent_state", {})

    if _is_new_comparison_task(agent_state, message):
        close_session_for_user(user_id, session_id)
        if message.strip().lower() == "new_comparison":
            return _open_empty_comparison_session(user_id, message)
        return _start_comparison_session(user_id, message, enforce_limit_guard=False)

    append_user_message(user_id, session_id, "comparison", message)
    agent = ComparisonAgent.from_state(agent_state)

    try:
        response = agent.handle_message(message)
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
            "comparison",
            "Comparison chat failed",
            payload={"error": str(exc)},
        )
        return {
            "status": "error",
            "type": "comparison",
            "message": str(exc),
            "session_id": session_id,
            "data": {},
        }

    persist_session_state(
        user_id,
        session_id,
        agent.to_state(),
        last_response_type="comparison",
        status="active",
        last_error=None,
    )
    append_assistant_message(
        user_id,
        session_id,
        "comparison",
        _assistant_summary(response),
        payload=response,
    )

    return {
        "status": "success",
        "type": "comparison",
        "message": "Updated comparison",
        "session_id": session_id,
        "data": response,
    }

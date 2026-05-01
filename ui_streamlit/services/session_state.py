from __future__ import annotations

import copy
from typing import Any

import streamlit as st

from config import (
    APP_TITLE,
    AUTH_PAGE,
    BACKEND_BASE_URL,
    COMPARISON_PAGE,
    RECOMMENDATION_PAGE,
    REVIEW_PAGE,
)
from services.api_client import (
    ApiClientError,
    get_session,
    get_session_messages,
    get_sessions,
)


_DEFAULT_STATE: dict[str, Any] = {
    "user_id": None,
    "user_mode": None,
    "user_email": None,
    "display_name": None,
    "active_session_id": None,
    "active_agent": None,
    "messages": [],
    "recommendation_session_id": None,
    "comparison_session_id": None,
    "review_session_id": None,
    "recommendation_messages": [],
    "comparison_messages": [],
    "review_messages": [],
    "recommendation_products": [],
    "recommendation_suggestions": [],
    "comparison_result": None,
    "review_result": None,
    "search_results": [],
    "selected_review_product": None,
    "history_loaded_session_id": None,
}

_AGENT_LABELS = {
    "recommendation": "Recommendation",
    "comparison": "Comparison",
    "review": "Review",
}

_AGENT_PAGES = {
    "recommendation": RECOMMENDATION_PAGE,
    "comparison": COMPARISON_PAGE,
    "review": REVIEW_PAGE,
}


def initialize_session_state() -> None:
    for key, value in _DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(value)


def navigate_to(page_path: str) -> bool:
    try:
        st.switch_page(page_path)
        return True
    except Exception:
        return False


def _set_active_session_query(session_id: str | None) -> None:
    try:
        if session_id:
            st.query_params["session_id"] = session_id
        elif "session_id" in st.query_params:
            del st.query_params["session_id"]
    except Exception:
        pass


def _query_session_id() -> str | None:
    try:
        value = st.query_params.get("session_id")
    except Exception:
        return None

    if isinstance(value, list):
        value = value[0] if value else None
    return str(value).strip() if value else None


def _truncate(text: str, limit: int = 40) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _normalize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for message in messages:
        normalized.append(
            {
                "role": "user" if message.get("role") == "user" else "assistant",
                "content": str(message.get("content") or ""),
                "payload": message.get("payload"),
            },
        )
    return normalized


def _first_user_content(messages: list[dict[str, Any]]) -> str | None:
    for message in messages:
        if message.get("role") == "user" and str(message.get("content") or "").strip():
            return str(message["content"])
    return None


def _session_title(session: dict[str, Any], user_id: str) -> str:
    title = str(session.get("title") or "").strip()
    if title:
        return _truncate(title)

    try:
        response = get_session_messages(session["session_id"], user_id=user_id, limit=6)
        messages = response.get("data", {}).get("messages", [])
        first_user_message = _first_user_content(messages)
    except (ApiClientError, KeyError):
        first_user_message = None

    return _truncate(first_user_message or "New Chat")


def _session_timestamp(session: dict[str, Any]) -> str | None:
    timestamp = session.get("last_message_at") or session.get("updated_at")
    if not timestamp:
        return None
    return str(timestamp).replace("T", " ")[:16]


def _last_assistant_payload(messages: list[dict[str, Any]]) -> Any | None:
    for message in reversed(messages):
        if message.get("role") != "user" and message.get("payload") is not None:
            return message.get("payload")
    return None


def _recommendation_suggestions() -> list[dict[str, str]]:
    return [
        {
            "type": "compare",
            "trigger": "after_recommendations",
            "message": "Want help comparing these products?",
        },
        {
            "type": "review",
            "trigger": "after_recommendations",
            "message": "Want to check real user reviews?",
        },
    ]


def _payload_data(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    data = payload.get("data")
    if data:
        return data
    return payload


def _hydrate_agent_state(
    agent_name: str,
    session: dict[str, Any],
    messages: list[dict[str, Any]],
) -> None:
    session_id = session.get("session_id")
    agent_state = session.get("agent_state") or {}
    last_payload = _last_assistant_payload(messages)

    st.session_state[f"{agent_name}_session_id"] = session_id
    set_agent_messages(agent_name, messages)

    if agent_name == "recommendation":
        products = agent_state.get("last_recommendations") or []
        payload_data = _payload_data(last_payload)
        if not products and isinstance(payload_data, dict):
            products = payload_data.get("products") or []
        elif not products and isinstance(payload_data, list):
            products = payload_data

        st.session_state.recommendation_products = products
        st.session_state.recommendation_suggestions = _recommendation_suggestions() if products else []
        st.session_state.selected_review_product = products[0].get("title") if products else None
    elif agent_name == "comparison":
        result = agent_state.get("comparison_result") or _payload_data(last_payload)
        st.session_state.comparison_result = result if result else None
    elif agent_name == "review":
        result = agent_state.get("reviews_data") or _payload_data(last_payload)
        st.session_state.review_result = result if result else None


def set_agent_messages(agent_name: str, messages: list[dict[str, Any]]) -> None:
    normalized_messages = copy.deepcopy(messages)
    st.session_state[f"{agent_name}_messages"] = normalized_messages
    if st.session_state.get("active_agent") == agent_name:
        st.session_state.messages = copy.deepcopy(normalized_messages)


def activate_session(agent_name: str, session_id: str | None) -> None:
    if not session_id:
        return
    set_session_id(agent_name, session_id)
    st.session_state.active_session_id = session_id
    st.session_state.active_agent = agent_name
    st.session_state.history_loaded_session_id = session_id
    _set_active_session_query(session_id)


def load_chat_session(user_id: str, session_id: str) -> str | None:
    session_response = get_session(session_id, user_id=user_id)
    session = session_response.get("data", {}).get("session")
    if not session:
        raise ApiClientError("Session not found.")

    agent_name = session.get("agent_type")
    if agent_name not in _AGENT_PAGES:
        raise ApiClientError("This session type is not supported in the UI.")

    messages_response = get_session_messages(session_id, user_id=user_id, limit=500)
    raw_messages = messages_response.get("data", {}).get("messages", [])
    messages = _normalize_messages(raw_messages)

    st.session_state.active_session_id = session_id
    st.session_state.active_agent = agent_name
    st.session_state.messages = copy.deepcopy(messages)
    st.session_state.history_loaded_session_id = session_id
    _set_active_session_query(session_id)
    _hydrate_agent_state(agent_name, session, messages)
    return agent_name


def clear_active_chat() -> None:
    st.session_state.active_session_id = None
    st.session_state.active_agent = None
    st.session_state.messages = []
    st.session_state.history_loaded_session_id = None
    _set_active_session_query(None)

    for agent_name in _AGENT_PAGES:
        st.session_state[f"{agent_name}_session_id"] = None
        st.session_state[f"{agent_name}_messages"] = []

    st.session_state.recommendation_products = []
    st.session_state.recommendation_suggestions = []
    st.session_state.selected_review_product = None
    st.session_state.comparison_result = None
    st.session_state.review_result = None


def reset_agent_state(agent_name: str) -> None:
    st.session_state[f"{agent_name}_session_id"] = None
    st.session_state[f"{agent_name}_messages"] = []

    if st.session_state.get("active_agent") == agent_name:
        st.session_state.active_session_id = None
        st.session_state.active_agent = None
        st.session_state.messages = []
        st.session_state.history_loaded_session_id = None
        _set_active_session_query(None)

    if agent_name == "recommendation":
        st.session_state.recommendation_products = []
        st.session_state.recommendation_suggestions = []
        st.session_state.selected_review_product = None
    elif agent_name == "comparison":
        st.session_state.comparison_result = None
    elif agent_name == "review":
        st.session_state.review_result = None


def reset_all_agent_state() -> None:
    reset_agent_state("recommendation")
    reset_agent_state("comparison")
    reset_agent_state("review")
    st.session_state.active_session_id = None
    st.session_state.active_agent = None
    st.session_state.messages = []
    st.session_state.history_loaded_session_id = None
    _set_active_session_query(None)
    st.session_state.search_results = []


def clear_user_state() -> None:
    for key, value in _DEFAULT_STATE.items():
        st.session_state[key] = copy.deepcopy(value)
    _set_active_session_query(None)


def set_authenticated_user(user_data: dict[str, Any]) -> None:
    reset_all_agent_state()
    st.session_state.user_id = user_data.get("user_id")
    st.session_state.user_mode = user_data.get("mode")
    st.session_state.user_email = user_data.get("email")
    st.session_state.display_name = user_data.get("display_name")


def ensure_authenticated() -> None:
    if st.session_state.get("user_id"):
        return

    st.warning("Please sign in or continue as guest before using the assistant.")
    if st.button("Open Auth Page", key="open_auth_page"):
        if not navigate_to(AUTH_PAGE):
            st.info("Use the sidebar to open the Auth page.")
    st.stop()


def set_session_id(agent_name: str, session_id: str | None) -> None:
    st.session_state[f"{agent_name}_session_id"] = session_id


def get_session_id(agent_name: str) -> str | None:
    return st.session_state.get(f"{agent_name}_session_id")


def append_chat_message(
    agent_name: str,
    role: str,
    content: str,
    payload: Any | None = None,
) -> None:
    messages_key = f"{agent_name}_messages"
    message = {"role": role, "content": content, "payload": payload}
    st.session_state[messages_key].append(message)
    if st.session_state.get("active_agent") == agent_name:
        st.session_state.messages.append(copy.deepcopy(message))


def _restore_active_session_from_query(user_id: str, current_page: str) -> None:
    session_id = _query_session_id()
    if not session_id or st.session_state.get("history_loaded_session_id") == session_id:
        return

    try:
        agent_name = load_chat_session(user_id, session_id)
    except ApiClientError as exc:
        st.sidebar.error(f"Could not restore chat: {exc}")
        _set_active_session_query(None)
        return

    target_page = _AGENT_PAGES.get(agent_name or "")
    if target_page and current_page != _AGENT_LABELS.get(agent_name):
        if navigate_to(target_page):
            st.stop()


def _render_chat_history_sidebar(current_page: str) -> None:
    user_id = st.session_state.get("user_id")
    if not user_id:
        return

    _restore_active_session_from_query(user_id, current_page)

    st.sidebar.divider()
    st.sidebar.title("💬 Chat History")

    if st.sidebar.button("➕ New Chat", key="new_chat", use_container_width=True):
        clear_active_chat()
        if current_page != "Recommendation":
            if navigate_to(RECOMMENDATION_PAGE):
                st.stop()
        st.rerun()

    try:
        response = get_sessions(user_id=user_id, limit=50)
        sessions = response.get("data", {}).get("sessions", [])
    except ApiClientError as exc:
        st.sidebar.error(f"Could not load chats: {exc}")
        return

    if not sessions:
        st.sidebar.info("No chats yet")
        return

    active_session_id = st.session_state.get("active_session_id")
    for session in sessions:
        session_id = session.get("session_id")
        if not session_id:
            continue

        title = _session_title(session, user_id)
        is_active = session_id == active_session_id
        label = f"● {title}" if is_active else title
        if st.sidebar.button(label, key=session_id, use_container_width=True):
            try:
                agent_name = load_chat_session(user_id, session_id)
            except ApiClientError as exc:
                st.error(f"Could not load chat: {exc}")
                continue

            target_page = _AGENT_PAGES.get(agent_name or "")
            if target_page and current_page != _AGENT_LABELS.get(agent_name):
                if navigate_to(target_page):
                    st.stop()
            st.rerun()

        meta = _AGENT_LABELS.get(session.get("agent_type"), "Chat")
        timestamp = _session_timestamp(session)
        if timestamp:
            meta = f"{meta} · {timestamp}"
        st.sidebar.caption(meta)


def render_sidebar(current_page: str) -> None:
    with st.sidebar:
        st.title(APP_TITLE)
        st.caption(f"Backend: {BACKEND_BASE_URL}")
        st.caption(f"Page: {current_page}")

        if st.session_state.get("user_id"):
            label = st.session_state.get("display_name") or st.session_state["user_id"]
            st.success(f"Signed in as {label}")
            st.write(f"Mode: `{st.session_state.get('user_mode') or 'unknown'}`")
            if st.session_state.get("user_email"):
                st.write(st.session_state["user_email"])

            with st.expander("Active sessions", expanded=False):
                st.write(
                    f"Recommendation: `{st.session_state.get('recommendation_session_id') or '-'}'",
                )
                st.write(
                    f"Comparison: `{st.session_state.get('comparison_session_id') or '-'}'",
                )
                st.write(f"Review: `{st.session_state.get('review_session_id') or '-'}'")

            if st.button("Logout", use_container_width=True):
                clear_user_state()
                if not navigate_to(AUTH_PAGE):
                    st.rerun()
        else:
            st.warning("Not signed in")

    _render_chat_history_sidebar(current_page)

from __future__ import annotations

import copy
from typing import Any

import streamlit as st

from config import APP_TITLE, AUTH_PAGE, BACKEND_BASE_URL


_DEFAULT_STATE: dict[str, Any] = {
    "user_id": None,
    "user_mode": None,
    "user_email": None,
    "display_name": None,
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


def reset_agent_state(agent_name: str) -> None:
    st.session_state[f"{agent_name}_session_id"] = None
    st.session_state[f"{agent_name}_messages"] = []

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
    st.session_state.search_results = []


def clear_user_state() -> None:
    for key, value in _DEFAULT_STATE.items():
        st.session_state[key] = copy.deepcopy(value)


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
    st.session_state[messages_key].append(
        {"role": role, "content": content, "payload": payload},
    )


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

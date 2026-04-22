from pathlib import Path
import sys

import streamlit as st

UI_ROOT = Path(__file__).resolve().parents[1]
if str(UI_ROOT) not in sys.path:
    sys.path.append(str(UI_ROOT))

from components.chat_box import render_chat_history, render_chat_input
from components.review_section import render_review_result
from config import APP_TITLE
from services.api_client import ApiClientError, chat_review, start_review
from services.session_state import (
    append_chat_message,
    activate_session,
    ensure_authenticated,
    get_session_id,
    initialize_session_state,
    render_sidebar,
    reset_agent_state,
    set_agent_messages,
)


st.set_page_config(page_title=f"Review | {APP_TITLE}", layout="wide")
initialize_session_state()
ensure_authenticated()
render_sidebar("Review")

st.title("Review")
st.write("Start a product review manually, or continue with the current review session.")

current_session_id = get_session_id("review")
if current_session_id:
    st.caption(f"Active review session: `{current_session_id}`")

with st.form("review_start_form"):
    review_query = st.text_input(
        "Review a product",
        placeholder="Example: iphone 13 reviews",
    )
    start_clicked = st.form_submit_button("Start Review")

if start_clicked:
    if not review_query.strip():
        st.warning("Please enter a review query.")
    else:
        try:
            response = start_review(
                user_id=st.session_state.user_id,
                message=review_query,
            )
            if response.get("status") != "success":
                st.error(response.get("message", "Review request failed."))
            else:
                reset_agent_state("review")
                activate_session("review", response.get("session_id"))
                st.session_state.review_result = response.get("data")
                set_agent_messages(
                    "review",
                    [
                        {"role": "user", "content": review_query},
                        {"role": "assistant", "content": response.get("message", "Review response"), "payload": response},
                    ],
                )
                st.rerun()
        except ApiClientError as exc:
            st.error(str(exc))

render_review_result(st.session_state.get("review_result"))

render_chat_history(
    st.session_state.review_messages,
    title="Review Chat",
    empty_text="No review conversation yet.",
)

review_chat_message = render_chat_input(
    key="review_chat_input",
    placeholder="Ask a follow-up about the current review",
)

if review_chat_message:
    review_session_id = get_session_id("review")
    if not review_session_id:
        st.warning("Start a review session first.")
    else:
        try:
            append_chat_message("review", "user", review_chat_message)
            response = chat_review(
                user_id=st.session_state.user_id,
                session_id=review_session_id,
                message=review_chat_message,
            )
            if response.get("status") != "success":
                st.session_state.review_messages.pop()
                set_agent_messages("review", st.session_state.review_messages)
                st.error(response.get("message", "Review chat failed."))
            else:
                if response.get("session_id"):
                    activate_session("review", response["session_id"])
                st.session_state.review_result = response.get("data")
                append_chat_message(
                    "review",
                    "assistant",
                    response.get("message", "Review response"),
                    response,
                )
                st.rerun()
        except ApiClientError as exc:
            st.session_state.review_messages.pop()
            set_agent_messages("review", st.session_state.review_messages)
            st.error(str(exc))

from pathlib import Path
import sys

import streamlit as st

UI_ROOT = Path(__file__).resolve().parents[1]
if str(UI_ROOT) not in sys.path:
    sys.path.append(str(UI_ROOT))

from components.chat_box import render_chat_history, render_chat_input
from components.comparison_table import render_comparison_result
from config import APP_TITLE
from services.api_client import ApiClientError, chat_comparison, start_comparison
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


st.set_page_config(page_title=f"Comparison | {APP_TITLE}", layout="wide")
initialize_session_state()
ensure_authenticated()
render_sidebar("Comparison")

st.title("Comparison")
st.write("Start a comparison manually, or continue with the current comparison session.")

current_session_id = get_session_id("comparison")
if current_session_id:
    st.caption(f"Active comparison session: `{current_session_id}`")

with st.form("comparison_start_form"):
    comparison_query = st.text_input(
        "Compare products",
        placeholder="Example: iphone 15 vs galaxy s24",
    )
    start_clicked = st.form_submit_button("Start Comparison")

if start_clicked:
    if not comparison_query.strip():
        st.warning("Please enter a comparison query.")
    else:
        try:
            response = start_comparison(
                user_id=st.session_state.user_id,
                message=comparison_query,
            )
            if response.get("status") != "success":
                st.error(response.get("message", "Comparison request failed."))
            else:
                reset_agent_state("comparison")
                activate_session("comparison", response.get("session_id"))
                st.session_state.comparison_result = response.get("data")
                set_agent_messages(
                    "comparison",
                    [
                        {"role": "user", "content": comparison_query},
                        {"role": "assistant", "content": response.get("message", "Comparison response"), "payload": response},
                    ],
                )
                st.rerun()
        except ApiClientError as exc:
            st.error(str(exc))

render_comparison_result(st.session_state.get("comparison_result"))

render_chat_history(
    st.session_state.comparison_messages,
    title="Comparison Chat",
    empty_text="No comparison conversation yet.",
)

comparison_chat_message = render_chat_input(
    key="comparison_chat_input",
    placeholder="Ask a follow-up about the current comparison",
)

if comparison_chat_message:
    comparison_session_id = get_session_id("comparison")
    if not comparison_session_id:
        st.warning("Start a comparison session first.")
    else:
        try:
            append_chat_message("comparison", "user", comparison_chat_message)
            response = chat_comparison(
                user_id=st.session_state.user_id,
                session_id=comparison_session_id,
                message=comparison_chat_message,
            )
            if response.get("status") != "success":
                st.session_state.comparison_messages.pop()
                set_agent_messages("comparison", st.session_state.comparison_messages)
                st.error(response.get("message", "Comparison chat failed."))
            else:
                if response.get("session_id"):
                    activate_session("comparison", response["session_id"])
                st.session_state.comparison_result = response.get("data")
                append_chat_message(
                    "comparison",
                    "assistant",
                    response.get("message", "Comparison response"),
                    response,
                )
                st.rerun()
        except ApiClientError as exc:
            st.session_state.comparison_messages.pop()
            set_agent_messages("comparison", st.session_state.comparison_messages)
            st.error(str(exc))

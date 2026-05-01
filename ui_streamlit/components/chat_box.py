from __future__ import annotations

from typing import Any

import streamlit as st


def render_chat_history(
    messages: list[dict[str, Any]],
    *,
    title: str,
    empty_text: str,
) -> None:
    st.subheader(title)
    if not messages:
        st.info(empty_text)
        return

    for message in messages:
        role = "assistant" if message.get("role") != "user" else "user"
        content = str(message.get("content") or "")
        with st.chat_message(role):
            st.markdown(content)


def render_chat_input(
    *,
    key: str,
    placeholder: str,
) -> str | None:
    return st.chat_input(placeholder=placeholder, key=key)

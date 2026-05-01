from __future__ import annotations

from typing import Any

import streamlit as st


def _render_string_list(items: list[Any], heading: str) -> None:
    if not items:
        return

    st.markdown(f"**{heading}**")
    for item in items:
        st.write(f"- {item}")


def render_review_result(result: dict | str | None, *, title: str = "Review") -> None:
    st.subheader(title)
    if not result:
        st.info("No review data available yet.")
        return

    if isinstance(result, str):
        st.info(result)
        return

    summary = result.get("summary")
    if summary:
        st.write(summary)

    sentiment = result.get("sentiment_score")
    if sentiment:
        st.caption(f"Sentiment: {sentiment}")

    value_for_money = result.get("value_for_money")
    if value_for_money:
        st.write(f"**Value for money:** {value_for_money}")

    _render_string_list(result.get("pros") or [], "Pros")
    _render_string_list(result.get("cons") or [], "Cons")
    _render_string_list(result.get("insights") or [], "Insights")
    _render_string_list(result.get("best_for") or [], "Best for")

    sources = result.get("sources") or []
    if sources:
        st.markdown("**Video sources**")
        for source in sources:
            if not isinstance(source, dict):
                continue
            title_text = source.get("title") or source.get("url") or "Source"
            url = source.get("url")
            if url:
                st.markdown(f"- [{title_text}]({url})")
            else:
                st.write(f"- {title_text}")

    with st.expander("Raw review payload", expanded=False):
        st.json(result)

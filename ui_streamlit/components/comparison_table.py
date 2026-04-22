from __future__ import annotations

from typing import Any

import streamlit as st


def _render_list_block(items: list[Any], heading: str) -> None:
    if not items:
        return

    st.markdown(f"**{heading}**")
    for item in items:
        st.write(f"- {item}")


def render_comparison_result(result: dict | str | None, *, title: str = "Comparison") -> None:
    st.subheader(title)
    if not result:
        st.info("No comparison data available yet.")
        return

    if isinstance(result, str):
        st.info(result)
        return

    summary = result.get("summary")
    if summary:
        st.write(summary)

    if result.get("type") == "feature_answer":
        feature = result.get("feature")
        if feature:
            st.caption(f"Feature: {feature}")
        comparison = result.get("comparison")
        if isinstance(comparison, dict) and comparison:
            st.dataframe([comparison], use_container_width=True, hide_index=True)

    comparison_rows = result.get("comparison_table")
    if isinstance(comparison_rows, list) and comparison_rows:
        st.dataframe(comparison_rows, use_container_width=True, hide_index=True)

    _render_list_block(result.get("key_differences") or [], "Key differences")

    recommendation = result.get("recommendation")
    if isinstance(recommendation, dict) and recommendation:
        st.markdown("**Recommendation notes**")
        for label, items in recommendation.items():
            st.write(label.replace("_", " ").title())
            if isinstance(items, list):
                for item in items:
                    st.write(f"- {item}")
            else:
                st.write(str(items))

    sources = result.get("sources") or []
    if sources:
        st.markdown("**Sources**")
        for source in sources:
            url = source.get("url") if isinstance(source, dict) else None
            if url:
                st.markdown(f"- [Source link]({url})")

    with st.expander("Raw comparison payload", expanded=False):
        st.json(result)

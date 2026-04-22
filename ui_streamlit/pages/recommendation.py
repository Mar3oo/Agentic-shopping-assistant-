from pathlib import Path
import sys

import streamlit as st

UI_ROOT = Path(__file__).resolve().parents[1]
if str(UI_ROOT) not in sys.path:
    sys.path.append(str(UI_ROOT))

from components.chat_box import render_chat_history, render_chat_input
from components.comparison_table import render_comparison_result
from components.product_cards import render_product_cards
from components.review_section import render_review_result
from config import APP_TITLE
from services.api_client import (
    ApiClientError,
    chat_recommendation,
    start_comparison,
    start_recommendation,
    start_review,
)
from services.session_state import (
    append_chat_message,
    activate_session,
    ensure_authenticated,
    get_session_id,
    initialize_session_state,
    render_sidebar,
    reset_agent_state,
    set_session_id,
)


st.set_page_config(page_title=f"Recommendation | {APP_TITLE}", layout="wide")
initialize_session_state()
ensure_authenticated()
render_sidebar("Recommendation")


def _apply_recommendation_response(prompt: str, response: dict, *, reset_messages: bool = False) -> None:
    if reset_messages:
        st.session_state.recommendation_messages = []

    session_id = response.get("session_id")
    if session_id:
        activate_session("recommendation", session_id)

    append_chat_message("recommendation", "user", prompt)
    append_chat_message("recommendation", "assistant", response.get("message", "Recommendation response"), response)

    response_type = response.get("type")
    if response_type == "recommendations":
        data = response.get("data", {})
        st.session_state.recommendation_products = data.get("products", [])
        st.session_state.recommendation_suggestions = data.get("suggestions", [])
        if not st.session_state.get("selected_review_product") and st.session_state.recommendation_products:
            st.session_state.selected_review_product = st.session_state.recommendation_products[0].get("title")
    elif response_type == "reset":
        st.session_state.recommendation_products = []
        st.session_state.recommendation_suggestions = []
        st.session_state.selected_review_product = None
        reset_agent_state("comparison")
        reset_agent_state("review")


def _apply_comparison_response(prompt: str, response: dict) -> None:
    session_id = response.get("session_id")
    if session_id:
        set_session_id("comparison", session_id)

    st.session_state.comparison_messages = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response.get("message", "Comparison response"), "payload": response},
    ]
    st.session_state.comparison_result = response.get("data")


def _apply_review_response(prompt: str, response: dict) -> None:
    session_id = response.get("session_id")
    if session_id:
        set_session_id("review", session_id)

    st.session_state.review_messages = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": response.get("message", "Review response"), "payload": response},
    ]
    st.session_state.review_result = response.get("data")


def _product_titles(products: list[dict]) -> list[str]:
    return [product.get("title") for product in products if product.get("title")]


def extract_short_name(title: str) -> str:
    cleaned_title = (title or "").strip()
    if not cleaned_title:
        return ""

    for separator in ("|", " - ", " -", "- "):
        if separator in cleaned_title:
            cleaned_title = cleaned_title.split(separator, 1)[0].strip()
            break

    words = []
    for raw_word in cleaned_title.replace("/", " ").split():
        word = raw_word.strip(" ,.;:()[]{}")
        if not word:
            continue
        if "-" in word and any(char.isdigit() for char in word):
            word = word.split("-", 1)[0]
        words.append(word)
        if len(words) == 5:
            break

    generic_suffixes = {"laptop", "notebook", "computer", "pc"}
    while len(words) > 3 and words[-1].lower() in generic_suffixes:
        words.pop()

    return " ".join(words) or cleaned_title


st.title("Recommendation")
st.write("Start here to get product recommendations and optionally launch comparison or review inline.")

current_session_id = get_session_id("recommendation")
if current_session_id:
    st.caption(f"Active recommendation session: `{current_session_id}`")

with st.form("recommendation_start_form"):
    initial_message = st.text_area(
        "What are you looking for?",
        placeholder="Example: I need a gaming laptop under 1500 dollars",
        height=120,
    )
    start_clicked = st.form_submit_button("Get Recommendations")

if start_clicked:
    if not initial_message.strip():
        st.warning("Please describe what you want first.")
    else:
        try:
            reset_agent_state("recommendation")
            reset_agent_state("comparison")
            reset_agent_state("review")
            response = start_recommendation(
                user_id=st.session_state.user_id,
                message=initial_message,
            )
            if response.get("status") != "success":
                st.error(response.get("message", "Recommendation request failed."))
            else:
                _apply_recommendation_response(initial_message, response, reset_messages=True)
                st.rerun()
        except ApiClientError as exc:
            st.error(str(exc))

products = st.session_state.recommendation_products
if products:
    render_product_cards(products, title="Recommended products")

    suggestions = st.session_state.recommendation_suggestions
    if suggestions:
        st.markdown("**Suggestions**")
        for suggestion in suggestions:
            st.write(f"- {suggestion.get('message')}")

    st.subheader("Next Actions")
    compare_col, review_col = st.columns(2)

    with compare_col:
        compare_options = _product_titles(products)
        has_enough_products = len(compare_options) >= 2
        if not has_enough_products:
            st.info("At least two products are needed for inline comparison.")

        selected_compare_products = st.multiselect(
            "Select 2 products to compare",
            options=compare_options,
            key="recommendation_compare_multiselect",
            disabled=not has_enough_products,
        )

        selected_count = len(selected_compare_products)
        if has_enough_products:
            if selected_count < 2:
                st.warning("Select exactly 2 products to compare.")
            elif selected_count > 2:
                st.warning("Select only 2 products to compare.")

        if selected_compare_products:
            st.write("You selected:")
            for selected_product in selected_compare_products:
                st.write(selected_product)

        can_compare_selected = has_enough_products and selected_count == 2
        if st.button(
            "Compare selected products",
            disabled=not can_compare_selected,
            use_container_width=True,
        ):
            product1, product2 = selected_compare_products
            short1 = extract_short_name(product1)
            short2 = extract_short_name(product2)
            query = f"compare {short1} vs {short2}"
            try:
                response = start_comparison(
                    user_id=st.session_state.user_id,
                    message=query,
                )
                if response.get("status") != "success":
                    st.error(response.get("message", "Comparison request failed."))
                else:
                    _apply_comparison_response(query, response)
                    st.rerun()
            except ApiClientError as exc:
                st.error(str(exc))

    with review_col:
        review_options = _product_titles(products)
        if review_options:
            default_product = st.session_state.get("selected_review_product")
            default_index = 0
            if default_product in review_options:
                default_index = review_options.index(default_product)

            selected_product = st.selectbox(
                "Pick a product to review",
                options=review_options,
                index=default_index,
                key="recommendation_review_selectbox",
            )
            st.session_state.selected_review_product = selected_product

            if st.button("Review a product", use_container_width=True):
                review_prompt = f"{selected_product} reviews"
                try:
                    response = start_review(
                        user_id=st.session_state.user_id,
                        message=review_prompt,
                    )
                    if response.get("status") != "success":
                        st.error(response.get("message", "Review request failed."))
                    else:
                        _apply_review_response(review_prompt, response)
                        st.rerun()
                except ApiClientError as exc:
                    st.error(str(exc))

if st.session_state.get("comparison_result"):
    render_comparison_result(
        st.session_state.comparison_result,
        title="Inline Comparison",
    )

if st.session_state.get("review_result"):
    render_review_result(
        st.session_state.review_result,
        title="Inline Review",
    )

render_chat_history(
    st.session_state.recommendation_messages,
    title="Recommendation Chat",
    empty_text="No recommendation conversation yet.",
)

recommendation_chat_message = render_chat_input(
    key="recommendation_chat_input",
    placeholder="Ask for refinements, explanations, or a new search",
)

if recommendation_chat_message:
    recommendation_session_id = get_session_id("recommendation")
    if not recommendation_session_id:
        st.warning("Start a recommendation session first.")
    else:
        try:
            response = chat_recommendation(
                user_id=st.session_state.user_id,
                session_id=recommendation_session_id,
                message=recommendation_chat_message,
            )
            if response.get("status") != "success":
                st.error(response.get("message", "Recommendation chat failed."))
            else:
                _apply_recommendation_response(recommendation_chat_message, response)
                st.rerun()
        except ApiClientError as exc:
            st.error(str(exc))

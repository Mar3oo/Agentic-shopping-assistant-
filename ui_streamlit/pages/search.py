from pathlib import Path
import sys

import streamlit as st

UI_ROOT = Path(__file__).resolve().parents[1]
if str(UI_ROOT) not in sys.path:
    sys.path.append(str(UI_ROOT))

from components.product_cards import render_product_cards
from config import APP_TITLE
from services.api_client import ApiClientError, search
from services.session_state import ensure_authenticated, initialize_session_state, render_sidebar


st.set_page_config(page_title=f"Search | {APP_TITLE}", layout="wide")
initialize_session_state()
ensure_authenticated()
render_sidebar("Search")

st.title("Search")
st.write("Run a stateless search over the backend search pipeline.")

with st.form("search_form"):
    search_query = st.text_input(
        "Search query",
        placeholder="Example: best laptops 2024",
    )
    search_clicked = st.form_submit_button("Search")

if search_clicked:
    if not search_query.strip():
        st.warning("Please enter a search query.")
    else:
        try:
            response = search(
                user_id=st.session_state.user_id,
                message=search_query,
            )
            if response.get("status") != "success":
                st.error(response.get("message", "Search request failed."))
            else:
                st.session_state.search_results = response.get("data", {}).get("products", [])
                st.rerun()
        except ApiClientError as exc:
            st.error(str(exc))

render_product_cards(
    st.session_state.get("search_results", []),
    title="Search Results",
)

from pathlib import Path
import sys

import streamlit as st

UI_ROOT = Path(__file__).resolve().parents[1]
if str(UI_ROOT) not in sys.path:
    sys.path.append(str(UI_ROOT))

from config import APP_TITLE, RECOMMENDATION_PAGE
from services.api_client import ApiClientError, create_guest_user, login, register
from services.session_state import (
    clear_user_state,
    initialize_session_state,
    navigate_to,
    render_sidebar,
    set_authenticated_user,
)


st.set_page_config(page_title=f"Auth | {APP_TITLE}", layout="wide")
initialize_session_state()
render_sidebar("Auth")

st.title("Sign In")
st.write("Use an existing account, create a new one, or continue as a guest.")

if st.session_state.get("user_id"):
    display_name = st.session_state.get("display_name") or st.session_state["user_id"]
    st.success(f"You are already signed in as {display_name}.")

    left, right = st.columns(2)
    with left:
        if st.button("Go to Recommendation", use_container_width=True):
            if not navigate_to(RECOMMENDATION_PAGE):
                st.info("Use the sidebar to open the Recommendation page.")
    with right:
        if st.button("Logout", use_container_width=True):
            clear_user_state()
            st.rerun()
    st.stop()


def _handle_success(response: dict) -> None:
    set_authenticated_user(response.get("data", {}))
    st.success(response.get("message", "Authentication successful"))
    if not navigate_to(RECOMMENDATION_PAGE):
        st.info("Use the sidebar to open the Recommendation page.")
        st.rerun()


login_tab, signup_tab = st.tabs(["Login", "Sign up"])

with login_tab:
    with st.form("login_form"):
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        login_submitted = st.form_submit_button("Login")

    if login_submitted:
        try:
            response = login(email=login_email, password=login_password)
            _handle_success(response)
        except ApiClientError as exc:
            st.error(str(exc))

with signup_tab:
    with st.form("signup_form"):
        signup_name = st.text_input("Display name", key="signup_name")
        signup_email = st.text_input("Email", key="signup_email")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_submitted = st.form_submit_button("Create account")

    if signup_submitted:
        try:
            response = register(
                email=signup_email,
                password=signup_password,
                display_name=signup_name or None,
            )
            _handle_success(response)
        except ApiClientError as exc:
            st.error(str(exc))

st.divider()

if st.button("Continue as Guest", use_container_width=True):
    try:
        response = create_guest_user()
        _handle_success(response)
    except ApiClientError as exc:
        st.error(str(exc))

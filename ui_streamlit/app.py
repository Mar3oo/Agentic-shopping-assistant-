import streamlit as st

from config import APP_TITLE, AUTH_PAGE, RECOMMENDATION_PAGE
from services.session_state import initialize_session_state, navigate_to, render_sidebar


st.set_page_config(page_title=APP_TITLE, layout="wide")
initialize_session_state()
render_sidebar("Welcome")

target_page = RECOMMENDATION_PAGE if st.session_state.get("user_id") else AUTH_PAGE
if navigate_to(target_page):
    st.stop()

st.title(APP_TITLE)
st.write("Welcome to the Streamlit UI for the AI shopping assistant.")

if st.session_state.get("user_id"):
    st.success("You are signed in.")
    if st.button("Open Recommendation Page", use_container_width=True):
        navigate_to(RECOMMENDATION_PAGE)
else:
    st.info("Please open the Auth page from the sidebar to continue.")
    if st.button("Open Auth Page", use_container_width=True):
        navigate_to(AUTH_PAGE)

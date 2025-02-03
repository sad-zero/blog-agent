import logging

import streamlit as st

from blog_agent.auth import authenticate

logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%dT%H:%M:%S",
    format="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
)

AUTH_KEY = "IS_AUTHENTICATED"
if not st.session_state.get(AUTH_KEY):
    secret = st.text_input("Secret")

    if not st.button("Enter"):
        st.stop()
    if not authenticate(secret=secret):
        st.warning("Invalid secret. Try other secrets")
        st.stop()

    st.session_state[AUTH_KEY] = True


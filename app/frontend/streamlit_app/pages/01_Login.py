from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.ui_theme import (
    apply_theme,
    render_badges,
    render_disclaimer,
    render_fixed_app_nav,
    render_action_card,
    render_sidebar_navigation,
)


st.set_page_config(
    page_title="Login | TriageAI",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()
render_sidebar_navigation("Login")

render_fixed_app_nav("Login", "Welcome")
st.markdown(
    """
    <style>
    div[data-testid="stTabs"],
    div[data-testid="stForm"] {
        max-width: 680px;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ta-auth-card">
        <h1>Sign in to the clinical workflow</h1>
        <p>ESI Clinical Intake & Care Routing</p>
    </div>
    """,
    unsafe_allow_html=True,
)
render_badges(
    [
        "Structured Intake",
        "Safety Escalation",
        "Clinician Review",
        "Audit Trail",
    ]
)

auth_tabs = st.tabs(["Sign in", "Create account"])

with auth_tabs[0]:
    with st.form("sign_in_form"):
        st.markdown(
            '<div class="ta-section-label">Sign In</div>', unsafe_allow_html=True
        )
        email = st.text_input("Email", placeholder="clinician@example.com")
        st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary")
    if submitted:
        st.session_state["auth_status"] = "signed_in"
        st.session_state["auth_user"] = email.strip() or "clinical-user"
        st.success("Signed in for this Streamlit session.")

with auth_tabs[1]:
    with st.form("create_account_form"):
        st.markdown(
            '<div class="ta-section-label">Create Account</div>',
            unsafe_allow_html=True,
        )
        name = st.text_input("Name", placeholder="Clinical reviewer")
        new_email = st.text_input("Work email", placeholder="clinician@example.com")
        st.text_input("Create password", type="password")
        created = st.form_submit_button("Create Account", type="primary")
    if created:
        st.session_state["auth_status"] = "account_created"
        st.session_state["auth_user"] = (
            new_email.strip() or name.strip() or "clinical-user"
        )
        st.success("Account created for this Streamlit session.")

render_action_card(
    "Continue as guest",
    "Use the clinical decision-support workflow without creating a session account.",
)
nav_left, nav_right = st.columns([1, 1], gap="medium")
with nav_left:
    if st.button("Back to Home", width="stretch"):
        st.switch_page("Home.py")
with nav_right:
    continue_guest = st.button("Continue as Guest", type="primary", width="stretch")
if continue_guest:
    st.session_state["auth_status"] = "guest"
    st.session_state["auth_user"] = "guest"
    st.switch_page("pages/02_New_Assessment.py")

render_disclaimer()

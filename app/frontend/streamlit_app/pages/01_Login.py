from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.components.layout import render_backend_status
from app.frontend.streamlit_app.ui_theme import (
    apply_theme,
    render_badges,
    render_disclaimer,
    render_top_header,
)


st.set_page_config(page_title="Login | TriageAI", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown("### TriageAI / SympDirect")
    st.caption("ESI care-routing workflow")
    render_backend_status()

render_top_header("Welcome")

_, auth_col, _ = st.columns([0.12, 0.76, 0.12])
with auth_col:
    st.markdown(
        """
        <div class="ta-auth-card">
            <div class="ta-logo">+</div>
            <h1>Welcome to TriageAI / SympDirect</h1>
            <p>ESI Clinical Intake & Care Routing Assistant</p>
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

    st.markdown(
        """
        <div class="ta-card">
            <h3>Continue as guest</h3>
            <p>Use the clinical decision-support workflow without creating a session account.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Continue as Guest", width="stretch"):
        st.session_state["auth_status"] = "guest"
        st.session_state["auth_user"] = "guest"
        st.switch_page("pages/02_New_Assessment.py")

    render_disclaimer()

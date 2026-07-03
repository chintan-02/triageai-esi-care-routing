from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.ui_theme import (
    apply_theme,
    render_action_cards,
    render_disclaimer,
    render_fixed_app_nav,
    render_home_hero,
    render_sidebar_navigation,
    render_workflow_card,
)


st.set_page_config(
    page_title="TriageAI / SympDirect",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()
render_sidebar_navigation("Home")

render_fixed_app_nav("Home", "System Active")
render_home_hero()
render_workflow_card()
render_action_cards()

st.markdown("")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Start New Assessment", type="primary", width="stretch"):
        st.switch_page("pages/02_New_Assessment.py")
with col2:
    if st.button("Open Dashboard", width="stretch"):
        st.switch_page("pages/05_Dashboard.py")
with col3:
    if st.button("Review Assessment", width="stretch"):
        st.switch_page("pages/06_Assessment_Detail.py")

render_disclaimer()

with st.expander("Developer commands"):
    st.code(
        "python -m uvicorn app.backend.api.main:app --reload --port 8001\n"
        "python -m streamlit run app/frontend/streamlit_app/Home.py",
        language="bash",
    )

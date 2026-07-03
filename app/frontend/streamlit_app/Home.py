from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.components.layout import render_backend_status
from app.frontend.streamlit_app.ui_theme import (
    apply_theme,
    render_action_cards,
    render_disclaimer,
    render_home_hero,
    render_top_header,
    render_workflow_card,
)


st.set_page_config(page_title="TriageAI / SympDirect", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown("### TriageAI / SympDirect")
    st.caption("ESI care-routing workflow")
    render_backend_status()

render_top_header("System Active")
render_home_hero()
render_workflow_card()
render_action_cards()
render_disclaimer()

st.markdown("")

col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/02_New_Assessment.py", label="Start New Assessment", icon="📝")
with col2:
    st.page_link("pages/05_Dashboard.py", label="Open Dashboard", icon="📊")
with col3:
    st.page_link("pages/06_Assessment_Detail.py", label="Review Assessment", icon="🔎")

with st.expander("Developer commands"):
    st.markdown(
        """
        <div class="ta-dev">
        python -m uvicorn app.backend.api.main:app --reload --port 8001<br>
        streamlit run app/frontend/streamlit_app/Home.py
        </div>
        """,
        unsafe_allow_html=True,
    )

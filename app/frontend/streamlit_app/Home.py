from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.assets.styles import apply_app_styles
from app.frontend.streamlit_app.components.layout import render_backend_status


st.set_page_config(page_title="TriageAI SympDirect", layout="wide")
apply_app_styles()

st.title("TriageAI / SympDirect")
st.subheader("ESI Clinical Intake & Care Routing Assistant")

render_backend_status()

st.markdown(
    """
    TriageAI connects structured intake to the FastAPI ESI prediction service and
    presents decision-support output for clinician review.

    Use **New Assessment** to submit intake data to `/predict`, then review the
    model output, safety rules, recommendation, explanation, and clinician
    summary on **Assessment Result**.
    """
)

st.warning(
    "This tool is for clinical decision-support workflow testing only and is not "
    "a diagnosis or a substitute for clinician judgment."
)

st.code(
    "python -m uvicorn app.backend.api.main:app --reload --port 8001\n"
    "streamlit run app/frontend/streamlit_app/Home.py",
    language="bash",
)

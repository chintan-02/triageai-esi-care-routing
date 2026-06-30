from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.assets.styles import apply_app_styles
from app.frontend.streamlit_app.components.layout import render_backend_status
from app.frontend.streamlit_app.components.probability_chart import (
    render_probability_section,
)
from app.frontend.streamlit_app.components.result_card import render_main_result_card


DISCLAIMER = (
    "This tool is for clinical decision-support workflow testing only and is not "
    "a diagnosis or a substitute for clinician judgment."
)


def _render_safety_section(result: dict) -> None:
    st.subheader("Safety Review")
    safety_rules = result.get("safety_rules_triggered") or []
    triggered = [rule for rule in safety_rules if rule.get("triggered")]

    if not triggered:
        st.info("No safety-rule escalation triggered.")
        return

    st.warning("Safety-rule escalation triggered. Clinician review is required.")
    for rule in triggered:
        st.markdown(
            f"- **{rule.get('rule_id', 'safety_rule')}**: {rule.get('message', '')}"
        )


def _render_model_info(result: dict) -> None:
    st.subheader("Model Info")
    col1, col2 = st.columns(2)
    col1.metric("Model Loaded", str(result.get("model_loaded")))
    col2.metric("Placeholder", str(result.get("is_placeholder")))
    st.write(f"**Model version:** `{result.get('model_version') or 'Unavailable'}`")
    st.write(f"**Request ID:** `{result.get('request_id') or 'Unavailable'}`")
    st.write(f"**Assessment ID:** `{result.get('assessment_id') or 'Unavailable'}`")


st.set_page_config(page_title="Assessment Result | TriageAI", layout="wide")
apply_app_styles()

st.title("Assessment Result")
st.caption("Backend-generated ESI decision-support output.")

render_backend_status()

result = st.session_state.get("last_prediction_result")

if not result:
    st.info("No assessment result is available yet. Submit a new intake first.")
    if st.button("Go to New Assessment"):
        try:
            st.switch_page("pages/02_New_Assessment.py")
        except Exception:
            st.stop()
    st.stop()

if result.get("model_loaded") is False or result.get("is_placeholder") is True:
    st.markdown(
        '<div class="warning-box">Model inference is currently unavailable; '
        "displaying fallback contract response.</div>",
        unsafe_allow_html=True,
    )

render_main_result_card(result)

left, right = st.columns([1, 1])
with left:
    render_probability_section(result.get("probabilities") or {})
with right:
    _render_safety_section(result)

st.markdown('<div class="triage-section">', unsafe_allow_html=True)
st.subheader("Recommendation")
st.write(result.get("recommendation") or "No recommendation returned.")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="triage-section">', unsafe_allow_html=True)
st.subheader("Clinical Explanation")
st.write(result.get("explanation") or "No explanation returned.")
st.markdown("</div>", unsafe_allow_html=True)

st.subheader("Clinician Summary")
st.markdown(
    f'<div class="note-box">{result.get("clinician_summary") or "No summary returned."}</div>',
    unsafe_allow_html=True,
)

_render_model_info(result)

st.divider()
st.warning(DISCLAIMER)

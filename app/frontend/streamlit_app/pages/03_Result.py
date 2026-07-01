from pathlib import Path
import sys
from html import escape

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
from app.frontend.streamlit_app.components.summary_card import (
    render_clinician_summary_card,
)


DISCLAIMER = (
    "This tool is for clinical decision-support workflow testing only and is not "
    "a diagnosis or a substitute for clinician judgment."
)


def _html_card(title: str, body: str, *, class_name: str = "clinical-card") -> None:
    st.markdown(
        f"""
        <div class="{class_name}">
          <div class="eyebrow">{escape(title)}</div>
          <div style="color:#1e3a52;line-height:1.65;">{escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_safety_section(result: dict) -> None:
    st.markdown('<div class="section-title">Safety Review</div>', unsafe_allow_html=True)
    safety_rules = result.get("safety_rules_triggered") or []
    triggered = [rule for rule in safety_rules if rule.get("triggered")]

    if not triggered:
        st.markdown(
            '<div class="safety-ok">No safety-rule escalation triggered.</div>',
            unsafe_allow_html=True,
        )
        return

    rule_items = "".join(
        "<li><strong>"
        + escape(str(rule.get("rule_id", "safety_rule")))
        + ":</strong> "
        + escape(str(rule.get("message", "")))
        + "</li>"
        for rule in triggered
    )
    st.markdown(
        f"""
        <div class="safety-warn">
          <strong>Safety-rule override applied.</strong>
          Final ESI was escalated for safety and clinician review is required.
          <ul style="margin:.55rem 0 0 1.1rem;padding:0;line-height:1.6;">
            {rule_items}
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_model_details(result: dict) -> None:
    with st.expander("Model & audit details"):
        st.write(f"**Request ID:** `{result.get('request_id') or 'Unavailable'}`")
        st.write(f"**Assessment ID:** `{result.get('assessment_id') or 'Unavailable'}`")
        st.write(f"**Model version:** `{result.get('model_version') or 'Unavailable'}`")
        st.write(f"**Model loaded:** `{result.get('model_loaded')}`")
        st.write(f"**Placeholder:** `{result.get('is_placeholder')}`")
        st.write(f"**Final source:** `{result.get('final_source') or 'Unavailable'}`")


st.set_page_config(page_title="Assessment Result | TriageAI", layout="wide")
apply_app_styles()

st.markdown(
    """
    <div class="clinical-header">
      <div class="eyebrow">Assessment Result</div>
      <h1 style="margin:.1rem 0 .2rem 0;color:#0e1f35;">ESI Decision-Support Output</h1>
      <div style="color:#526070;">Backend-generated model result prepared for clinician review.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_backend_status()

result = (
    st.session_state.get("latest_prediction_response")
    or st.session_state.get("last_prediction_result")
)

if not result:
    st.info("No assessment result is available yet. Submit a new intake first.")
    st.caption("Open New Assessment from the sidebar, enter intake details, and run triage assessment.")
    if st.button("Go to New Assessment", type="primary"):
        try:
            st.switch_page("pages/02_New_Assessment.py")
        except Exception:
            st.stop()
    st.stop()

st.markdown(
    f'<div class="disclaimer">{escape(DISCLAIMER)}</div>',
    unsafe_allow_html=True,
)

if result.get("model_loaded") is False or result.get("is_placeholder") is True:
    st.markdown(
        '<div class="warning-box"><strong>Fallback response:</strong> Model inference '
        "is currently unavailable; displaying contract response only.</div>",
        unsafe_allow_html=True,
    )

render_main_result_card(result)

review_col, dashboard_col = st.columns([1, 1], gap="medium")
with review_col:
    if st.button("Proceed to Clinician Review", type="primary", width="stretch"):
        st.session_state["latest_prediction_response"] = result
        st.switch_page("pages/04_Clinician_Review.py")
with dashboard_col:
    if st.button("Go to Dashboard", width="stretch"):
        st.switch_page("pages/05_Dashboard.py")

_html_card(
    "Recommendation",
    result.get("recommendation") or "No recommendation returned.",
)

left, right = st.columns([1, 1], gap="large")
with left:
    render_probability_section(
        result.get("probabilities") or {},
        predicted_esi=result.get("predicted_esi"),
    )
with right:
    _render_safety_section(result)

st.markdown('<div class="section-title">Clinical Explanation</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="note-box">{escape(result.get("explanation") or "No explanation returned.")}</div>',
    unsafe_allow_html=True,
)

render_clinician_summary_card(result.get("clinician_summary"))

_render_model_details(result)

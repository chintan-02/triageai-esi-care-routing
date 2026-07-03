from pathlib import Path
import sys
from html import escape
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.components.layout import render_backend_status
from app.frontend.streamlit_app.services.api_client import submit_clinician_review
from app.frontend.streamlit_app.ui_theme import (
    apply_theme,
    render_disclaimer,
    render_empty_state,
    render_page_header,
    render_top_header,
)


DISCLAIMER = (
    "This tool is for clinical decision-support workflow testing only and does "
    "not replace clinician judgment."
)

DECISION_LABELS = {
    "accept": "Accept model recommendation",
    "override": "Override final ESI",
}


def _latest_prediction() -> dict[str, Any] | None:
    return st.session_state.get("latest_prediction_response") or st.session_state.get(
        "last_prediction_result"
    )


def _latest_intake() -> dict[str, Any]:
    return (
        st.session_state.get("latest_intake_payload")
        or st.session_state.get("last_intake_payload")
        or {}
    )


def _display_value(value: Any) -> str:
    if value is None or value == "":
        return "Not documented"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _confidence_label(value: Any) -> str:
    if value is None:
        return "Unavailable"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "Unavailable"


def _source_label(value: Any) -> str:
    if not value:
        return "Unavailable"
    return str(value).replace("_", " ").title()


def _triggered_safety_rules(result: dict[str, Any]) -> list[dict[str, Any]]:
    rules = result.get("safety_rules_triggered") or []
    return [rule for rule in rules if rule.get("triggered")]


def _render_header(result: dict[str, Any]) -> None:
    final_esi = _display_value(result.get("final_esi"))
    predicted_esi = _display_value(result.get("predicted_esi"))
    confidence = _confidence_label(result.get("confidence_score"))
    source = _source_label(result.get("final_source"))
    safety_label = "Triggered" if _triggered_safety_rules(result) else "Not triggered"
    model_badge = "Real model" if result.get("model_loaded") else "Fallback"

    st.markdown(
        '<div class="section-title">Review Snapshot</div>', unsafe_allow_html=True
    )
    cols = st.columns(6)
    cols[0].metric("Final ESI", final_esi)
    cols[1].metric("Predicted ESI", predicted_esi)
    cols[2].metric("Confidence", confidence)
    cols[3].metric("Final source", source)
    cols[4].metric("Safety rules", safety_label)
    cols[5].metric("Model status", model_badge)


def _render_intake_context(intake: dict[str, Any], result: dict[str, Any]) -> None:
    vitals = [
        ("Pain", intake.get("pain_score")),
        ("Temp C", intake.get("temperature_c")),
        ("HR", intake.get("heart_rate")),
        ("RR", intake.get("respiratory_rate")),
        ("BP", _format_bp(intake)),
        ("SpO2", intake.get("oxygen_saturation")),
    ]
    vitals_html = "".join(
        f'<span class="badge">{escape(label)}: {escape(_display_value(value))}</span>'
        for label, value in vitals
    )

    st.markdown(
        f"""
        <div class="clinical-card">
          <div class="eyebrow">Clinical Context</div>
          <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;margin-bottom:.9rem;">
            <div><strong>Chief complaint</strong><br>{escape(_display_value(intake.get("chief_complaint")))}</div>
            <div><strong>Age</strong><br>{escape(_display_value(intake.get("patient_age")))}</div>
            <div><strong>Gender/Sex</strong><br>{escape(_display_value(intake.get("sex")))}</div>
          </div>
          <div style="line-height:2;">{vitals_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">Recommendation</div>', unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="note-box">{escape(result.get("recommendation") or "No recommendation returned.")}</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown(
            '<div class="section-title">Clinical Explanation</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="note-box">{escape(result.get("explanation") or "No explanation returned.")}</div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            '<div class="section-title">Clinician Handoff Summary</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="note-box">{escape(result.get("clinician_summary") or "No summary returned.")}</div>',
            unsafe_allow_html=True,
        )


def _format_bp(intake: dict[str, Any]) -> str | None:
    systolic = intake.get("systolic_bp")
    diastolic = intake.get("diastolic_bp")
    if systolic is None and diastolic is None:
        return None
    return f"{_display_value(systolic)}/{_display_value(diastolic)}"


def _render_safety_notice(result: dict[str, Any]) -> None:
    triggered = _triggered_safety_rules(result)
    if not triggered:
        st.markdown(
            '<div class="safety-ok">No safety-rule escalation triggered for this result.</div>',
            unsafe_allow_html=True,
        )
        return

    items = "".join(
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
          <strong>Safety-rule review:</strong> escalation logic contributed to the final ESI.
          <ul style="margin:.55rem 0 0 1.1rem;padding:0;line-height:1.6;">{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_success_summary(response: dict[str, Any]) -> None:
    decision = _source_label(response.get("clinician_decision"))
    final_esi = _display_value(response.get("clinician_final_esi"))
    review_note = _display_value(response.get("review_note"))
    assessment_id = _display_value(response.get("assessment_id"))
    review_id = _display_value(response.get("review_id"))

    st.success("Clinician decision saved and audit trail updated.", icon="✅")
    st.markdown(
        f"""
        <div class="clinical-card">
          <div class="eyebrow">Saved Review</div>
          <div class="metric-row">
            <div class="mini-metric"><div class="metric-label">Decision</div><div class="metric-value">{escape(decision)}</div></div>
            <div class="mini-metric"><div class="metric-label">Clinician Final ESI</div><div class="metric-value">{escape(final_esi)}</div></div>
            <div class="mini-metric"><div class="metric-label">Status</div><div class="metric-value">{escape(_display_value(response.get("status")))}</div></div>
          </div>
          <div style="margin-top:.9rem;color:#1e3a52;line-height:1.6;">
            <strong>Assessment:</strong> {escape(assessment_id)}<br>
            <strong>Review:</strong> {escape(review_id)}<br>
            <strong>Note/reason:</strong> {escape(review_note)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Clinician Review | TriageAI", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown("### TriageAI / SympDirect")
    st.caption("ESI care-routing workflow")
    render_backend_status()

render_top_header("Clinician Review")
render_page_header(
    "Confirm or Override Final ESI",
    "Structured model output, clinician judgment, and audit trail in one workflow.",
    "Clinician Review",
)

result = _latest_prediction()
intake = _latest_intake()

if not result:
    render_empty_state(
        "No assessment selected for clinician review",
        "Complete a new assessment first, then return here to accept or override the final ESI.",
        "New Assessment",
    )
    if st.button("Go to New Assessment", type="primary"):
        st.switch_page("pages/02_New_Assessment.py")
    st.stop()

assessment_id = result.get("assessment_id")
if not assessment_id:
    st.error(
        "This result does not include an assessment ID, so it cannot be saved for review."
    )
    st.stop()

render_disclaimer(DISCLAIMER)

if result.get("is_placeholder"):
    st.markdown(
        '<div class="warning-box"><strong>Fallback output:</strong> model inference was not available for this assessment. '
        "Clinician review can still record the workflow decision, but the model result is placeholder-only.</div>",
        unsafe_allow_html=True,
    )

_render_header(result)
_render_safety_notice(result)
_render_intake_context(intake, result)

st.markdown(
    '<div class="section-title">Clinician Decision</div>', unsafe_allow_html=True
)
st.info(
    "The model provides an ESI 3/4/5 decision-support recommendation based on "
    "structured intake data. Clinicians can accept or override the recommendation "
    "when additional clinical context, safety concerns, or patient presentation "
    "justify a different final ESI. All overrides require a reason and are stored "
    "in the audit trail.",
    icon="ℹ️",
)
st.markdown(
    """
    <div class="note-box">
      <strong>Human-in-the-loop review:</strong>
      This workflow is designed as a human-in-the-loop safety feature: the model
      supports triage review, but the clinician makes the final decision.
    </div>
    """,
    unsafe_allow_html=True,
)

action = st.radio(
    "Decision",
    ["accept", "override"],
    format_func=lambda value: DECISION_LABELS[value],
    horizontal=True,
    key="clinician_review_decision",
)
model_final_esi = result.get("final_esi")

with st.form("clinician_review_form"):
    clinician_id = st.text_input(
        "Clinician ID / reviewer name",
        value=st.session_state.get("clinician_id", "clinician-reviewer"),
        help="Stored with the clinician review and audit log.",
    )

    clinician_final_esi = model_final_esi
    override_reason = None

    if action == "accept":
        st.info(
            f"Accepting the model/safety final ESI: ESI {_display_value(model_final_esi)}",
            icon="ℹ️",
        )
    else:
        st.warning("Overrides are stored in the audit trail.", icon="⚠️")
        st.caption(
            "Model prediction is limited to ESI 3-5. Clinician override supports "
            "ESI 1-5 so higher-risk cases can be escalated and documented."
        )
        override_options = [1, 2, 3, 4, 5]
        default_index = (
            override_options.index(model_final_esi)
            if model_final_esi in override_options
            else 2
        )
        clinician_final_esi = st.selectbox(
            "Clinician final ESI override",
            override_options,
            index=default_index,
            format_func=lambda value: f"ESI {value}",
        )
        if clinician_final_esi in [1, 2]:
            st.warning(
                "High-acuity override selected. Document the clinical reason for escalation.",
                icon="⚠️",
            )
        override_reason = st.text_area(
            "Reason for override",
            placeholder="Document the clinical reason for changing the final ESI.",
        )

    notes = st.text_area(
        "Clinical note / reviewer comment",
        placeholder="Optional reviewer context for the audit trail.",
    )

    render_disclaimer(DISCLAIMER)
    submitted = st.form_submit_button("Save Clinician Review", type="primary")

if submitted:
    st.session_state["clinician_id"] = clinician_id.strip() or "clinician-reviewer"
    if action == "override" and not (override_reason or "").strip():
        st.warning("Reason for override is required.", icon="⚠️")
        st.stop()

    payload = {
        "assessment_id": assessment_id,
        "clinician_id": st.session_state["clinician_id"],
        "action": action,
        "final_esi": clinician_final_esi,
        "notes": notes.strip() or None,
    }
    if action == "override":
        payload["override_reason"] = (override_reason or "").strip()

    with st.spinner("Saving clinician review..."):
        api_result = submit_clinician_review(payload)

    if api_result.get("ok"):
        response = api_result["data"]
        st.session_state["latest_clinician_review"] = response
        st.session_state["last_clinician_review_response"] = response
        _render_success_summary(response)
    else:
        st.error(api_result.get("message") or "Clinician review request failed.")
        if api_result.get("error_type") == "connection":
            st.code(api_result.get("start_command", ""), language="bash")
        details = api_result.get("data")
        if details:
            st.json(details)

nav_left, nav_right = st.columns([1, 1], gap="medium")
with nav_left:
    if st.button("Back to Result", width="stretch"):
        st.switch_page("pages/03_Result.py")
with nav_right:
    if st.button("Go to Dashboard", width="stretch"):
        st.switch_page("pages/05_Dashboard.py")

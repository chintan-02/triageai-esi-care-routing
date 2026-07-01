from pathlib import Path
import sys
from html import escape
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.assets.styles import apply_app_styles
from app.frontend.streamlit_app.components.layout import render_backend_status
from app.frontend.streamlit_app.components.probability_chart import (
    render_probability_section,
)
from app.frontend.streamlit_app.services.api_client import (
    download_report,
    generate_report,
    get_assessment_detail,
)


DETAIL_DISCLAIMER = (
    "This detail view is for clinical decision-support workflow review and audit "
    "visibility only. It is not a diagnosis or a substitute for clinician judgment."
)

MODEL_VS_CLINICIAN_NOTE = (
    "Model recommendation was based on structured intake data. The clinician final "
    "ESI may differ when additional clinical context, safety concerns, or patient "
    "presentation justify an override. Overrides require a reason and are stored "
    "in the audit trail."
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


def _label(value: Any) -> str:
    if not value:
        return "Pending"
    return str(value).replace("_", " ").title()


def _format_bp(detail: dict[str, Any]) -> str:
    systolic = detail.get("systolic_bp")
    diastolic = detail.get("diastolic_bp")
    if systolic is None and diastolic is None:
        return "Not documented"
    return f"{_display_value(systolic)}/{_display_value(diastolic)}"


def _candidate_assessment_id() -> str:
    latest_result = (
        st.session_state.get("latest_prediction_response")
        or st.session_state.get("last_prediction_result")
        or {}
    )
    return (
        st.session_state.get("selected_assessment_id")
        or st.session_state.get("assessment_detail_id")
        or latest_result.get("assessment_id")
        or ""
    )


def _prediction_for_session(detail: dict[str, Any]) -> dict[str, Any] | None:
    prediction = detail.get("latest_prediction")
    if not prediction:
        return None
    return {
        "request_id": detail.get("request_id"),
        "assessment_id": detail.get("assessment_id"),
        "acuity_scale": "ESI",
        "model_version": prediction.get("model_version"),
        "model_loaded": prediction.get("model_loaded"),
        "predicted_esi": prediction.get("predicted_esi"),
        "final_esi": prediction.get("final_esi"),
        "confidence_score": prediction.get("confidence_score"),
        "probabilities": prediction.get("probabilities") or {},
        "safety_rules_triggered": prediction.get("safety_rules_triggered") or [],
        "final_source": prediction.get("final_source"),
        "recommendation": prediction.get("recommendation"),
        "explanation": prediction.get("explanation"),
        "clinician_summary": prediction.get("clinician_summary"),
        "is_placeholder": prediction.get("is_placeholder"),
        "disclaimer": DETAIL_DISCLAIMER,
    }


def _render_snapshot(detail: dict[str, Any]) -> None:
    intake = detail.get("intake") or {}
    st.markdown('<div class="section-title">Patient / Intake Snapshot</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    cols[0].metric("Age", _display_value(intake.get("patient_age")))
    cols[1].metric("Gender/Sex", _display_value(intake.get("sex")))
    cols[2].metric("Status", _label(detail.get("status")))
    cols[3].metric("Created", _display_value(detail.get("created_at")))
    cols[4].metric("Assessment", _display_value(detail.get("assessment_id"))[:8])

    vitals = [
        ("Pain", detail.get("pain_score")),
        ("Temp C", detail.get("temperature_c")),
        ("HR", detail.get("heart_rate")),
        ("RR", detail.get("respiratory_rate")),
        ("BP", _format_bp(detail)),
        ("SpO2", detail.get("oxygen_saturation")),
        ("Arrival", detail.get("arrival_mode")),
        ("Consciousness", detail.get("consciousness_level")),
    ]
    vitals_html = "".join(
        f'<span class="badge">{escape(label)}: {escape(_display_value(value))}</span>'
        for label, value in vitals
    )
    st.markdown(
        f"""
        <div class="clinical-card">
          <div class="eyebrow">Chief Complaint</div>
          <div style="color:#0e1f35;font-weight:800;margin-bottom:.7rem;">
            {escape(_display_value(detail.get("chief_complaint")))}
          </div>
          <div style="line-height:2;">{vitals_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if detail.get("additional_context"):
        st.markdown(
            f'<div class="note-box">{escape(str(detail.get("additional_context")))}</div>',
            unsafe_allow_html=True,
        )


def _render_safety_rules(prediction: dict[str, Any]) -> None:
    rules = prediction.get("safety_rules_triggered") or []
    triggered = [rule for rule in rules if rule.get("triggered")]
    st.markdown('<div class="section-title">Safety Rules</div>', unsafe_allow_html=True)
    if not triggered:
        st.markdown(
            '<div class="safety-ok">No safety-rule escalation triggered.</div>',
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
          <strong>Safety-rule escalation visible.</strong>
          <ul style="margin:.55rem 0 0 1.1rem;padding:0;line-height:1.6;">{items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_prediction(detail: dict[str, Any]) -> None:
    prediction = detail.get("latest_prediction")
    st.markdown('<div class="section-title">Model Prediction</div>', unsafe_allow_html=True)
    if not prediction:
        st.info("No model prediction is stored for this assessment yet.")
        return

    cols = st.columns(5)
    cols[0].metric("Predicted ESI", _display_value(prediction.get("predicted_esi")))
    cols[1].metric("Model final ESI", _display_value(prediction.get("final_esi")))
    cols[2].metric("Confidence", _confidence_label(prediction.get("confidence_score")))
    cols[3].metric("Final source", _label(prediction.get("final_source")))
    cols[4].metric("Model loaded", _display_value(prediction.get("model_loaded")))

    left, right = st.columns([1, 1], gap="large")
    with left:
        render_probability_section(
            prediction.get("probabilities") or {},
            predicted_esi=prediction.get("predicted_esi"),
        )
    with right:
        _render_safety_rules(prediction)

    st.markdown('<div class="section-title">Recommendation</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="note-box">{escape(_display_value(prediction.get("recommendation")))}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-title">Clinical Explanation</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="note-box">{escape(_display_value(prediction.get("explanation")))}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-title">Clinician Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="note-box">{escape(_display_value(prediction.get("clinician_summary")))}</div>',
        unsafe_allow_html=True,
    )


def _render_review(detail: dict[str, Any]) -> None:
    review = detail.get("latest_clinician_review")
    prediction = detail.get("latest_prediction") or {}
    st.markdown('<div class="section-title">Clinician Review</div>', unsafe_allow_html=True)
    if not review:
        st.warning("This assessment is pending clinician review.", icon="⚠️")
        return

    cols = st.columns(5)
    cols[0].metric("Reviewed", _display_value(review.get("reviewed")))
    cols[1].metric("Decision", _label(review.get("clinician_decision")))
    cols[2].metric("Clinician final ESI", _display_value(review.get("clinician_final_esi")))
    cols[3].metric("Review ID", _display_value(review.get("review_id"))[:8])
    cols[4].metric("Reviewed at", _display_value(review.get("created_at")))

    model_final = prediction.get("final_esi")
    clinician_final = review.get("clinician_final_esi")
    if clinician_final is not None and clinician_final != model_final:
        st.markdown(
            f'<div class="warning-box">{escape(MODEL_VS_CLINICIAN_NOTE)}</div>',
            unsafe_allow_html=True,
        )

    note = review.get("override_reason") or review.get("review_note")
    st.markdown(
        f'<div class="note-box">{escape(_display_value(note))}</div>',
        unsafe_allow_html=True,
    )


def _render_audit(detail: dict[str, Any]) -> None:
    st.markdown('<div class="section-title">Audit Trail</div>', unsafe_allow_html=True)
    events = detail.get("audit_trail") or []
    if not events:
        st.info("No audit events are available for this assessment.")
        return
    rows = []
    for event in events:
        details = event.get("details")
        rows.append(
            {
                "Timestamp": _display_value(event.get("created_at")),
                "Action": _label(event.get("action")),
                "Actor": _display_value(event.get("actor_id")),
                "Details": _display_value(details),
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)


def _render_report_actions(assessment_id: str) -> None:
    st.markdown('<div class="section-title">PDF Report</div>', unsafe_allow_html=True)
    st.caption(
        "Generate a decision-support summary from persisted intake, model output, "
        "clinician review, and audit trail data."
    )

    report_key = f"generated_report_{assessment_id}"
    if st.button("Generate PDF Report", type="primary", width="stretch"):
        with st.spinner("Generating PDF report..."):
            report_result = generate_report(assessment_id)

        if not report_result.get("ok"):
            st.error(report_result.get("message") or "Report generation failed.")
            if report_result.get("error_type") == "connection":
                st.code(report_result.get("start_command", ""), language="bash")
            details = report_result.get("data")
            if details:
                st.json(details)
            st.session_state.pop(report_key, None)
            return

        report_data = report_result["data"]
        stored_report = {
            "metadata": report_data,
            "content": None,
            "download_error": None,
        }
        report_id = report_data.get("report_id")
        if report_id:
            download_result = download_report(report_id)
            if download_result.get("ok"):
                stored_report["content"] = download_result["data"]["content"]
            else:
                stored_report["download_error"] = (
                    download_result.get("message") or "Report download failed."
                )
        st.session_state[report_key] = stored_report

    stored_report = st.session_state.get(report_key)
    if not stored_report:
        return

    metadata = stored_report.get("metadata") or {}
    file_name = metadata.get("file_name") or "triageai_report.pdf"
    st.success(metadata.get("message") or "PDF report generated.")
    if stored_report.get("content"):
        st.download_button(
            "Download PDF Report",
            data=stored_report["content"],
            file_name=file_name,
            mime="application/pdf",
            width="stretch",
        )
    else:
        if stored_report.get("download_error"):
            st.warning(stored_report["download_error"], icon="⚠️")
        file_path = metadata.get("file_path")
        if file_path:
            st.info(f"Generated report saved at: {file_path}")


st.set_page_config(page_title="Assessment Detail | TriageAI", layout="wide")
apply_app_styles()

st.markdown(
    """
    <div class="clinical-header">
      <div class="eyebrow">Assessment Detail</div>
      <h1 style="margin:.1rem 0 .2rem 0;color:#0e1f35;">Persisted Assessment Review</h1>
      <div style="color:#526070;">Model output, clinician review, and audit context from the database.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

render_backend_status()

st.markdown(
    f'<div class="disclaimer">{escape(DETAIL_DISCLAIMER)}</div>',
    unsafe_allow_html=True,
)

default_assessment_id = _candidate_assessment_id()
assessment_id = st.text_input(
    "Assessment ID",
    value=default_assessment_id,
    placeholder="Paste or select an assessment ID",
)

if not assessment_id:
    st.info("No assessment selected.")
    st.caption("Open Dashboard to choose an assessment, or paste an assessment ID above.")
    if st.button("Back to Dashboard", type="primary"):
        st.switch_page("pages/05_Dashboard.py")
    st.stop()

with st.spinner("Loading assessment detail..."):
    api_result = get_assessment_detail(assessment_id.strip())

if not api_result.get("ok"):
    st.error(api_result.get("message") or "Assessment detail request failed.")
    if api_result.get("error_type") == "connection":
        st.code(api_result.get("start_command", ""), language="bash")
    details = api_result.get("data")
    if details:
        st.json(details)
    st.stop()

detail = api_result["data"]
st.session_state["selected_assessment_id"] = detail.get("assessment_id")
st.session_state["assessment_detail_id"] = detail.get("assessment_id")

_render_snapshot(detail)
_render_prediction(detail)
_render_review(detail)
_render_audit(detail)
_render_report_actions(detail.get("assessment_id") or assessment_id.strip())

nav_cols = st.columns([1, 1, 1], gap="medium")
with nav_cols[0]:
    if st.button("Back to Dashboard", width="stretch"):
        st.switch_page("pages/05_Dashboard.py")
with nav_cols[1]:
    latest_prediction = _prediction_for_session(detail)
    if detail.get("status") != "review_completed" and latest_prediction:
        if st.button("Go to Clinician Review", type="primary", width="stretch"):
            st.session_state["latest_prediction_response"] = latest_prediction
            st.session_state["latest_intake_payload"] = detail.get("intake") or {}
            st.switch_page("pages/04_Clinician_Review.py")
with nav_cols[2]:
    latest_result = st.session_state.get("latest_prediction_response")
    if latest_result:
        if st.button("Go to Result", width="stretch"):
            st.switch_page("pages/03_Result.py")

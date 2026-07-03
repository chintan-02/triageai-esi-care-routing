from pathlib import Path
import sys
from html import escape
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.frontend.streamlit_app.components.layout import render_backend_status
from app.frontend.streamlit_app.services.api_client import get_dashboard_summary
from app.frontend.streamlit_app.ui_theme import (
    apply_theme,
    render_disclaimer,
    render_empty_state,
    render_page_header,
    render_top_header,
)


DASHBOARD_DISCLAIMER = (
    "This dashboard is for clinical decision-support workflow review and audit "
    "visibility only."
)


def _short_id(value: str | None) -> str:
    if not value:
        return "Unavailable"
    return value[:8]


def _display_value(value: Any) -> str:
    if value is None or value == "":
        return "Not documented"
    return str(value)


def _percent(value: Any) -> str:
    if value is None:
        return "Unavailable"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "Unavailable"


def _source_label(value: Any) -> str:
    if not value:
        return "Pending"
    return str(value).replace("_", " ").title()


def _effective_esi(row: dict[str, Any]) -> int | None:
    return (
        row.get("clinician_final_esi")
        or row.get("final_esi")
        or row.get("model_final_esi")
    )


def _filter_rows(
    rows: list[dict[str, Any]],
    status_filter: str,
    esi_filter: str,
    decision_filter: str,
    search_text: str,
) -> list[dict[str, Any]]:
    normalized_search = search_text.strip().lower()
    filtered = []
    for row in rows:
        if status_filter != "All" and row.get("status") != status_filter:
            continue
        if (
            decision_filter != "All"
            and row.get("clinician_decision") != decision_filter
        ):
            continue
        if esi_filter != "All":
            try:
                selected_esi = int(esi_filter.replace("ESI ", ""))
            except ValueError:
                selected_esi = None
            if _effective_esi(row) != selected_esi:
                continue
        if normalized_search:
            haystack = " ".join(
                [
                    str(row.get("assessment_id") or ""),
                    str(row.get("chief_complaint") or ""),
                ]
            ).lower()
            if normalized_search not in haystack:
                continue
        filtered.append(row)
    return filtered


def _table_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table_data = []
    for row in rows:
        table_data.append(
            {
                "Created": _display_value(row.get("created_at")),
                "Assessment": _short_id(row.get("assessment_id")),
                "Age": row.get("patient_age"),
                "Gender": _display_value(row.get("sex")),
                "Chief complaint": _display_value(row.get("chief_complaint")),
                "Predicted ESI": row.get("predicted_esi"),
                "Model final ESI": row.get("model_final_esi"),
                "Clinician final ESI": row.get("clinician_final_esi"),
                "Status": _source_label(row.get("status")),
                "Clinician decision": _source_label(row.get("clinician_decision")),
                "Final source": _source_label(row.get("final_source")),
                "Confidence": _percent(row.get("confidence_score")),
            }
        )
    return table_data


def _render_esi_distribution(distribution: dict[str, int]) -> None:
    st.markdown(
        '<div class="section-title">ESI Distribution</div>', unsafe_allow_html=True
    )
    st.caption(
        "The deployed model predicts ESI 3-5. Safety rules and clinician override "
        "can produce final ESI 1-5 for workflow review."
    )
    total = sum(distribution.values())
    if total == 0:
        st.info("No final ESI values are available yet.")
        return

    for esi_level in [1, 2, 3, 4, 5]:
        count = int(distribution.get(str(esi_level), 0))
        ratio = count / total if total else 0
        label = f"ESI {esi_level}"
        if esi_level == 2:
            label = "ESI 2 safety/clinician escalation"
        elif esi_level == 1:
            label = "ESI 1 clinician escalation"
        st.write(f"**{label}:** {count}")
        st.progress(ratio)


st.set_page_config(page_title="Dashboard | TriageAI", layout="wide")
apply_theme()

with st.sidebar:
    st.markdown("### TriageAI / SympDirect")
    st.caption("ESI care-routing workflow")
    render_backend_status()

render_top_header("Dashboard")
render_page_header(
    "Assessment History",
    "Workflow view for ESI output, review status, and audit readiness.",
    "Dashboard",
)

render_disclaimer(DASHBOARD_DISCLAIMER)

with st.spinner("Loading dashboard summary..."):
    api_result = get_dashboard_summary()

if not api_result.get("ok"):
    st.error(api_result.get("message") or "Dashboard request failed.")
    if api_result.get("error_type") == "connection":
        st.code(api_result.get("start_command", ""), language="bash")
    details = api_result.get("data")
    if details:
        st.json(details)
    st.stop()

summary = api_result["data"]
rows = summary.get("recent_assessments") or []

metric_cols = st.columns(6)
metric_cols[0].metric("Total assessments", summary.get("total_assessments", 0))
metric_cols[1].metric(
    "Model predictions",
    summary.get("model_predictions_generated", 0),
)
metric_cols[2].metric(
    "Reviewed",
    summary.get("reviewed_assessments", summary.get("completed_reviews", 0)),
)
metric_cols[3].metric("Pending review", summary.get("pending_reviews", 0))
metric_cols[4].metric("Overrides", summary.get("override_count", 0))
metric_cols[5].metric(
    "Common final ESI",
    _display_value(summary.get("most_common_final_esi")),
)

left, right = st.columns([0.8, 1.2], gap="large")
with left:
    _render_esi_distribution(summary.get("esi_distribution") or {})
with right:
    st.markdown(
        '<div class="section-title">Recent Assessments</div>', unsafe_allow_html=True
    )
    if not rows:
        render_empty_state(
            "No assessments have been created yet",
            "Start with New Assessment, then return here to review workflow history.",
            "New Assessment",
        )
        if st.button("Go to New Assessment", type="primary"):
            st.switch_page("pages/02_New_Assessment.py")
        st.stop()

    filter_cols = st.columns([1, 1, 1, 1.4], gap="small")
    status_options = ["All"] + sorted(
        {str(row.get("status")) for row in rows if row.get("status")}
    )
    decision_options = ["All"] + sorted(
        {
            str(row.get("clinician_decision"))
            for row in rows
            if row.get("clinician_decision")
        }
    )
    status_filter = filter_cols[0].selectbox("Status", status_options)
    esi_filter = filter_cols[1].selectbox(
        "Final ESI",
        ["All", "ESI 1", "ESI 2", "ESI 3", "ESI 4", "ESI 5"],
    )
    decision_filter = filter_cols[2].selectbox("Decision", decision_options)
    search_text = filter_cols[3].text_input(
        "Search",
        placeholder="Chief complaint or assessment ID",
    )

    filtered_rows = _filter_rows(
        rows,
        status_filter=status_filter,
        esi_filter=esi_filter,
        decision_filter=decision_filter,
        search_text=search_text,
    )

    if not filtered_rows:
        st.warning("No assessments match the current filters.", icon="⚠️")
    else:
        st.dataframe(
            _table_rows(filtered_rows),
            width="stretch",
            hide_index=True,
        )

    assessment_options = {
        f"{_short_id(row.get('assessment_id'))} | {_display_value(row.get('chief_complaint'))}": row.get(
            "assessment_id"
        )
        for row in filtered_rows
    }
    if assessment_options:
        selected_label = st.selectbox(
            "Assessment to open",
            list(assessment_options.keys()),
        )
        selected_assessment_id = assessment_options[selected_label]
        action_cols = st.columns([1, 1], gap="medium")
        with action_cols[0]:
            if st.button("Load Assessment Detail", type="primary", width="stretch"):
                st.session_state["selected_assessment_id"] = selected_assessment_id
                st.session_state["assessment_detail_id"] = selected_assessment_id
                st.switch_page("pages/06_Assessment_Detail.py")
        with action_cols[1]:
            selected_row = next(
                row
                for row in filtered_rows
                if row.get("assessment_id") == selected_assessment_id
            )
            if selected_row.get("status") != "review_completed":
                if st.button("Open Detail for Review", width="stretch"):
                    st.session_state["selected_assessment_id"] = selected_assessment_id
                    st.session_state["assessment_detail_id"] = selected_assessment_id
                    st.switch_page("pages/06_Assessment_Detail.py")

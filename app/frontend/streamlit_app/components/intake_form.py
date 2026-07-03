"""Structured intake form for backend prediction."""

from __future__ import annotations

from html import escape

import streamlit as st

from app.frontend.streamlit_app.ui_theme import render_section_label


ARRIVAL_MODES = [
    "Walk-in",
    "Car",
    "Ambulance",
    "Wheelchair",
    "Public Transportation",
    "Police",
    "Other",
]


def _optional_intake_context(flags: dict[str, bool], free_text: str) -> str | None:
    phrases = [label for label, selected in flags.items() if selected]
    if free_text:
        phrases.append(free_text.strip())
    return "; ".join(phrases) if phrases else None


def _vital_status(label: str, value: float) -> tuple[str, str]:
    if label == "Heart rate":
        if value < 40 or value > 130:
            return "red", "Escalation risk"
        if value < 60 or value > 100:
            return "amber", "Abnormal"
    if label == "Respiratory rate":
        if value < 8 or value > 30:
            return "red", "Escalation risk"
        if value < 12 or value > 20:
            return "amber", "Abnormal"
    if label == "Oxygen saturation":
        if value < 92:
            return "red", "Escalation risk"
        if value < 95:
            return "amber", "Abnormal"
    if label == "Systolic BP":
        if value < 80 or value > 200:
            return "red", "Escalation risk"
        if value < 90 or value > 140:
            return "amber", "Abnormal"
    if label == "Diastolic BP":
        if value < 45 or value > 120:
            return "red", "Escalation risk"
        if value < 60 or value > 90:
            return "amber", "Abnormal"
    if label == "Temperature":
        if value < 35.0 or value >= 39.5:
            return "red", "Escalation risk"
        if value < 36.0 or value > 38.0:
            return "amber", "Abnormal"
    if label == "Pain score":
        if value >= 8:
            return "red", "Severe"
        if value >= 4:
            return "amber", "Moderate"
        return "green", "Low"
    return "green", "Normal"


def _format_vital_value(value: int | float) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.1f}"
    return str(int(value))


def _render_vital_card(
    slot,
    *,
    label: str,
    current: int | float,
    min_value: int | float,
    max_value: int | float,
    unit: str,
    helper: str,
) -> None:
    tone, status = _vital_status(label, float(current))
    display_value = _format_vital_value(current)
    slot.markdown(
        f"""
        <div class="ta-vital-card {tone}">
            <div class="ta-vital-head">
                <div class="ta-vital-label">{escape(label)}</div>
                <div class="ta-vital-status">{escape(status)}</div>
            </div>
            <div class="ta-vital-value">{escape(display_value)}<span class="ta-vital-unit">{escape(unit)}</span></div>
            <div class="ta-vital-helper">{escape(helper)}</div>
            <div class="ta-vital-helper">Range: {escape(str(min_value))} to {escape(str(max_value))} {escape(unit)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_vital_slider(
    label: str,
    *,
    value: int | float,
    min_value: int | float,
    max_value: int | float,
    step: int | float,
    unit: str,
    helper: str,
    key: str,
) -> int | float:
    with st.container(border=True):
        card_slot = st.empty()
        slider_kwargs = {
            "label": label,
            "min_value": min_value,
            "max_value": max_value,
            "step": step,
            "key": key,
            "label_visibility": "collapsed",
        }
        if key not in st.session_state:
            slider_kwargs["value"] = value
        current = st.slider(**slider_kwargs)
        _render_vital_card(
            card_slot,
            label=label,
            current=current,
            min_value=min_value,
            max_value=max_value,
            unit=unit,
            helper=helper,
        )
    return current


def render_intake_form() -> tuple[bool, dict]:
    """Render the intake form and return submitted state plus backend payload."""
    st.caption("Enter intake information available before clinician review.")

    patient_card = st.container(border=True)
    with patient_card:
        render_section_label("Patient Information")
        patient_cols = st.columns([1, 1, 1], gap="medium")
        with patient_cols[0]:
            patient_age = st.number_input("Age", min_value=0, max_value=120, value=45)
        with patient_cols[1]:
            gender = st.selectbox("Gender", ["", "Female", "Male", "Other"], index=0)
        with patient_cols[2]:
            arrival_mode = st.selectbox("Arrival mode", ARRIVAL_MODES, index=0)

    complaint_card = st.container(border=True)
    with complaint_card:
        render_section_label("Chief Complaint")
        chief_complaint = st.text_area(
            "Chief complaint",
            value="Chest discomfort",
            height=90,
        )
        symptom_duration = st.text_input("Symptom duration", value="")

    vitals_card = st.container(border=True)
    with vitals_card:
        render_section_label("Vital Signs")
        vital_cols = st.columns(2, gap="medium")
        with vital_cols[0]:
            heart_rate = _render_vital_slider(
                "Heart rate",
                value=88,
                min_value=0,
                max_value=260,
                step=1,
                unit="bpm",
                helper="Reference: 60-100 bpm",
                key="vital_heart_rate",
            )
            oxygen_saturation = _render_vital_slider(
                "Oxygen saturation",
                value=98.0,
                min_value=0.0,
                max_value=100.0,
                step=0.5,
                unit="%",
                helper="Reference: 95-100%",
                key="vital_oxygen_saturation",
            )
            diastolic_bp = _render_vital_slider(
                "Diastolic BP",
                value=82,
                min_value=0,
                max_value=220,
                step=1,
                unit="mmHg",
                helper="Reference: 60-90 mmHg",
                key="vital_diastolic_bp",
            )
            pain_score = _render_vital_slider(
                "Pain score",
                value=0,
                min_value=0,
                max_value=10,
                step=1,
                unit="/10",
                helper="Severe pain is 8 or higher",
                key="vital_pain_score",
            )
        with vital_cols[1]:
            respiratory_rate = _render_vital_slider(
                "Respiratory rate",
                value=18,
                min_value=0,
                max_value=80,
                step=1,
                unit="/min",
                helper="Reference: 12-20/min",
                key="vital_respiratory_rate",
            )
            systolic_bp = _render_vital_slider(
                "Systolic BP",
                value=128,
                min_value=0,
                max_value=320,
                step=1,
                unit="mmHg",
                helper="Reference: 90-140 mmHg",
                key="vital_systolic_bp",
            )
            temperature_c = _render_vital_slider(
                "Temperature",
                value=36.8,
                min_value=25.0,
                max_value=45.0,
                step=0.1,
                unit="C",
                helper="Reference: 36.0-38.0 C",
                key="vital_temperature_c",
            )

    safety_card = st.container(border=True)
    with safety_card:
        render_section_label("Safety Context")
        flag_cols = st.columns(3, gap="medium")
        with flag_cols[0]:
            pregnancy = st.checkbox("Pregnancy")
            severe_pain = st.checkbox("Severe pain")
            altered_mental_status = st.checkbox("Altered mental status")
        with flag_cols[1]:
            chest_pain = st.checkbox("Chest pain")
            shortness_of_breath = st.checkbox("Shortness of breath")
            active_bleeding = st.checkbox("Active bleeding")
        with flag_cols[2]:
            stroke_symptoms = st.checkbox("Stroke-like symptoms")
            suicidal_ideation = st.checkbox("Suicidal ideation")
            o2_device = st.checkbox("Supplemental oxygen device")

        free_text = st.text_area("Additional context", height=80)

    nav_left, nav_center, nav_right = st.columns([1, 1, 1], gap="medium")
    with nav_left:
        back_home = st.button("Back to Home", width="stretch")
    with nav_center:
        submitted = st.button("Run ESI Assessment", type="primary", width="stretch")
    with nav_right:
        open_dashboard = st.button("Open Dashboard", width="stretch")

    if back_home:
        st.switch_page("Home.py")
    if open_dashboard:
        st.switch_page("pages/05_Dashboard.py")

    flags = {
        "severe pain": severe_pain,
        "altered mental status": altered_mental_status,
        "chest pain": chest_pain,
        "shortness of breath": shortness_of_breath,
        "stroke-like symptoms": stroke_symptoms,
        "suicidal ideation": suicidal_ideation,
        "active bleeding": active_bleeding,
        "supplemental oxygen device": o2_device,
    }

    payload = {
        "patient_age": int(patient_age),
        "sex": gender.lower() if gender else None,
        "chief_complaint": chief_complaint.strip(),
        "symptom_duration": symptom_duration.strip() or None,
        "pain_score": int(pain_score),
        "heart_rate": int(heart_rate),
        "respiratory_rate": int(respiratory_rate),
        "systolic_bp": int(systolic_bp),
        "diastolic_bp": int(diastolic_bp),
        "oxygen_saturation": float(oxygen_saturation),
        "temperature_c": float(temperature_c),
        "arrival_mode": arrival_mode,
        "pregnancy": pregnancy,
        "consciousness_level": "altered" if altered_mental_status else None,
        "additional_context": _optional_intake_context(flags, free_text),
    }

    return submitted, payload

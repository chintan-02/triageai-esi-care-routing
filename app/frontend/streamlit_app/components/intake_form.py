"""Structured intake form for backend prediction."""

from __future__ import annotations

import streamlit as st


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


def render_intake_form() -> tuple[bool, dict]:
    """Render the intake form and return submitted state plus backend payload."""
    with st.form("triage_intake_form"):
        st.subheader("Patient Intake")
        st.caption("Enter intake information available before clinician review.")

        left, right = st.columns(2)
        with left:
            patient_age = st.number_input("Age", min_value=0, max_value=120, value=45)
            gender = st.selectbox("Gender", ["", "Female", "Male", "Other"], index=0)
            chief_complaint = st.text_area(
                "Chief complaint",
                value="Chest discomfort",
                height=90,
            )
            symptom_duration = st.text_input("Symptom duration", value="")
            arrival_mode = st.selectbox("Arrival mode", ARRIVAL_MODES, index=0)

        with right:
            heart_rate = st.number_input("Heart rate", min_value=0, max_value=260, value=88)
            respiratory_rate = st.number_input(
                "Respiratory rate",
                min_value=0,
                max_value=80,
                value=18,
            )
            systolic_bp = st.number_input("Systolic BP", min_value=0, max_value=320, value=128)
            diastolic_bp = st.number_input("Diastolic BP", min_value=0, max_value=220, value=82)
            oxygen_saturation = st.number_input(
                "Oxygen saturation (%)",
                min_value=0.0,
                max_value=100.0,
                value=98.0,
                step=0.1,
            )
            temperature_c = st.number_input(
                "Temperature (C)",
                min_value=25.0,
                max_value=45.0,
                value=36.8,
                step=0.1,
            )

        st.markdown("#### Safety Context")
        flag_cols = st.columns(3)
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
        pain_score = st.slider("Pain score", min_value=0, max_value=10, value=0)

        submitted = st.form_submit_button("Run Triage Assessment", type="primary")

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

"""Clinician summary placeholder service."""

from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import SafetyRuleResult
from app.backend.services.text_formatting import clean_human_readable_text


def build_placeholder_clinician_summary() -> str:
    return (
        "Clinician summary generation is not connected yet. This is a "
        "contract-only placeholder response."
    )


def build_clinician_summary(
    intake: PatientIntakeRequest,
    predicted_esi: int | None,
    final_esi: int | None,
    safety_rules: list[SafetyRuleResult],
    probabilities: dict[str, float],
) -> str:
    demographics = f"{intake.patient_age}-year-old"
    if intake.sex:
        demographics = f"{demographics} {intake.sex}"

    vitals = []
    if intake.temperature_c is not None:
        vitals.append(f"temp {intake.temperature_c}C")
    if intake.heart_rate is not None:
        vitals.append(f"HR {intake.heart_rate}")
    if intake.respiratory_rate is not None:
        vitals.append(f"RR {intake.respiratory_rate}")
    if intake.systolic_bp is not None or intake.diastolic_bp is not None:
        vitals.append(f"BP {intake.systolic_bp}/{intake.diastolic_bp}")
    if intake.oxygen_saturation is not None:
        vitals.append(f"SpO2 {intake.oxygen_saturation}%")

    triggered = [rule.message for rule in safety_rules if rule.triggered]
    confidence = ""
    if predicted_esi is not None:
        confidence = f"Model predicted ESI {predicted_esi}"
        predicted_key = f"ESI_{predicted_esi}"
        if predicted_key in probabilities:
            confidence += f" ({probabilities[predicted_key]:.2f})."
        else:
            confidence += "."

    summary_parts = [
        f"{demographics} presenting with {intake.chief_complaint}.",
    ]
    if intake.symptom_duration:
        summary_parts.append(f"Duration: {intake.symptom_duration}.")
    if intake.pain_score is not None:
        summary_parts.append(f"Pain score: {intake.pain_score}/10.")
    if vitals:
        summary_parts.append(f"Key vitals: {', '.join(vitals)}.")
    if confidence:
        summary_parts.append(confidence)
    if triggered and final_esi is not None:
        summary_parts.append(f"Safety escalation to ESI {final_esi}: {'; '.join(triggered)}")
    elif final_esi is not None:
        summary_parts.append(f"Final ESI {final_esi}; clinician review recommended.")

    return clean_human_readable_text(" ".join(summary_parts)) or ""

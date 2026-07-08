"""Helpers for audit log payloads."""

from typing import Any

from app.backend.services.text_formatting import clean_human_readable_text


def build_audit_details(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    final_esi = payload.get("final_esi") or payload.get("clinician_final_esi")
    note = clean_human_readable_text(payload.get("notes") or payload.get("review_note"))
    override_reason = clean_human_readable_text(payload.get("override_reason"))
    clinician_id = payload.get("clinician_id") or payload.get("reviewer_name")

    if action == "accept":
        message = "Clinician accepted final routing decision."
    elif action == "override":
        message = "Clinician overrode final routing decision."
    else:
        message = "Clinician marked assessment for additional review."

    return {
        "action": action,
        "clinician_decision": action,
        "clinician_id": clinician_id,
        "clinician_final_esi": final_esi,
        "override_reason": override_reason,
        "review_note": note,
        "message": clean_human_readable_text(message),
    }

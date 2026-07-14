from typing import Any

from fastapi.testclient import TestClient

from app.backend.api.main import app


client = TestClient(app)


def valid_intake_payload() -> dict[str, Any]:
    return {
        "patient_age": 62,
        "chief_complaint": "Chest pain",
        "symptom_duration": "2 hours",
        "heart_rate": 118,
        "systolic_bp": 92,
        "diastolic_bp": 60,
        "oxygen_saturation": 91,
    }


def reviewed_nlp_audit() -> dict[str, Any]:
    return {
        "reviewed": True,
        "source": "clinical_intake_nlp",
        "extracted_fields": {
            "age": 62,
            "chief_complaint": "chest pain",
            "symptoms": ["chest pain", "shortness of breath"],
            "vitals": {"hr": 118, "sbp": 92, "predicted_esi": 1},
            "diagnosis": "must not be stored",
            "treatment": "must not be stored",
            "clinical_note": "must not be stored",
        },
        "safety_cues": ["chest pain", "low oxygen"],
        "missing_fields": ["respiratory rate"],
        "evidence": [
            {"field": "age", "value": 62, "text": "62-year-old"},
            {"field": "triage_vital_hr", "value": 118, "text": "HR 118"},
        ],
        "disclaimer": (
            "Decision support only. Extracted fields require clinician review "
            "before prediction."
        ),
        "note_text": "must not be stored",
        "raw_note": "must not be stored",
        "transcript": "must not be stored",
        "treatment_recommendation": "must not be stored",
        "final_esi": 1,
    }


def _contains_unsafe_key(value: Any) -> bool:
    unsafe_keys = {
        "diagnosis",
        "treatment",
        "treatment_recommendation",
        "predicted_esi",
        "final_esi",
        "clinical_note",
        "note_text",
        "raw_note",
        "transcript",
    }
    if isinstance(value, dict):
        return any(
            key in unsafe_keys or _contains_unsafe_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_unsafe_key(item) for item in value)
    return False


def test_predict_without_nlp_audit_has_no_review_event() -> None:
    response = client.post("/predict", json=valid_intake_payload())

    assert response.status_code == 200
    assessment_id = response.json()["assessment_id"]

    audit_response = client.get(f"/assessments/{assessment_id}/audit")
    assert audit_response.status_code == 200
    actions = [event["action"] for event in audit_response.json()["events"]]
    assert "nlp_extraction_reviewed" not in actions


def test_reviewed_nlp_audit_is_in_audit_endpoint_and_assessment_detail() -> None:
    payload = valid_intake_payload()
    payload["nlp_extraction_audit"] = reviewed_nlp_audit()

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assessment_id = response.json()["assessment_id"]

    audit_response = client.get(f"/assessments/{assessment_id}/audit")
    assert audit_response.status_code == 200
    review_event = next(
        event
        for event in audit_response.json()["events"]
        if event["action"] == "nlp_extraction_reviewed"
    )
    assert review_event["actor_id"] == "clinical_nlp_review_ui"
    assert review_event["details"] == {
        "reviewed": True,
        "source": "clinical_intake_nlp",
        "extracted_fields": {
            "age": 62,
            "chief_complaint": "chest pain",
            "symptoms": ["chest pain", "shortness of breath"],
            "vitals": {"hr": 118, "sbp": 92},
        },
        "safety_cues": ["chest pain", "low oxygen"],
        "missing_fields": ["respiratory rate"],
        "evidence": [
            {"field": "age", "value": 62, "text": "62-year-old"},
            {"field": "triage_vital_hr", "value": 118, "text": "HR 118"},
        ],
        "disclaimer": (
            "Decision support only. Extracted fields require clinician review "
            "before prediction."
        ),
        "message": "Clinical NLP extraction reviewed before ESI decision support.",
    }
    assert _contains_unsafe_key(review_event["details"]) is False

    detail_response = client.get(f"/assessments/{assessment_id}")
    assert detail_response.status_code == 200
    detail_events = detail_response.json()["audit_trail"]
    detail_review_event = next(
        event for event in detail_events if event["action"] == "nlp_extraction_reviewed"
    )
    assert detail_review_event["details"] == review_event["details"]
    assert _contains_unsafe_key(detail_review_event["details"]) is False


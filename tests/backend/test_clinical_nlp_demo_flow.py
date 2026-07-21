import json
from io import BytesIO

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.backend.api.main import app


client = TestClient(app)

DEMO_NOTE = (
    "62-year-old male with chest pain and shortness of breath. "
    "HR 118, BP 92/60, O2 91%, temp 38.2. Patient looks pale and dizzy."
)


def _pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_clinical_nlp_demo_flow_reaches_audit_detail_and_pdf() -> None:
    extraction_response = client.post(
        "/nlp/extract-intake",
        json={"note_text": DEMO_NOTE},
    )

    assert extraction_response.status_code == 200
    extraction = extraction_response.json()
    assert extraction["age"] == 62
    assert extraction["gender"] == "Male"
    assert extraction["chief_complaint"] == "chest pain"
    assert "chest pain" in extraction["symptoms"]
    assert extraction["vitals"] == {
        "hr": 118,
        "sbp": 92,
        "dbp": 60,
        "rr": None,
        "o2": 91,
        "temp": 38.2,
    }
    assert "low oxygen" in extraction["safety_cues"]
    assert "respiratory rate" in extraction["missing_fields"]

    prediction_payload = {
        "patient_age": extraction["age"],
        "sex": extraction["gender"].lower(),
        "chief_complaint": extraction["chief_complaint"],
        "symptom_duration": "Not stated",
        "heart_rate": extraction["vitals"]["hr"],
        "respiratory_rate": extraction["vitals"]["rr"],
        "systolic_bp": extraction["vitals"]["sbp"],
        "diastolic_bp": extraction["vitals"]["dbp"],
        "temperature_c": extraction["vitals"]["temp"],
        "oxygen_saturation": extraction["vitals"]["o2"],
        "nlp_extraction_audit": {
            "reviewed": True,
            "source": "clinical_intake_nlp",
            "extracted_fields": {
                "age": extraction["age"],
                "gender": extraction["gender"],
                "chief_complaint": extraction["chief_complaint"],
                "symptoms": extraction["symptoms"],
                "vitals": extraction["vitals"],
            },
            "safety_cues": extraction["safety_cues"],
            "missing_fields": extraction["missing_fields"],
            "evidence": extraction["evidence"],
            "disclaimer": extraction["disclaimer"],
        },
    }

    prediction_response = client.post("/predict", json=prediction_payload)

    assert prediction_response.status_code == 200
    assessment_id = prediction_response.json()["assessment_id"]
    assert assessment_id

    audit_response = client.get(f"/assessments/{assessment_id}/audit")
    assert audit_response.status_code == 200
    nlp_audit_event = next(
        event
        for event in audit_response.json()["events"]
        if event["action"] == "nlp_extraction_reviewed"
    )
    audit_details_text = json.dumps(nlp_audit_event["details"]).lower()
    assert DEMO_NOTE.lower() not in audit_details_text
    assert "diagnosis" not in audit_details_text
    assert "treatment_recommendation" not in audit_details_text
    assert "ai confirmed esi" not in audit_details_text

    detail_response = client.get(f"/assessments/{assessment_id}")
    assert detail_response.status_code == 200
    assert any(
        event["action"] == "nlp_extraction_reviewed"
        for event in detail_response.json()["audit_trail"]
    )

    pdf_response = client.get(f"/assessments/{assessment_id}/report/pdf")

    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    pdf_text = _pdf_text(pdf_response.content)
    normalized_pdf_text = pdf_text.lower()
    assert "Clinical NLP Review Evidence" in pdf_text
    assert "Reviewed before prediction" in pdf_text
    assert "62-year-old" in pdf_text
    assert "low oxygen" in normalized_pdf_text
    assert "Decision-support audit context only" in pdf_text
    assert DEMO_NOTE.lower() not in normalized_pdf_text
    assert "not diagnosis" in normalized_pdf_text
    assert "not a treatment recommendation" in normalized_pdf_text
    assert "not a substitute for emergency protocols" in normalized_pdf_text
    assert "treatment_recommendation" not in normalized_pdf_text
    assert "ai confirmed esi" not in normalized_pdf_text

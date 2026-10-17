from io import BytesIO
from pathlib import Path
import re

from fastapi.testclient import TestClient
from pypdf import PdfReader

from app.backend.api.main import app
from app.backend.services.pdf_service import _details_text, _safety_rule_label


client = TestClient(app)


def valid_intake_payload() -> dict[str, object]:
    return {
        "patient_age": 42,
        "chief_complaint": "Chest discomfort",
        "pain_score": 6,
        "oxygen_saturation": 98.0,
    }


def reviewed_nlp_intake_payload() -> dict[str, object]:
    return {
        "patient_age": 62,
        "chief_complaint": "Chest pain",
        "symptom_duration": "2 hours",
        "additional_context": "do not store full raw note",
        "heart_rate": 118,
        "systolic_bp": 92,
        "diastolic_bp": 60,
        "oxygen_saturation": 91,
        "nlp_extraction_audit": {
            "reviewed": True,
            "source": "clinical_intake_nlp",
            "extracted_fields": {
                "age": 62,
                "gender": "Male",
                "chief_complaint": "chest pain",
                "symptoms": ["chest pain", "shortness of breath"],
                "vitals": {"hr": 118, "sbp": 92, "dbp": 60, "o2": 91},
                "clinical_note": "do not store full raw note",
                "diagnosis": "unsafe diagnosis payload",
                "treatment_recommendation": "unsafe treatment payload",
                "predicted_esi": 1,
                "final_esi": 1,
            },
            "safety_cues": ["low oxygen", "low blood pressure"],
            "missing_fields": ["respiratory rate"],
            "evidence": [
                {"field": "age", "value": 62, "text": "62-year-old"},
                {"field": "triage_vital_hr", "value": 118, "text": "HR 118"},
            ],
            "disclaimer": (
                "Decision support only. Extracted fields require clinician review "
                "before prediction."
            ),
            "note_text": "do not store full raw note",
            "raw_note": "do not store full raw note",
            "transcript": "do not store full raw note",
        },
    }


def pdf_text(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def test_generate_report_creates_pdf_file_for_prediction() -> None:
    predict_response = client.post("/predict", json=valid_intake_payload())
    assessment_id = predict_response.json()["assessment_id"]

    response = client.post(
        "/reports/generate",
        json={"assessment_id": assessment_id, "include_audit": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["report_id"]
    assert body["assessment_id"] == assessment_id
    assert body["report_status"] == "generated"
    assert body["status"] == "generated"
    assert body["download_url"] == f"/reports/{body['report_id']}/download"
    assert body["created_at"]
    assert body["is_placeholder"] is False
    assert body["file_name"].endswith(".pdf")
    file_path = Path(body["file_path"])
    assert file_path.exists()
    assert file_path.stat().st_size > 0

    detail_response = client.get(f"/assessments/{assessment_id}")
    audit_actions = [event["action"] for event in detail_response.json()["audit_trail"]]
    assert "report_generated" in audit_actions


def test_generate_report_does_not_require_clinician_review() -> None:
    create_response = client.post("/assessments", json=valid_intake_payload())
    assessment_id = create_response.json()["assessment_id"]

    response = client.post(
        "/reports/generate",
        json={"assessment_id": assessment_id, "include_audit": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_placeholder"] is False
    assert Path(body["file_path"]).exists()


def test_download_generated_report_returns_pdf() -> None:
    predict_response = client.post("/predict", json=valid_intake_payload())
    assessment_id = predict_response.json()["assessment_id"]
    client.post(
        "/clinician-review",
        json={
            "assessment_id": assessment_id,
            "clinician_id": "clinician-123",
            "action": "accept",
            "final_esi": predict_response.json()["final_esi"],
            "notes": (
                "Reviewed structured intake, model output, safety-rule context, and "
                "available patient information before accepting the final routing "
                "decision. Important review context retained."
            ),
        },
    )
    report_response = client.post(
        "/reports/generate",
        json={"assessment_id": assessment_id, "include_audit": True},
    )
    report_id = report_response.json()["report_id"]

    download_response = client.get(f"/reports/{report_id}/download")

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content.startswith(b"%PDF")
    assert len(download_response.content) > 500
    text = pdf_text(download_response.content)
    assert "Clinician decision: Accepted" in text
    assert "Clinician final ESI:" in text
    assert "Important Review Context Retained" in text
    assert "Safety escalation triggers" in text
    assert "Clinician-selected risk flags" in text


def test_pdf_separates_selected_risk_flags_comorbidities_and_safety_triggers() -> None:
    payload = {
        **valid_intake_payload(),
        "oxygen_saturation": 91,
        "risk_flags": ["Chest pain"],
        "comorbidities": ["Hypertension"],
    }
    predict_response = client.post("/predict", json=payload)
    assessment_id = predict_response.json()["assessment_id"]

    detail = client.get(f"/assessments/{assessment_id}").json()
    assert detail["risk_flags"] == ["Chest pain"]
    assert detail["comorbidities"] == ["Hypertension"]

    report_response = client.post(
        "/reports/generate",
        json={"assessment_id": assessment_id, "include_audit": True},
    )
    text = pdf_text(client.get(report_response.json()["download_url"]).content)

    assert "Clinician-selected risk flags" in text
    assert "Chest pain" in text
    assert "Comorbidities" in text
    assert "Hypertension" in text
    assert "Safety escalation triggers" in text
    assert "Oxygen saturation below 92%" in text


def test_pdf_preserves_multiple_comorbidities() -> None:
    predict_response = client.post(
        "/predict",
        json={
            **valid_intake_payload(),
            "comorbidities": ["Diabetes", "Hypertension", "Cardiac disease"],
        },
    )
    report_response = client.post(
        "/reports/generate",
        json={
            "assessment_id": predict_response.json()["assessment_id"],
            "include_audit": True,
        },
    )
    text = pdf_text(client.get(report_response.json()["download_url"]).content)

    assert "Diabetes; Hypertension; Cardiac disease" in text


def test_pdf_distinguishes_explicit_none_from_undocumented_selections() -> None:
    none_response = client.post(
        "/predict",
        json={**valid_intake_payload(), "comorbidities": ["None reported"]},
    )
    none_report = client.post(
        "/reports/generate",
        json={
            "assessment_id": none_response.json()["assessment_id"],
            "include_audit": True,
        },
    )
    none_text = pdf_text(client.get(none_report.json()["download_url"]).content)
    assert "Comorbidities\nNone reported" in none_text

    undocumented_response = client.post("/predict", json=valid_intake_payload())
    undocumented_report = client.post(
        "/reports/generate",
        json={
            "assessment_id": undocumented_response.json()["assessment_id"],
            "include_audit": True,
        },
    )
    undocumented_text = pdf_text(
        client.get(undocumented_report.json()["download_url"]).content
    )
    assert "Clinician-selected risk flags\nNot documented" in undocumented_text
    assert "Comorbidities\nNot documented" in undocumented_text


def test_pdf_audit_is_chronological_deterministic_and_shows_seconds() -> None:
    predict_response = client.post("/predict", json=reviewed_nlp_intake_payload())
    assessment_id = predict_response.json()["assessment_id"]
    review_response = client.post(
        "/clinician-review",
        json={
            "assessment_id": assessment_id,
            "clinician_id": "clinician-123",
            "action": "accept",
            "final_esi": predict_response.json()["final_esi"],
            "notes": "Reviewed and accepted.",
        },
    )
    assert review_response.status_code == 200

    report_response = client.post(
        "/reports/generate",
        json={"assessment_id": assessment_id, "include_audit": True},
    )
    text = pdf_text(client.get(report_response.json()["download_url"]).content)
    audit_text = text[text.rfind("Audit Metadata / Audit Trail") :]
    normalized_audit_text = " ".join(audit_text.split())

    ordered_actions = [
        "Assessment created",
        "Clinical NLP extraction reviewed",
        "Prediction generated",
        "Clinician review accepted",
        "PDF report generated",
    ]
    positions = [normalized_audit_text.find(action) for action in ordered_actions]
    assert all(position >= 0 for position in positions)
    assert positions == sorted(positions)
    assert (
        len(
            re.findall(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC",
                normalized_audit_text,
            )
        )
        >= 5
    )


def test_pdf_includes_reviewed_clinical_nlp_evidence_without_unsafe_metadata() -> None:
    predict_response = client.post("/predict", json=reviewed_nlp_intake_payload())
    assert predict_response.status_code == 200
    assessment_id = predict_response.json()["assessment_id"]

    report_response = client.post(
        "/reports/generate",
        json={"assessment_id": assessment_id, "include_audit": True},
    )
    assert report_response.status_code == 200

    download_response = client.get(report_response.json()["download_url"])
    assert download_response.status_code == 200
    text = pdf_text(download_response.content)
    normalized_text = text.lower()

    assert "Clinical NLP Review Evidence" in text
    assert "Reviewed before prediction" in text
    assert "Safety Rules & Review Context" in text
    assert "Clinician review context" in text
    assert "Safety flags require clinician review" in text
    assert "clinician judgment remains required" in text
    assert "Explanation / Decision-support note" in text
    assert "Safety Rules & Recommendation" not in text
    assert "High-priority clinician review recommended" not in text
    assert "Extracted fields summary" in text
    assert "low oxygen" in normalized_text
    assert "respiratory rate" in normalized_text
    assert "62-year-old" in text
    assert "Decision-support audit context only" in text
    assert "do not store full raw note" not in normalized_text
    assert "not diagnosis" in normalized_text
    assert "not a treatment recommendation" in normalized_text
    assert "not a substitute for emergency protocols" in normalized_text
    assert "unsafe diagnosis payload" not in normalized_text
    assert "unsafe treatment payload" not in normalized_text
    assert "treatment_recommendation" not in normalized_text
    assert "AI confirmed ESI" not in text


def test_pdf_generation_without_nlp_review_event_remains_compatible() -> None:
    predict_response = client.post("/predict", json=valid_intake_payload())
    assert predict_response.status_code == 200
    assessment_id = predict_response.json()["assessment_id"]

    download_response = client.get(f"/assessments/{assessment_id}/report/pdf")

    assert download_response.status_code == 200
    assert download_response.content.startswith(b"%PDF")
    assert "Clinical NLP Review Evidence" not in pdf_text(download_response.content)


def test_assessment_pdf_download_reuses_existing_report_without_duplicate_audit() -> None:
    predict_response = client.post("/predict", json=valid_intake_payload())
    assessment_id = predict_response.json()["assessment_id"]

    first_response = client.get(f"/assessments/{assessment_id}/report/pdf")
    second_response = client.get(f"/assessments/{assessment_id}/report/pdf")

    assert first_response.status_code == 200
    assert first_response.headers["content-type"] == "application/pdf"
    assert first_response.content.startswith(b"%PDF")
    assert second_response.status_code == 200
    assert second_response.headers["content-type"] == "application/pdf"
    assert second_response.content.startswith(b"%PDF")

    detail_response = client.get(f"/assessments/{assessment_id}")
    detail = detail_response.json()
    report_actions = [
        event["action"]
        for event in detail["audit_trail"]
        if event["action"] == "report_generated"
    ]
    assert len(report_actions) == 1
    assert len(detail["report_ids"]) == 1


def test_generate_report_for_unknown_assessment_returns_404() -> None:
    response = client.post(
        "/reports/generate",
        json={"assessment_id": "unknown-assessment", "include_audit": True},
    )

    assert response.status_code == 404


def test_download_unknown_report_returns_404() -> None:
    response = client.get("/reports/unknown-report/download")

    assert response.status_code == 404


def test_pdf_safety_rule_labels_are_reader_friendly() -> None:
    assert _safety_rule_label("oxygen_saturation_below_92") == "Oxygen saturation below 92%"
    assert _safety_rule_label("oxygen_saturation_below_9 / 2") == "Oxygen saturation below 92%"
    assert _safety_rule_label("pregnancy_bleeding_red_flag") == "Pregnancy-related risk flag"
    assert _safety_rule_label("custom_rule_name") == "Custom Rule Name"


def test_pdf_audit_details_are_readable_not_raw_json() -> None:
    details = _details_text(
        {
            "payload": {
                "action": "override",
                "final_esi": 1,
                "override_reason": "Emergency",
                "notes": "Cardiac Arrest",
            }
        }
    )

    assert "Clinician decision: Override" in details
    assert "Clinician final ESI: 1" in details
    assert "Override reason: Emergency" in details
    assert "Review note: Cardiac Arrest" in details
    assert "{" not in details
    assert "}" not in details


def test_assessment_list_exposes_current_report_status_not_historical_audit():
    from app.backend.db.session import SessionLocal
    from app.backend.db.models import Report

    aid = client.post('/predict', json=valid_intake_payload()).json()['assessment_id']
    generated = client.post('/reports/generate', json={'assessment_id': aid}).json()
    rid = generated['report_id']
    with SessionLocal() as db:
        report = db.get(Report, rid)
        report.report_status = 'failed'
        report.download_url = None
        db.commit()
    row = next(item for item in client.get('/assessments').json() if item['assessment_id'] == aid)
    assert row['report_ids'] == [rid]
    assert row['reports'] == [{'report_id': rid, 'report_status': 'failed', 'created_at': row['reports'][0]['created_at']}]
    assert row['reports'][0]['created_at']
    assert client.get(f'/reports/{rid}/download').status_code == 404
    events = client.get(f'/assessments/{aid}/audit').json()['events']
    assert any(event['action'] == 'report_generated' for event in events)


def test_assessment_pdf_refreshes_after_review_and_preserves_snapshot() -> None:
    prediction = client.post('/predict', json=valid_intake_payload()).json()
    assessment_id = prediction['assessment_id']
    url = f'/assessments/{assessment_id}/report/pdf'
    before = client.get(url)
    assert before.status_code == 200
    assert 'Pending review' in pdf_text(before.content)
    original_id = client.get(f'/assessments/{assessment_id}').json()['report_ids'][0]
    review = client.post('/clinician-review', json={
        'assessment_id': assessment_id, 'clinician_id': 'snapshot-reviewer',
        'action': 'accept', 'final_esi': prediction['final_esi'],
        'notes': 'Snapshot review accepted.',
    })
    assert review.status_code == 200
    after = client.get(url)
    assert after.status_code == 200
    text = pdf_text(after.content)
    assert 'Clinician decision: Accepted' in text
    assert 'snapshot-reviewer' in text
    assert 'Snapshot Review Accepted' in text
    assert f"Clinician final ESI: {prediction['final_esi']}" in text
    assert 'Reviewed time: Pending review' not in text
    detail = client.get(f'/assessments/{assessment_id}').json()
    assert len(detail['report_ids']) == 2
    assert 'report_regenerated' in [event['action'] for event in detail['audit_trail']]
    assert client.get(f'/reports/{original_id}/download').content == before.content
    assert client.get(url).content == after.content
    assert len(client.get(f'/assessments/{assessment_id}').json()['report_ids']) == 2


def test_report_freshness_handles_utc_and_changed_prediction(monkeypatch) -> None:
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace
    from app.backend.api.routes.reports import _report_is_current
    from app.backend.db import repositories

    generated = datetime(2026, 10, 17, 4, 0, tzinfo=timezone.utc)
    assessment = SimpleNamespace(id='test', updated_at=generated - timedelta(minutes=1))
    record = SimpleNamespace(created_at=generated.replace(tzinfo=None), include_audit=True)
    prediction = SimpleNamespace(created_at=generated - timedelta(seconds=1))
    monkeypatch.setattr(repositories, 'get_latest_prediction_for_assessment', lambda *_: prediction)
    monkeypatch.setattr(repositories, 'get_latest_clinician_review_for_assessment', lambda *_: None)
    assert _report_is_current(None, assessment, record)
    prediction.created_at = generated + timedelta(seconds=1)
    assert not _report_is_current(None, assessment, record)
    prediction.created_at = generated - timedelta(seconds=1)
    assessment.updated_at = generated + timedelta(seconds=1)
    assert not _report_is_current(None, assessment, record)
    assessment.updated_at = generated - timedelta(seconds=1)
    record.include_audit = False
    assert not _report_is_current(None, assessment, record)

from fastapi.testclient import TestClient
from pathlib import Path

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
            "notes": "Reviewed for PDF report test.",
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

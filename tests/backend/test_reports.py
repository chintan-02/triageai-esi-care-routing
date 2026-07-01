from fastapi.testclient import TestClient
from pathlib import Path

from app.backend.api.main import app


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


def test_generate_report_for_unknown_assessment_returns_404() -> None:
    response = client.post(
        "/reports/generate",
        json={"assessment_id": "unknown-assessment", "include_audit": True},
    )

    assert response.status_code == 404


def test_download_unknown_report_returns_404() -> None:
    response = client.get("/reports/unknown-report/download")

    assert response.status_code == 404

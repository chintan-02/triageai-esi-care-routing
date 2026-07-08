from app.frontend.streamlit_app.services import api_client


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: dict,
        content: bytes = b"",
        headers: dict | None = None,
    ):
        self.status_code = status_code
        self._payload = payload
        self.content = content
        self.headers = headers or {}
        self.text = ""

    def json(self) -> dict:
        return self._payload


def test_get_ready_status_parses_backend_response(monkeypatch) -> None:
    def fake_get(url, timeout):
        return FakeResponse(
            200,
            {
                "status": "ready",
                "model_loaded": True,
                "model_version": "lightgbm_v2_weight_threshold_esi345",
                "database": "connected",
            },
        )

    monkeypatch.setattr(api_client.requests, "get", fake_get)

    result = api_client.get_ready_status()

    assert result["ok"] is True
    assert result["backend_connected"] is True
    assert result["data"]["model_loaded"] is True


def test_submit_prediction_marks_placeholder_warning(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        return FakeResponse(
            200,
            {
                "request_id": "request-1",
                "model_loaded": False,
                "is_placeholder": True,
                "probabilities": {},
            },
        )

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    result = api_client.submit_prediction({"patient_age": 42, "chief_complaint": "Cough"})

    assert result["ok"] is True
    assert "fallback contract response" in result["message"]


def test_submit_prediction_formats_validation_error(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        return FakeResponse(422, {"detail": [{"loc": ["body", "patient_age"]}]})

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    result = api_client.submit_prediction({"patient_age": 121})

    assert result["ok"] is False
    assert result["error_type"] == "validation_error"
    assert result["data"]["detail"][0]["loc"] == ["body", "patient_age"]


def test_submit_clinician_review_posts_payload(monkeypatch) -> None:
    posted = {}

    def fake_post(url, json, timeout):
        posted["url"] = url
        posted["json"] = json
        return FakeResponse(
            200,
            {
                "review_id": "review-1",
                "assessment_id": "assessment-1",
                "clinician_decision": "accept",
                "clinician_final_esi": 3,
                "review_note": "Reviewed.",
                "status": "review_completed",
                "reviewed": True,
                "message": "Clinician review saved and audit trail updated.",
                "is_placeholder": False,
                "timestamp": "2026-06-30T12:00:00Z",
            },
        )

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    payload = {
        "assessment_id": "assessment-1",
        "clinician_id": "clinician-456",
        "action": "accept",
        "final_esi": 3,
    }
    result = api_client.submit_clinician_review(payload)

    assert posted["url"].endswith("/clinician-review")
    assert posted["json"] == payload
    assert result["ok"] is True
    assert result["data"]["review_id"] == "review-1"
    assert result["data"]["is_placeholder"] is False


def test_submit_clinician_review_formats_validation_error(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        return FakeResponse(422, {"detail": [{"loc": ["body", "override_reason"]}]})

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    result = api_client.submit_clinician_review(
        {
            "assessment_id": "assessment-1",
            "action": "override",
            "final_esi": 2,
        }
    )

    assert result["ok"] is False
    assert result["error_type"] == "validation_error"
    assert "clinician decision fields" in result["message"]


def test_get_dashboard_summary_parses_backend_response(monkeypatch) -> None:
    def fake_get(url, timeout):
        return FakeResponse(
            200,
            {
                "total_assessments": 1,
                "model_predictions_generated": 1,
                "reviewed_assessments": 1,
                "pending_reviews": 0,
                "completed_reviews": 1,
                "override_count": 1,
                "most_common_final_esi": 2,
                "high_risk_flags": 1,
                "esi_distribution": {"2": 1},
                "recent_assessments": [
                    {
                        "assessment_id": "assessment-1",
                        "patient_id": "patient-1",
                        "patient_age": 42,
                        "sex": "female",
                        "chief_complaint": "Chest discomfort",
                        "status": "review_completed",
                        "created_at": "2026-06-30T12:00:00Z",
                        "predicted_esi": 3,
                        "model_final_esi": 3,
                        "final_esi": 2,
                        "clinician_final_esi": 2,
                        "clinician_decision": "override",
                        "final_source": "clinician_override",
                        "confidence_score": 0.78,
                    }
                ],
                "is_placeholder": False,
            },
        )

    monkeypatch.setattr(api_client.requests, "get", fake_get)

    result = api_client.get_dashboard_summary()

    assert result["ok"] is True
    assert result["data"]["override_count"] == 1
    assert result["data"]["recent_assessments"][0]["final_source"] == "clinician_override"


def test_get_assessment_detail_parses_backend_response(monkeypatch) -> None:
    def fake_get(url, timeout):
        return FakeResponse(
            200,
            {
                "request_id": "request-1",
                "assessment_id": "assessment-1",
                "patient_id": "patient-1",
                "status": "review_completed",
                "chief_complaint": "Chest discomfort",
                "created_at": "2026-06-30T12:00:00Z",
                "updated_at": "2026-06-30T12:01:00Z",
                "intake": {
                    "patient_age": 42,
                    "chief_complaint": "Chest discomfort",
                },
                "latest_prediction": {
                    "prediction_id": "prediction-1",
                    "model_loaded": True,
                    "predicted_esi": 3,
                    "final_esi": 3,
                    "confidence_score": 0.78,
                    "probabilities": {"ESI_3": 0.78, "ESI_4": 0.2, "ESI_5": 0.02},
                    "safety_rules_triggered": [],
                    "final_source": "model",
                    "recommendation": "Urgent evaluation recommended.",
                    "explanation": "Model explanation.",
                    "clinician_summary": "Summary.",
                    "is_placeholder": False,
                },
                "latest_clinician_review": {
                    "review_id": "review-1",
                    "clinician_id": "clinician-456",
                    "clinician_decision": "accept",
                    "clinician_final_esi": 3,
                    "reviewed": True,
                },
                "audit_trail": [{"audit_id": "audit-1", "action": "clinician_review_accept"}],
                "message": "Assessment loaded from database.",
                "is_placeholder": False,
            },
        )

    monkeypatch.setattr(api_client.requests, "get", fake_get)

    result = api_client.get_assessment_detail("assessment-1")

    assert result["ok"] is True
    assert result["data"]["assessment_id"] == "assessment-1"
    assert result["data"]["latest_prediction"]["predicted_esi"] == 3
    assert result["data"]["latest_clinician_review"]["clinician_decision"] == "accept"


def test_get_assessment_detail_formats_not_found(monkeypatch) -> None:
    def fake_get(url, timeout):
        return FakeResponse(404, {"detail": "Assessment not found"})

    monkeypatch.setattr(api_client.requests, "get", fake_get)

    result = api_client.get_assessment_detail("missing")

    assert result["ok"] is False
    assert result["error_type"] == "not_found"
    assert result["message"] == "Assessment not found"


def test_generate_report_posts_assessment_id(monkeypatch) -> None:
    posted = {}

    def fake_post(url, json, timeout):
        posted["url"] = url
        posted["json"] = json
        return FakeResponse(
            200,
            {
                "report_id": "report-1",
                "assessment_id": "assessment-1",
                "file_name": "triageai_report_report-1.pdf",
                "file_path": "reports/generated/triageai_report_report-1.pdf",
                "status": "generated",
                "report_status": "generated",
                "download_url": "/reports/report-1/download",
                "created_at": "2026-06-30T12:00:00Z",
                "message": "PDF report generated for assessment decision-support review.",
                "is_placeholder": False,
            },
        )

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    result = api_client.generate_report("assessment-1")

    assert posted["url"].endswith("/reports/generate")
    assert posted["json"] == {"assessment_id": "assessment-1", "include_audit": True}
    assert result["ok"] is True
    assert result["data"]["is_placeholder"] is False
    assert result["data"]["download_url"] == "/reports/report-1/download"


def test_generate_report_formats_not_found(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        return FakeResponse(404, {"detail": "Assessment not found"})

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    result = api_client.generate_report("missing")

    assert result["ok"] is False
    assert result["error_type"] == "not_found"
    assert result["message"] == "Assessment not found"


def test_download_report_returns_pdf_bytes(monkeypatch) -> None:
    def fake_get(url, timeout):
        return FakeResponse(
            200,
            {},
            content=b"%PDF-1.4 report bytes",
            headers={"content-type": "application/pdf"},
        )

    monkeypatch.setattr(api_client.requests, "get", fake_get)

    result = api_client.download_report("report-1")

    assert result["ok"] is True
    assert result["data"]["content"].startswith(b"%PDF")
    assert result["data"]["content_type"] == "application/pdf"

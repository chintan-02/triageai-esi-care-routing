from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from google.api_core.exceptions import NotFound, ServiceUnavailable

from app.backend.api.main import app
from app.backend.core.config import settings
from app.backend.services.report_storage import GCSReportStore, LocalReportStore


def test_local_store_survives_recreation_and_rejects_traversal(tmp_path):
    key = f"{uuid4()}.pdf"
    LocalReportStore(str(tmp_path)).put(key, b"%PDF test")
    assert LocalReportStore(str(tmp_path)).get(key) == b"%PDF test"
    with pytest.raises(ValueError):
        LocalReportStore(str(tmp_path)).get("../private.pdf")


def test_gcs_adapter_uses_private_objects_and_distinguishes_outage(monkeypatch):
    client = Mock()
    monkeypatch.setattr("google.cloud.storage.Client", lambda: client)
    store = GCSReportStore("private-reports")
    key = f"{uuid4()}.pdf"
    blob = client.bucket.return_value.blob.return_value
    store.put(key, b"%PDF test")
    blob.upload_from_string.assert_called_once_with(b"%PDF test", content_type="application/pdf", timeout=30)
    blob.download_as_bytes.return_value = b"%PDF test"
    assert store.get(key) == b"%PDF test"
    blob.download_as_bytes.side_effect = NotFound("missing")
    with pytest.raises(FileNotFoundError):
        store.get(key)
    blob.download_as_bytes.side_effect = ServiceUnavailable("unavailable")
    with pytest.raises(ServiceUnavailable):
        store.get(key)


def test_remote_report_download_does_not_depend_on_temporary_file(monkeypatch):
    objects = {}
    class ObjectStore:
        def put(self, key, content): objects[key] = content
        def get(self, key): return objects[key]
    monkeypatch.setattr(settings, "REPORT_STORAGE_BACKEND", "gcs")
    monkeypatch.setattr("app.backend.api.routes.reports.get_report_store", lambda backend=None: ObjectStore())
    client = TestClient(app)
    prediction = client.post("/predict", json={"patient_age": 30, "chief_complaint": "Synthetic ankle pain"})
    aid = prediction.json()["assessment_id"]
    response = client.post("/reports/generate", json={"assessment_id": aid})
    assert response.status_code == 200
    assert response.json()["file_path"] is None
    assert len(objects) == 1
    assert TestClient(app).get(response.json()["download_url"]).content.startswith(b"%PDF")


def test_upload_failure_never_marks_report_generated(monkeypatch):
    from app.backend.db.session import SessionLocal
    from app.backend.db.models import Report
    from sqlalchemy import select
    store = Mock()
    store.put.side_effect = RuntimeError("secret upstream details")
    monkeypatch.setattr("app.backend.api.routes.reports.get_report_store", lambda backend=None: store)
    client = TestClient(app)
    aid = client.post("/assessments", json={"patient_age": 30, "chief_complaint": "Synthetic pain"}).json()["assessment_id"]
    response = client.post("/reports/generate", json={"assessment_id": aid})
    assert response.status_code == 503
    assert "secret upstream details" not in response.text
    with SessionLocal() as db:
        assert db.scalar(select(Report)).report_status == "failed"

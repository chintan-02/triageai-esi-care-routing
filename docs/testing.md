# Testing

Phase 10A strengthens deterministic regression checks for the TriageAI / SympDirect clinical decision-support workflow before Docker, deployment, capstone demo, and portfolio screenshots.

## Core Commands

```bash
python ml/inference/validate_artifacts.py
pytest
python -m uvicorn app.backend.api.main:app --reload --port 8001
python scripts/api_smoke_test.py --base-url http://127.0.0.1:8001
```

## Covered

- Model artifact validation for the deployed LightGBM ESI 3/4/5 artifact and companion metadata.
- Health and readiness response shape for deployment smoke checks.
- Structured intake prediction responses, including predicted ESI, final ESI, probabilities, confidence, model version, recommendation/explanation fields, disclaimer text, and safety-rule fields.
- Safety-rule escalation for low oxygen saturation and cardiopulmonary red-flag intake scenarios.
- Clinician review accept and override workflow, including required override reasons and audit trail updates.
- Dashboard summary counts for total assessments, generated predictions, reviewed and pending assessments, overrides, most common final ESI, ESI distribution, and recent assessment rows.
- Assessment detail retrieval for existing and missing assessments, including intake summary, latest prediction, clinician review status, and audit trail.
- PDF decision-support summary generation and download checks for non-empty PDF artifacts.
- Demo reset/seed script safety checks using local/test SQLite patterns so tests do not destroy a developer's real local database.
- A local API smoke-test script that checks `/health`, `/ready`, and a safe sample `/predict` request.

## Intentionally Not Covered Yet

- Streamlit rendering and visual regression screenshots.
- Browser-driven dashboard-to-detail navigation tests.
- Docker image build checks.
- External network, SMTP, Azure Speech, or production environment integration tests.
- Retraining, model metric regeneration, or model artifact mutation.
- Tests against real clinical production data.

## Data Safety

Tests use local fixtures, temporary paths, or the isolated pytest SQLite database configured in `tests/backend/conftest.py`. Demo reset/seed tests use temporary files or test database sessions and should not be pointed at real clinical production data.

The project should be described as a clinical decision-support workflow that uses structured intake data, ESI care routing, safety-rule escalation, clinician review, human-in-the-loop override, audit trail records, and PDF decision-support summaries. It is not a diagnostic tool and does not replace clinicians.

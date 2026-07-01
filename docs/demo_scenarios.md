# Demo Scenarios

Phase 9A prepares clean local demo data and realistic walkthrough cases for
screenshots, portfolio review, and recruiter demos. This is a documentation-only
plan. It does not change model artifacts, model inference logic, clinician
review behavior, backend contracts, or legacy reference files.

The expected model behavior below was checked against the current local
LightGBM artifact through the existing prediction service. Exact probabilities
can change if artifacts are retrained or replaced, so do not hard-code
probabilities in demo narration.

## Local Demo Data Behavior

Local development uses SQLite by default:

- Default database URL: `sqlite:///./triageai.db`
- Local DB file: `triageai.db` in the repository root
- Tables are created on backend startup through `init_db()`
- `POST /predict` creates both an assessment and the latest prediction
- `POST /clinician-review` creates a clinician review, updates assessment
  status, and writes an audit log
- `POST /reports/generate` creates report metadata and a local PDF under
  `reports/generated/`

Tests do not use the local demo DB. The test suite overrides `DATABASE_URL` to a
temporary SQLite file under the system temp directory.

## Safe Local Cleanup

Identify the active local SQLite path:

```bash
python -c "from app.backend.core.config import settings; print(settings.DATABASE_URL)"
ls -lh triageai.db
```

For local demo resets only, prefer backing up or moving the local SQLite file
rather than deleting source code, model artifacts, or production-like data.

Safe local backup/reset:

```bash
# Stop backend/frontend first.
cp triageai.db triageai.demo-backup.db
mv triageai.db triageai.previous-demo.db
python -m uvicorn app.backend.api.main:app --reload --port 8001
```

Backend startup recreates empty tables. Keep the backup until screenshots and
reports are verified.

If you only want to clear workflow rows while keeping the same DB file, use this
only for a local throwaway demo database:

```bash
sqlite3 triageai.db "
DELETE FROM reports;
DELETE FROM audit_logs;
DELETE FROM clinician_reviews;
DELETE FROM predictions;
DELETE FROM assessments;
DELETE FROM patients;
"
```

Generated PDFs are ignored by git. For a visually clean demo folder, remove old
local PDFs only after confirming they are not needed:

```bash
find reports/generated -name '*.pdf' -delete
```

Do not run cleanup commands against any shared, production-like, or externally
hosted database.

## Creating Fresh Demo Data

Scripted local reset/seed path:

```bash
python scripts/demo_reset_seed.py --backup
python scripts/demo_reset_seed.py --backup --reset --seed --yes
```

The script prints the active `DATABASE_URL`, resolves the local SQLite path,
refuses non-SQLite database URLs, requires `--yes` for destructive reset, backs
up to `backups/demo_db/`, clears workflow tables, and seeds five demo cases
through the real prediction service plus the normal clinician review repository
flow. It does not hard-code model outputs.

UI path:

1. Start backend:

```bash
python -m uvicorn app.backend.api.main:app --reload --port 8001
```

2. Start frontend:

```bash
streamlit run app/frontend/streamlit_app/Home.py
```

3. Open **New Assessment** and enter one case below.
4. Review **Assessment Result**.
5. Open **Clinician Review** when the scenario calls for accept or override.
6. Open **Dashboard** and **Assessment Detail** for screenshots.
7. Generate a PDF report from **Assessment Detail** when needed.

API path:

1. `POST /predict` with the intake payload to create the assessment and model
   prediction.
2. Copy `assessment_id` and `final_esi` from the response.
3. For reviewed scenarios, `POST /clinician-review` with that assessment ID.
4. For PDF screenshots, `POST /reports/generate` and download from the returned
   `download_url`.

Example API pattern:

```bash
curl -s -X POST http://127.0.0.1:8001/predict \
  -H "Content-Type: application/json" \
  -d '{...intake payload...}'

curl -s -X POST http://127.0.0.1:8001/clinician-review \
  -H "Content-Type: application/json" \
  -d '{
    "assessment_id": "paste-assessment-id",
    "clinician_id": "demo-clinician",
    "action": "accept"
  }'

curl -s -X POST http://127.0.0.1:8001/reports/generate \
  -H "Content-Type: application/json" \
  -d '{"assessment_id": "paste-assessment-id", "include_audit": true}'
```

## Case A: Typical ESI 3

Purpose: show common ESI 3 decision-support behavior with stable vitals and no
safety-rule escalation.

Intake:

```json
{
  "patient_age": 52,
  "sex": "female",
  "chief_complaint": "Abdominal pain with vomiting",
  "symptom_duration": "8 hours",
  "pain_score": 6,
  "temperature_c": 37.4,
  "heart_rate": 96,
  "respiratory_rate": 18,
  "systolic_bp": 130,
  "diastolic_bp": 82,
  "oxygen_saturation": 98.0,
  "consciousness_level": "alert",
  "pregnancy": false,
  "arrival_mode": "walk-in",
  "additional_context": "Multiple episodes of vomiting, no confusion."
}
```

Expected behavior:

- Model output: predicted ESI 3, final ESI 3
- Safety rules: none triggered
- Clinician review action: accept recommendation
- Screenshot/demo purpose: result card, model probabilities, recommendation,
  accepted clinician review, dashboard reviewed count, and PDF report for a
  typical reviewed case

Suggested clinician review payload:

```json
{
  "clinician_id": "demo-clinician",
  "action": "accept",
  "notes": "Reviewed as stable ESI 3 demo scenario."
}
```

## Case B: Safety-Rule Escalation

Purpose: show transparent safety-rule escalation from model ESI 3 to final ESI 2
when oxygen saturation is below 92%.

Intake:

```json
{
  "patient_age": 67,
  "sex": "male",
  "chief_complaint": "Cough and shortness of breath",
  "symptom_duration": "1 day",
  "pain_score": 3,
  "temperature_c": 37.9,
  "heart_rate": 108,
  "respiratory_rate": 22,
  "systolic_bp": 138,
  "diastolic_bp": 84,
  "oxygen_saturation": 89.0,
  "consciousness_level": "alert",
  "pregnancy": false,
  "arrival_mode": "walk-in",
  "additional_context": "Feels breathless walking across room."
}
```

Expected behavior:

- Model output: predicted ESI 3 in the current artifact sample
- Safety rules: `oxygen_saturation_below_92` triggers
- Final ESI: ESI 2 with `final_source: safety_rule_override`
- Clinician review action: accept safety escalation
- Screenshot/demo purpose: safety-rule warning, final source, audit trail, and
  PDF safety-rule section

Suggested clinician review payload:

```json
{
  "clinician_id": "demo-clinician",
  "action": "accept",
  "notes": "Accepted safety-rule escalation due to low oxygen saturation."
}
```

## Case C: Clinician Override

Purpose: show human-in-the-loop review where the clinician selects a higher
acuity final ESI than the model/safety output and documents the reason.

Intake:

```json
{
  "patient_age": 41,
  "sex": "female",
  "chief_complaint": "Headache",
  "symptom_duration": "6 hours",
  "pain_score": 5,
  "temperature_c": 36.8,
  "heart_rate": 80,
  "respiratory_rate": 16,
  "systolic_bp": 122,
  "diastolic_bp": 78,
  "oxygen_saturation": 99.0,
  "consciousness_level": "alert",
  "pregnancy": false,
  "arrival_mode": "walk-in",
  "additional_context": "No weakness, no confusion, no trauma."
}
```

Expected behavior:

- Model output: predicted ESI 3, final ESI 3
- Safety rules: none triggered
- Clinician review action: override to ESI 2
- Override reason: "New severe headache pattern and clinician concern after
  bedside assessment."
- Review note: "Escalated for urgent clinician evaluation; additional context
  documented during review."
- Screenshot/demo purpose: override form, model-vs-clinician explanation,
  dashboard override count, audit trail, and PDF override note

Suggested clinician review payload:

```json
{
  "clinician_id": "demo-clinician",
  "action": "override",
  "final_esi": 2,
  "override_reason": "New severe headache pattern and clinician concern after bedside assessment.",
  "notes": "Escalated for urgent clinician evaluation; additional context documented during review."
}
```

## Case D: Lower-Acuity Case

Purpose: show that the model can produce a lower-acuity ESI 4 style result when
the complaint and vitals are stable. The current artifact sample produced ESI 4
for this case.

Intake:

```json
{
  "patient_age": 34,
  "sex": "male",
  "chief_complaint": "Ankle injury after twisting while walking",
  "symptom_duration": "3 hours",
  "pain_score": 4,
  "temperature_c": 36.7,
  "heart_rate": 82,
  "respiratory_rate": 16,
  "systolic_bp": 124,
  "diastolic_bp": 78,
  "oxygen_saturation": 98.0,
  "consciousness_level": "alert",
  "pregnancy": false,
  "arrival_mode": "walk-in",
  "additional_context": "Able to bear partial weight, no deformity, distal circulation intact."
}
```

Expected behavior:

- Model output: predicted ESI 4, final ESI 4 in the current artifact sample
- Safety rules: none triggered
- Clinician review action: accept final ESI 4, or leave pending if the demo
  needs another unreviewed row
- Screenshot/demo purpose: lower-acuity dashboard row, ESI distribution, and
  accepted or pending lower-acuity workflow

Suggested clinician review payload:

```json
{
  "clinician_id": "demo-clinician",
  "action": "accept",
  "notes": "Stable lower-acuity presentation reviewed for demo."
}
```

## Case E: Pending Review

Purpose: show dashboard and assessment detail states before clinician review is
completed.

Intake:

```json
{
  "patient_age": 28,
  "sex": "female",
  "chief_complaint": "Mild itchy rash on forearm",
  "symptom_duration": "2 days",
  "pain_score": 1,
  "temperature_c": 36.8,
  "heart_rate": 74,
  "respiratory_rate": 14,
  "systolic_bp": 118,
  "diastolic_bp": 76,
  "oxygen_saturation": 99.0,
  "consciousness_level": "alert",
  "pregnancy": false,
  "arrival_mode": "walk-in",
  "additional_context": "No fever, no swelling, no breathing symptoms."
}
```

Expected behavior:

- Model output: predicted ESI 3 in the current artifact sample
- Safety rules: none triggered
- Clinician review action: none; leave pending
- Screenshot/demo purpose: dashboard pending-review count, Assessment Detail
  pending review warning, and PDF generated before review showing "Pending
  clinician review"

## Suggested Demo Screenshot Set

- New Assessment form with a realistic intake
- Result page for Case B showing safety escalation
- Clinician Review override form for Case C
- Dashboard after all five cases are created
- Assessment Detail for Case C showing model output, clinician final ESI, and
  audit trail
- PDF report for Case B or Case C

## Demo Integrity Rules

- Do not edit model probabilities or final ESI values manually.
- Do not seed fake prediction rows directly into the database.
- Use `POST /predict` or the UI so the real model and safety rules create the
  prediction record.
- Use `POST /clinician-review` or the UI so the audit trail is created through
  the normal workflow.
- Avoid CTAS/KTAS language in narration and screenshots.
- Describe output as decision support, not diagnosis.

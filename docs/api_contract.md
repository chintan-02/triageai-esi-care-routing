# API Contract

TriageAI Phase 3 exposes ESI-only backend contracts with local database
persistence for assessments, prediction records, clinician reviews, audit logs,
report metadata, and dashboard summaries.

Responses with `is_placeholder: true` are workflow scaffolding only and must not
be treated as clinical output.

## Health

`GET /health`

Returns service health.

```json
{
  "status": "ok",
  "service": "TriageAI API"
}
```

## Readiness

`GET /ready`

Returns current backend readiness. The ML model is still intentionally not
loaded in Phase 3.

```json
{
  "status": "ready",
  "model_loaded": false,
  "database": "not_connected"
}
```

## Patient Intake

The shared intake request shape is used by `POST /predict` and
`POST /assessments`.

Required fields:

- `patient_age`: integer from 0 to 120
- `chief_complaint`: string with minimum length 3

Optional fields:

- `sex`
- `symptom_duration`
- `pain_score`: integer from 0 to 10
- `temperature_c`
- `heart_rate`
- `respiratory_rate`
- `systolic_bp`
- `diastolic_bp`
- `oxygen_saturation`: number from 0 to 100
- `consciousness_level`
- `pregnancy`
- `arrival_mode`
- `additional_context`

## Speech Transcription

`POST /speech/transcribe`

Accepts multipart form-data with `audio_file`.

Returns a contract-only speech-to-text response. Azure Speech integration is a
future phase:

```json
{
  "transcript": "",
  "confidence": null,
  "language": "en-US",
  "is_placeholder": true,
  "message": "Speech-to-text contract is ready. Azure Speech integration will be added in the next implementation phase."
}
```

## ESI Prediction

`POST /predict`

Accepts `PatientIntakeRequest`.

The Streamlit frontend submits intake to this endpoint and renders the returned
`assessment_id`, `request_id`, ESI prediction fields, probabilities, safety
rules, recommendation, explanation, clinician summary, and model metadata.

Phase 4 stores the intake as a database-backed assessment, attempts to load the
approved ESI 3/4/5 artifacts, and stores prediction metadata against that
assessment.

If required artifacts are missing or invalid, the endpoint returns the safe
placeholder shape with `model_loaded: false` and `is_placeholder: true`.

If artifacts are present and valid, the endpoint returns model probabilities,
`model_loaded: true`, a predicted ESI, safety-rule-adjusted final ESI, and
`is_placeholder: false`.

Required placeholder response behavior:

- `assessment_id`: ID of the persisted assessment
- `acuity_scale`: `ESI`
- `model_loaded`: `false` when artifacts are unavailable, otherwise `true`
- `model_version`: artifact metadata version when available
- `predicted_esi`: `null` without artifacts, otherwise ESI 3/4/5
- `final_esi`: `null` without artifacts, otherwise model output or safety-rule escalation
- `confidence_score`: `null` without artifacts, otherwise selected class probability
- `probabilities`: `{}` without artifacts, otherwise class probabilities
- `is_placeholder`: `true` without artifacts, otherwise `false`
- `recommendation`: placeholder text without artifacts, otherwise an ESI review pathway recommendation
- `disclaimer`: decision-support only, not diagnosis

## Assessments

`POST /assessments`

Accepts `PatientIntakeRequest`, creates a minimal patient record and assessment
record, and returns:

- `assessment_id`
- `patient_id`
- `status`: `pending_review`
- `created_at`
- `is_placeholder`: `false`

`GET /assessments/{assessment_id}`

Loads the persisted assessment detail and returns `404` when the assessment does
not exist.

## Clinician Review

`POST /clinician-review`

Accepts:

- `assessment_id`
- `clinician_id`
- `action`: `accept`, `override`, or `needs_review`
- `final_esi`: optional integer from 1 to 5
- `override_reason`: required when `action` is `override`
- `notes`

Verifies the assessment exists, persists the review, writes an audit log, and
updates assessment status:

- `review_completed` for `accept` or `override`
- `needs_review` for `needs_review`

Returns `404` when the assessment does not exist. Successful responses include
`is_placeholder: false`.

## Dashboard

`GET /dashboard/summary`

Returns database-backed dashboard counts:

```json
{
  "total_assessments": 0,
  "pending_reviews": 0,
  "completed_reviews": 0,
  "high_risk_flags": 0,
  "esi_distribution": {},
  "recent_assessments": [],
  "is_placeholder": false
}
```

`high_risk_flags` and `esi_distribution` are based on the latest stored
prediction `final_esi` when available.

## Reports

`POST /reports/generate`

Accepts:

- `assessment_id`
- `include_audit`: boolean, default `true`

Verifies the assessment exists and stores report metadata with status `queued`.
No PDF is generated yet, so the response keeps `is_placeholder: true` and
`download_url: null`. Returns `404` when the assessment does not exist.

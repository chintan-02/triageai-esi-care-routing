# API Contract

TriageAI Phase 2 exposes ESI-only backend contracts. Prediction, speech,
persistence, review, dashboard, and report endpoints are placeholders until
their production integrations are implemented.

Placeholder responses include `is_placeholder: true` and must not be treated as
clinical output.

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

Returns current backend readiness. Phase 2 does not connect the model or
database.

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

Returns a placeholder speech-to-text contract response:

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

Phase 2 validates the request contract only. It does not load a model, infer an
ESI level, or apply clinical routing.

Required placeholder response behavior:

- `acuity_scale`: `ESI`
- `model_loaded`: `false`
- `predicted_esi`: `null`
- `final_esi`: `null`
- `confidence_score`: `null`
- `probabilities`: `{}`
- `is_placeholder`: `true`
- `recommendation`: `Model inference is not connected yet. This endpoint validates the request contract only.`
- `disclaimer`: decision-support only, not diagnosis

## Assessments

`POST /assessments`

Accepts `PatientIntakeRequest` and returns a generated `assessment_id`. No
database record is created in Phase 2.

`GET /assessments/{assessment_id}`

Returns placeholder assessment detail for the requested ID. No persisted
assessment is loaded in Phase 2.

## Clinician Review

`POST /clinician-review`

Accepts:

- `assessment_id`
- `clinician_id`
- `action`: `accept`, `override`, or `needs_review`
- `final_esi`: optional integer from 1 to 5
- `override_reason`: required when `action` is `override` and `final_esi` is provided
- `notes`

Returns a generated `review_id` with `is_placeholder: true`. No review is
persisted in Phase 2.

## Dashboard

`GET /dashboard/summary`

Returns zeroed placeholder dashboard counts:

```json
{
  "total_assessments": 0,
  "pending_reviews": 0,
  "completed_reviews": 0,
  "high_risk_flags": 0,
  "esi_distribution": {},
  "recent_assessments": [],
  "is_placeholder": true
}
```

## Reports

`POST /reports/generate`

Accepts:

- `assessment_id`
- `include_audit`: boolean, default `true`

Returns a placeholder report status with no `download_url`. No report file is
generated in Phase 2.

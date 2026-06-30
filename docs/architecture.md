# Architecture

## Overview

TriageAI is an ESI-only clinical intake and care routing assistant. Phase 3 adds
database persistence around the existing FastAPI contracts while keeping real ML
inference, Azure Speech transcription, PDF generation, authentication, and the
frontend as future-phase work.

## Backend

The backend is a FastAPI application under `app/backend/api`. Routes validate
Pydantic schemas, call small repository functions, and return explicit
placeholder flags where downstream clinical integrations are not yet real.

On application startup, `init_db()` imports the ORM models and creates tables
for local development and tests. Alembic is intentionally not introduced in
Phase 3.

## Database Persistence

SQLAlchemy ORM models live in `app/backend/db/models.py`, with session setup in
`app/backend/db/session.py` and repository helpers in
`app/backend/db/repositories.py`.

Local development uses SQLite through `DATABASE_URL`, defaulting to
`sqlite:///./triageai.db`. The engine setup keeps SQLite-only
`check_same_thread` configuration isolated so the same structure remains ready
for PostgreSQL later.

Phase 3 creates these tables:

- `users`
- `patients`
- `assessments`
- `predictions`
- `clinician_reviews`
- `audit_logs`
- `reports`

The active patient table stores only minimal intake demographics needed for the
workflow. It does not store unnecessary identifying information.

## Assessment Flow

`POST /assessments` creates a patient and assessment with status
`pending_review`.

`POST /predict` creates a patient and assessment, then runs the model-aware
prediction flow:

`PatientIntakeRequest -> feature_builder -> LightGBM V2 booster text model -> thresholds -> safety_rules -> explanation -> DB prediction record`

If required artifacts are missing or invalid, the prediction service returns the
safe placeholder response and stores placeholder prediction metadata. If
artifacts are available, it stores real ESI 3/4/5 probabilities and the final ESI
after transparent safety-rule handling.

`POST /clinician-review` verifies the assessment exists, saves the clinician
review, writes an audit log, and updates the assessment status to
`review_completed` or `needs_review`.

`GET /dashboard/summary` reads database counts, recent assessments, and ESI
distribution data from stored prediction records.

`POST /reports/generate` verifies the assessment exists and stores report
metadata with status `queued`. Real PDF generation remains a future phase.

## Frontend

No frontend UI is implemented in Phase 3.

## ML Pipeline

Training stays outside FastAPI in `ml/training` and notebooks. The backend only
loads saved artifacts from `model_artifacts/`:

- `esi_345_lightgbm_v2_threshold.txt`
- `thresholds.json`
- `feature_schema.json`
- `model_metadata.json`

The selected staging model is LightGBM V2 Weight + Threshold. V3 files are kept
as comparison/reference artifacts only. Missing runtime support never crashes
startup or `/predict`; it produces a clear placeholder response with
`model_loaded: false`.

## Deployment

The current deployment shape is local-development focused. SQLite works out of
the box through `DATABASE_URL`; a PostgreSQL URL can be supplied later without
changing route or repository call sites.

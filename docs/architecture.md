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

`POST /predict` creates a patient and assessment, returns the existing
contract-only ESI prediction response, and stores prediction metadata linked to
the assessment. The model remains unloaded and `is_placeholder` remains `true`.

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

The ML pipeline and model artifacts remain disconnected from the API in Phase 3.
Prediction responses are contract-only, include `model_loaded: false`, and do
not provide fake ESI inference.

## Deployment

The current deployment shape is local-development focused. SQLite works out of
the box through `DATABASE_URL`; a PostgreSQL URL can be supplied later without
changing route or repository call sites.

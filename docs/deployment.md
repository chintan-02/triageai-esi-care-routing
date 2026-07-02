# Deployment

This Docker setup supports local demo deployment for the TriageAI / SympDirect clinical decision-support workflow. It runs the FastAPI backend and Streamlit frontend with local SQLite storage, structured intake data, ESI care routing, safety-rule escalation, clinician review, audit trail records, and PDF decision-support summary generation.

## Local Commands

Run the backend without Docker:

```bash
python -m uvicorn app.backend.api.main:app --reload --port 8001
```

Run the frontend without Docker:

```bash
streamlit run app/frontend/streamlit_app/Home.py
```

## Docker Commands

Build both images:

```bash
docker compose build
```

Start the local demo stack:

```bash
docker compose up
```

Stop the stack:

```bash
docker compose down
```

Expected local URLs:

- Backend: http://127.0.0.1:8001
- Frontend: http://127.0.0.1:8501

Docker Compose uses named volumes for local SQLite data and generated PDF reports:

- `triageai_sqlite_data` mounted at `/app/data`
- `triageai_reports` mounted at `/app/reports/generated`

## Smoke Test

With the backend running, verify the API:

```bash
python scripts/api_smoke_test.py --base-url http://127.0.0.1:8001
```

The smoke test checks `/health`, `/ready`, and a safe sample `/predict` request. `/ready` should return HTTP 200 only when required app components are available.

## Demo Data

For local SQLite demo data, run:

```bash
python scripts/demo_reset_seed.py --backup --reset --seed --yes
```

This command is intended for local SQLite demo databases only. It backs up existing local data before reset and should not be pointed at real clinical data.

## Environment

Use `.env.example` as a non-secret reference for local settings. The Docker Compose stack sets demo-safe values directly and stores SQLite/report output in Docker volumes. Do not commit real secrets.

The frontend reads `TRIAGEAI_BACKEND_URL`; Docker Compose sets it to `http://backend:8001` so the Streamlit container can reach the FastAPI service.

Key local settings:

- `APP_ENV`: environment label, such as `development` or `demo`.
- `LOG_LEVEL`: optional logging verbosity label for local runs.
- `DEMO_MODE`: marks local demo behavior when set to `true`.
- `DATABASE_URL`: local SQLite database URL.
- `TRIAGEAI_BACKEND_URL`: backend API base URL used by the Streamlit frontend.
- `MODEL_PATH`, `THRESHOLDS_PATH`, `FEATURE_SCHEMA_PATH`, and `MODEL_METADATA_PATH`: model artifact paths used by backend readiness and prediction.

## Troubleshooting

If port `8001` or `8501` is already in use, stop the conflicting local process or update the host-side port mapping in `docker-compose.yml`. Keep the container ports as `8001` for the backend and `8501` for Streamlit unless the app commands are also changed.

If `/ready` does not pass, check the backend logs:

```bash
docker compose logs backend
```

The most common readiness issues are missing model artifacts, dependency installation problems, or an unavailable SQLite volume path.

If the frontend cannot reach the backend inside Docker, confirm `TRIAGEAI_BACKEND_URL=http://backend:8001` is set for the frontend service.

## Notes

This is a capstone/demo deployment setup for local review and portfolio walkthroughs. It is not intended for live clinical use. The workflow is designed to support clinician review and human-in-the-loop override; it is not a substitute for clinician judgment.

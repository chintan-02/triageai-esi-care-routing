# TriageAI – AI Clinical Intake & ESI Care Routing Assistant

TriageAI is an AI-assisted clinical intake and ESI care-routing system designed for structured patient intake, speech-to-text symptom capture, explainable ESI triage support, clinician review, audit traceability, dashboard visibility, and backend-generated PDF reports.

This project is decision-support only. It is not diagnosis and does not replace clinician judgment.

## Run Locally

Start the FastAPI backend:

```bash
python -m uvicorn app.backend.api.main:app --reload --port 8001
```

Verify readiness:

```bash
curl http://127.0.0.1:8001/ready
```

Start the React frontend:

```bash
cd app/frontend/react_app
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Start the Streamlit frontend:

```bash
streamlit run app/frontend/streamlit_app/Home.py
```

Workflow:

1. Start FastAPI.
2. Confirm `/ready` reports backend/database/model status.
3. Start React on port 5173 for the production-style frontend, or Streamlit for the legacy frontend.
4. Submit intake on **New Assessment**.
5. Review the backend-generated ESI result on **Assessment Detail**.
6. Download official backend PDF reports from **Reports**.
7. Review backend audit events from **Audit**.

## Production Notes

- The backend/database is the source of truth for assessments, dashboard summaries, audit events, clinician review, and official reports.
- Local development uses SQLite with `DATABASE_URL=sqlite:///./triageai.db`.
- Azure or other production deployments should use PostgreSQL.
- The final model registry path is `model_registry/esi_345_lightgbm_v2`.
- React uses `VITE_API_BASE_URL=http://localhost:8001` for local FastAPI.
- Generated files such as `node_modules`, `dist`, `*.tsbuildinfo`, local SQLite databases, and generated PDFs should not be tracked.

## Reset Local Demo Data

For screenshot-ready local data, reset and seed the SQLite demo database:

```bash
python scripts/reset_demo_data.py
```

This command is local SQLite only. It backs up the existing database, clears demo workflow tables, seeds named demo patients with MRNs, runs predictions through the backend model path, saves clinician review/audit records, and prepares backend PDF report records. Do not use it against production databases.

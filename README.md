# TriageAI – AI Clinical Intake & ESI Care Routing Assistant

TriageAI is an AI-assisted clinical intake and ESI care-routing system designed for structured patient intake, speech-to-text symptom capture, explainable ESI triage support, clinician review, and dashboard visibility.

This project is designed as clinical decision support and does not replace medical judgment.

## Run Locally

Start the FastAPI backend:

```bash
python -m uvicorn app.backend.api.main:app --reload --port 8001
```

Verify readiness:

```bash
curl http://127.0.0.1:8001/ready
```

Start the Streamlit frontend:

```bash
streamlit run app/frontend/streamlit_app/Home.py
```

Workflow:

1. Start FastAPI.
2. Confirm `/ready` reports backend/database/model status.
3. Start Streamlit.
4. Submit intake on **New Assessment**.
5. Review the backend-generated ESI result on **Assessment Result**.

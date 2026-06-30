# Frontend

The Streamlit frontend submits structured intake to the FastAPI backend and
displays the `/predict` response. It does not call model artifacts directly and
does not generate frontend-only predictions.

## Run Workflow

1. Start the backend:

```bash
python -m uvicorn app.backend.api.main:app --reload --port 8001
```

2. Verify readiness:

```bash
curl http://127.0.0.1:8001/ready
```

3. Start the frontend:

```bash
streamlit run app/frontend/streamlit_app/Home.py
```

4. Open **New Assessment**, submit intake, then review the ESI result on
**Assessment Result**.

The result page shows final ESI, predicted ESI, confidence, class
probabilities, safety rules, recommendation, explanation, clinician summary,
model metadata, request ID, and assessment ID.

If the backend is unavailable, the sidebar shows:

```bash
python -m uvicorn app.backend.api.main:app --reload --port 8001
```

If the backend returns `model_loaded: false`, the UI clearly labels the output as
a fallback contract response.

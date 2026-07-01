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
5. Select **Proceed to Clinician Review** to accept the model/safety final ESI
or override it with a required reason.

The result page shows final ESI, predicted ESI, confidence, class
probabilities, safety rules, recommendation, explanation, clinician summary,
model metadata, request ID, and assessment ID.

The clinician review page reads the latest assessment result and intake from
Streamlit session state. It shows a compact review snapshot, chief complaint,
demographics, vitals, recommendation, explanation, clinician handoff summary,
and the required decision-support disclaimer. Saving a review calls
`POST /clinician-review`; success is shown only from the backend response and
stores the response in `st.session_state["latest_clinician_review"]`.

Accepting the recommendation submits the model/safety final ESI. Overriding
requires a clinician final ESI from 1 to 5 and a reason that is stored in the
audit trail.

The deployed model provides ESI 3-5 decision-support recommendations from the
structured intake fields. Clinician final override intentionally supports ESI
1-5, because the final triage decision remains under clinician judgment. This
human-in-the-loop workflow lets clinicians escalate when additional clinical
context, safety concerns, or patient presentation justify a different final ESI;
the override reason is required and saved to the audit trail.

The dashboard reads DB-backed workflow history from `GET /dashboard/summary`.
It shows summary cards, final ESI distribution, review status, override count,
recent assessments, and filters for status, ESI, clinician decision, and search
by chief complaint or assessment ID. It does not show fake rows when the
database is empty.

The assessment detail page reads `GET /assessments/{assessment_id}`. It can load
from a dashboard-selected assessment ID, manual input, or the latest prediction
session state. Detail view shows intake, vitals, latest model prediction,
probabilities, safety rules, recommendation, explanation, clinician summary,
latest clinician review, override reason or review note, and audit timeline
events. The model predicts ESI 3-5, while clinician final ESI can be 1-5 through
review; overrides require a reason and are shown as audit-visible workflow
events.

If the backend is unavailable, the sidebar shows:

```bash
python -m uvicorn app.backend.api.main:app --reload --port 8001
```

If the backend returns `model_loaded: false`, the UI clearly labels the output as
a fallback contract response.

# Dashboard And Assessment Detail UX Audit

Phase 7A compares Khushal's archived Streamlit prototype with the current
TriageAI dashboard/detail surface before implementation. This is an audit only;
it does not change frontend behavior, backend contracts, model artifacts, or
prediction logic.

## Files Inspected

Legacy Khushal reference:

- `legacy/khushal_reference/README.md`
- `legacy/khushal_reference/front_end/app.py`
- `legacy/khushal_reference/front_end/form_page.py`
- `legacy/khushal_reference/front_end/result_page.py`
- `legacy/khushal_reference/front_end/database.py`
- `legacy/khushal_reference/front_end/db_helper.py`
- `legacy/khushal_reference/front_end/ui_helpers.py`

Current project:

- `app/frontend/streamlit_app/pages/05_Dashboard.py`
- `app/frontend/streamlit_app/pages/06_Assessment_Detail.py`
- `app/frontend/streamlit_app/services/api_client.py`
- `app/frontend/streamlit_app/api_client.py`
- `app/frontend/streamlit_app/components/dashboard_cards.py`
- `app/backend/api/routes/dashboard.py`
- `app/backend/api/routes/assessments.py`
- `app/backend/api/routes/reports.py`
- `app/backend/db/models.py`
- `app/backend/db/repositories.py`
- `app/backend/schemas/dashboard.py`
- `app/backend/schemas/assessment.py`
- `docs/api_contract.md`
- `docs/frontend.md`

## Legacy Dashboard And Detail UX Summary

Khushal's app does not include a separate dashboard page. It uses a monolithic
three-step Streamlit flow: authentication, intake form, and result page. The
dashboard-adjacent ideas are embedded in persistence, result presentation, and
report generation rather than a browsable list of assessments.

The legacy persistence layer stores users and assessments in SQLite through
`database.py` and `db_helper.py`. Saved assessment fields include demographics,
chief complaint, vitals, predicted triage level, final triage level, confidence,
rule outputs, model outputs, final source, and timestamps. This is useful as a
conceptual precedent for a current assessment table, but the old raw SQLite
helpers should not be carried forward.

The legacy result page is highly structured. It shows a hero result card,
recommended action, probability breakdown, input summary, decision-pathway
explanation, clinician identity, disclaimers, and PDF/email report generation.
It also uses card-like containers, compact metric blocks, visual status chips,
and expanders for detail. These patterns are relevant for a modern assessment
detail page.

No legacy manual clinician review status, accept/override workflow, audit trail
viewer, search, filter, delete, or dashboard table was found. Rule overrides are
system-generated rather than clinician-entered.

## Current Dashboard And Detail UX Summary

The current Streamlit pages are placeholders:

- `pages/05_Dashboard.py` only renders `st.title("Dashboard")`.
- `pages/06_Assessment_Detail.py` only renders `st.title("Assessment Detail")`.
- `components/dashboard_cards.py` is also a placeholder.

The backend has a stronger foundation than the frontend currently exposes:

- `GET /dashboard/summary` returns total assessments, pending reviews,
  completed reviews, high-risk flags, ESI distribution, recent assessments, and
  `is_placeholder: false`.
- Recent assessment rows include assessment ID, patient ID, chief complaint,
  status, created timestamp, and latest final ESI.
- `GET /assessments/{assessment_id}` returns persisted intake and assessment
  status fields.
- The database stores predictions, clinician reviews, audit logs, and report
  metadata, but current assessment detail response does not yet join these into
  one detail payload.
- The report endpoint queues metadata only and still returns
  `is_placeholder: true`; PDF generation is not active in the current backend.

The current result and clinician review pages already establish the desired
Phase 7 visual language: restrained clinical cards, ESI-only terminology,
decision-support disclaimers, safety-rule visibility, and human-in-the-loop
review wording.

## Legacy Vs Current Comparison

Dashboard cards:
Legacy has no dashboard, but uses compact result cards and metric-like panels.
Current backend returns enough counts for dashboard cards, while frontend cards
are not implemented.

Assessment table:
Legacy stores assessment rows but does not show a patient or assessment list.
Current backend returns `recent_assessments`, which is a natural table source.

Filters and search:
Legacy has no filter/search UX. Phase 7B can add client-side search by chief
complaint or assessment ID, plus status and final ESI filters, without implying
clinical prioritization beyond the stored data.

Final ESI visibility:
Legacy makes final CTAS highly visible on the result page. Current dashboard
summary includes final ESI per recent assessment when a prediction exists.
Phase 7B should show final ESI as a prominent but compact table column and
detail-page badge.

Reviewed/unreviewed status:
Legacy has no explicit review status. Current assessment status supports
`pending_review`, `needs_review`, and `review_completed`; dashboard and detail
pages should make this state visible.

Clinician decision and override reason:
Legacy has no clinician-entered override flow. Current database stores review
action, final ESI, override reason, notes, clinician ID, and timestamp, but the
current public detail contract does not surface them. Phase 7B should expose
this information carefully if backend detail support is added.

Audit trail visibility:
Legacy report text describes system decision logic but does not show a saved
audit timeline. Current backend writes audit logs for clinician review. Phase 7B
should include audit visibility as read-only history, not as a blame-oriented
log.

Detail page flow:
Legacy detail is essentially the result page: hero result, recommended action,
probabilities, inputs, explanation, report/export. Current detail page should
become the persisted version of that experience, with review status and audit
context added.

## Continuity Decisions

- Carry forward the simple clinical dashboard feeling: calm cards, clear
  labels, compact metrics, and scan-friendly tables.
- Carry forward the result-to-detail structure: final triage signal first,
  then patient/intake context, vitals, probability/model context, explanation,
  clinician summary, and report readiness.
- Carry forward report/export as a visible future workflow, but label queued or
  placeholder report states honestly.
- Carry forward clinician identity and timestamp concepts where available.
- Carry forward the explicit disclaimer that the system supports, and does not
  replace, clinician judgment.
- Keep review status visible so pending records do not look finished.

## Modernization Decisions

- Use current FastAPI and SQLAlchemy data rather than legacy SQLite helpers.
- Use ESI-only language. Do not use CTAS, KTAS, old model names, or legacy
  response-time claims.
- Keep dashboard layout operational, not marketing-like: summary cards at top,
  filters/search next, recent assessment table below.
- Avoid a monolithic Streamlit file. Prefer API-client helpers and small
  components for dashboard cards, status chips, and detail sections.
- Do not add delete behavior in Phase 7B unless there is a clear backend audit
  and authorization story.
- Treat export/report controls as queued metadata until real PDF generation is
  implemented.
- Avoid synthetic metrics. Only show values returned by the backend.

## Phase 7B Implementation Checklist

- Add frontend API-client helpers:
  `get_dashboard_summary()` and `get_assessment_detail(assessment_id)`.
- Build `pages/05_Dashboard.py` into a real page with:
  total assessments, pending reviews, completed reviews, high-risk flags, ESI
  distribution, recent assessment table, empty state, backend error state, and
  decision-support disclaimer.
- Add client-side search/filter controls for recent assessments:
  assessment ID, chief complaint, review status, and final ESI.
- Make each recent assessment row actionable:
  select an assessment ID, store it in session state, and navigate to
  Assessment Detail.
- Build `pages/06_Assessment_Detail.py` with:
  selected/manual assessment ID loading, empty state, intake summary, vitals,
  status, timestamps, and navigation back to Dashboard.
- Show final ESI, prediction context, clinician decision, override reason, and
  audit history only when backend support is present.
- If backend detail is extended, add read-only latest prediction, latest
  clinician review, and audit timeline fields to the assessment detail contract.
- Keep all dashboard/detail wording decision-support only.
- Keep report generation honest: queued metadata is not a downloadable PDF.
- Add frontend API-client tests for dashboard and assessment detail helpers.
- Add backend tests if the assessment detail contract is extended.

## Files Likely To Change In Phase 7B

- `app/frontend/streamlit_app/services/api_client.py`
- `app/frontend/streamlit_app/api_client.py`
- `app/frontend/streamlit_app/pages/05_Dashboard.py`
- `app/frontend/streamlit_app/pages/06_Assessment_Detail.py`
- `app/frontend/streamlit_app/components/dashboard_cards.py`
- `app/frontend/streamlit_app/assets/styles.py`
- `app/backend/api/routes/assessments.py`
- `app/backend/db/repositories.py`
- `app/backend/schemas/assessment.py`
- `tests/frontend/test_api_client.py`
- `tests/backend/test_assessments_db.py`
- `docs/api_contract.md`
- `docs/frontend.md`

## Safety And Responsible AI Wording

Dashboard and detail pages should consistently use language such as:

- "Decision-support output"
- "Clinician review status"
- "Final ESI after model/safety logic and clinician review"
- "Override reason documented in audit trail"
- "This tool is for clinical decision-support workflow testing only and is not
  a diagnosis or a substitute for clinician judgment."

Avoid language such as:

- "AI diagnosis"
- "AI decision"
- "Corrected model"
- "Confirmed diagnosis"
- "Automatic triage assignment"
- "CTAS" or "KTAS"

## Bottom Line

Khushal's legacy project should influence the feel of the dashboard/detail work
through clear clinical cards, strong result summaries, explainability sections,
input summaries, and report continuity. The current implementation should be
more production-like: backend-driven, ESI-only, searchable, review-status aware,
and explicit about human clinician responsibility.

# Report Generation Audit

Phase 8A defines the PDF/report content and UX plan before implementation.
This is an audit-only planning artifact. It does not change backend report
generation, frontend controls, model artifacts, prediction logic, or clinician
review behavior.

The report should feel like a continuation of the current TriageAI workflow:
structured intake, model-backed ESI decision support, safety-rule visibility,
human clinician review, and audit-ready documentation. It must remain ESI-only
and decision-support only.

## Files Inspected

Legacy Khushal reference:

- `legacy/khushal_reference/README.md`
- `legacy/khushal_reference/front_end/result_page.py`
- `legacy/khushal_reference/front_end/form_page.py`
- `legacy/khushal_reference/front_end/triage_utils.py`
- `legacy/khushal_reference/front_end/config.py`
- `legacy/khushal_reference/front_end/database.py`
- `legacy/khushal_reference/front_end/db_helper.py`

Current backend:

- `app/backend/api/routes/reports.py`
- `app/backend/schemas/report.py`
- `app/backend/services/pdf_service.py`
- `app/backend/api/routes/assessments.py`
- `app/backend/api/routes/clinician_review.py`
- `app/backend/db/models.py`
- `app/backend/db/repositories.py`
- `app/backend/schemas/assessment.py`
- `app/backend/schemas/prediction.py`
- `app/backend/services/care_routing_service.py`
- `app/backend/services/explanation_service.py`
- `app/backend/services/audit_service.py`
- `tests/backend/test_reports.py`

Current frontend:

- `app/frontend/streamlit_app/pages/03_Result.py`
- `app/frontend/streamlit_app/pages/04_Clinician_Review.py`
- `app/frontend/streamlit_app/pages/05_Dashboard.py`
- `app/frontend/streamlit_app/pages/06_Assessment_Detail.py`
- `app/frontend/streamlit_app/services/api_client.py`
- `app/frontend/streamlit_app/components/probability_chart.py`
- `app/frontend/streamlit_app/components/result_card.py`
- `app/frontend/streamlit_app/components/summary_card.py`

Supporting docs:

- `docs/dashboard_assessment_detail_ux_audit.md`
- `docs/clinician_review_ux_audit.md`
- `docs/safety_rules.md`
- `docs/responsible_ai.md`

## Legacy Report Ideas

Khushal's archived Streamlit app includes a substantial ReportLab PDF concept in
`legacy/khushal_reference/front_end/result_page.py`. The useful ideas are:

- A professional A4 report layout with a branded header and generated timestamp.
- A prominent final triage result block.
- Patient/intake details and vital-sign summary.
- Probability breakdown table.
- Explainable decision pathway with rule evaluation, model prediction, and final
  result narrative.
- Clinician/session identity in the header/footer when available.
- A clinical disclaimer near the end of the report.
- Optional email attachment workflow.

These ideas should be treated as UX inspiration only. The implementation should
not copy legacy code directly because the old report is CTAS-oriented, uses old
response-time labels, references old model outputs, and belongs to a monolithic
Streamlit prototype rather than the current FastAPI/SQLAlchemy architecture.

## Current Report Behavior

The current report route is intentionally a placeholder:

- `POST /reports/generate` accepts `assessment_id` and `include_audit`.
- The route verifies that the assessment exists.
- It creates a `reports` metadata row with `report_status="queued"`,
  `download_url=None`, and the requested `include_audit` value.
- The response returns `is_placeholder=True` and the message
  "Report metadata queued. No PDF file is generated yet."
- `app/backend/services/pdf_service.py` is an empty placeholder.
- `tests/backend/test_reports.py` verifies metadata creation and 404 behavior.

There is no current frontend API helper or Streamlit button for report
generation/download. Phase 8B should add those only after the backend can return
a real PDF or an honest generated-file response.

## Data Available Today

`GET /assessments/{assessment_id}` already returns most of the report-ready
payload:

- Assessment ID, patient ID, assessment status, created/updated timestamps.
- Intake snapshot: age, sex, chief complaint, symptom duration, pain score,
  temperature, heart rate, respiratory rate, blood pressure, oxygen saturation,
  consciousness level, pregnancy, arrival mode, and additional context.
- Latest prediction: model version, model loaded flag, predicted ESI, model
  final ESI, confidence score, ESI probabilities, safety rules, final source,
  recommendation, explanation, clinician summary, placeholder flag, and
  prediction timestamp.
- Latest clinician review: review ID, clinician ID, action, clinician final
  ESI, override reason, review note, reviewed flag, and review timestamp.
- Audit trail: assessment creation, prediction generation, and clinician review
  audit log entries.

The Assessment Detail page already presents these sections in a report-like
order, making it the best frontend reference for Phase 8B.

## Final Report Content Plan

The final PDF should include the following sections in this order:

1. Report title:
   "TriageAI ESI Clinical Intake Report" or "TriageAI ESI Decision-Support
   Report".
2. Generated timestamp:
   Use timezone-aware timestamp formatting. Prefer UTC or clearly label the
   server/local timezone.
3. Identifiers:
   Assessment ID, report ID, patient ID if present, prediction ID if present,
   review ID if present.
4. Patient/intake snapshot:
   Age, sex, chief complaint, symptom duration, pain score, vitals, pregnancy,
   arrival mode, consciousness level, and additional context. Missing values
   should display as "Not documented".
5. Model prediction:
   Acuity scale `ESI`, model version, model loaded status, predicted ESI, model
   final ESI, confidence score, final source, and prediction timestamp.
6. ESI probabilities:
   Show ESI 3, ESI 4, and ESI 5 probabilities from the deployed model output.
   Do not invent ESI 1 or ESI 2 model probabilities.
7. Safety rules:
   List triggered safety rules with rule ID and message. If none triggered,
   state "No safety-rule escalation triggered for this result."
8. Recommendation:
   Use the backend recommendation text without strengthening it into a clinical
   order.
9. Clinical explanation:
   Use the backend explanation text, preserving decision-support wording.
10. Clinician summary:
   Include the generated handoff summary.
11. Clinician review:
   Show status, clinician ID, decision, clinician final ESI, reviewed timestamp,
   override reason, and review note.
12. Audit trail:
   Include assessment creation, prediction generation, and clinician review
   events when `include_audit=True`. Keep details concise and readable.
13. Decision-support disclaimer:
   Close with a clear statement that the report supports clinician review and is
   not a diagnosis or autonomous clinical decision.

## Content To Exclude

The final PDF must not include:

- Diagnosis language such as "AI diagnosis", "diagnosed as", or disease labels
  inferred from symptoms.
- Autonomous AI decision wording such as "AI decided", "AI assigned", "AI
  approved", or "final decision by AI".
- CTAS or KTAS labels, response-time tables, or legacy CTAS/KTAS names.
- Fake metrics, synthetic validation claims, or demo-only performance numbers.
- Raw model internals that confuse non-technical readers, such as feature
  vector dumps, encoded column names, threshold files, pickled model names, or
  implementation-only artifacts.
- Old PyCaret/pickle model details from `legacy/khushal_reference/`.
- Any wording that implies the report replaces clinician judgment.

## Safety Wording

Recommended standard disclaimer:

> This report is generated by TriageAI for clinical decision-support workflow
> review. It is not a diagnosis, treatment recommendation, or substitute for the
> judgment of a qualified clinician. The clinician remains responsible for the
> final ESI assignment and care-routing decision.

Recommended safety-rule wording:

- "Safety-rule escalation visible."
- "Safety rules are conservative workflow safeguards and are not diagnostic."
- "No safety-rule escalation triggered for this result."
- "Clinician review is required before acting on this output."

Recommended clinician-review wording:

- "Clinician final ESI"
- "Clinician decision"
- "Override reason documented in audit trail"
- "Model/safety output accepted by clinician"
- "Model/safety output overridden by clinician"

Avoid:

- "AI final decision"
- "Confirmed diagnosis"
- "Corrected diagnosis"
- "Patient should be treated as..."
- "Guaranteed acuity"
- "CTAS", "KTAS", or mixed acuity terminology

## UX Decisions

- The report should match the current result/detail visual hierarchy: final ESI
  and identifiers first, then intake context, model/safety details, clinician
  review, and audit/disclaimer.
- The PDF should be compact and readable for demo review. Prefer tables,
  labeled fields, and short paragraphs over dense raw JSON.
- Use "Not documented" for missing optional clinical fields.
- Show placeholder/fallback status honestly if a stored prediction was generated
  without the real model.
- If clinician review is pending, the report should clearly say "Pending
  clinician review" and avoid making the workflow look complete.
- A generated report should be downloadable from Assessment Detail after Phase
  8B, and optionally from the Result or Dashboard flow if the assessment has
  persisted prediction data.

## Phase 8B Implementation Checklist

- Add a real PDF service in `app/backend/services/pdf_service.py`.
- Build a report payload from the same assessment-detail data shape used by
  `GET /assessments/{assessment_id}` to avoid duplicate field logic.
- Decide whether `POST /reports/generate` returns raw PDF bytes, a download URL,
  or metadata plus a separate download endpoint.
- Update `ReportResponse` to distinguish queued, generated, and failed states.
- Persist generated report status and `download_url` or file reference in the
  `reports` table.
- Keep `include_audit` behavior: include audit events only when requested.
- Add backend tests for successful PDF generation, unknown assessment, missing
  prediction, pending clinician review, audit included/excluded, and PDF content
  safety wording.
- Add a frontend API helper for report generation/download.
- Add a report action to Assessment Detail once a real generated PDF exists.
- Show clear loading, success, download, and backend-error states in Streamlit.
- Update API/frontend docs after implementation.
- Keep all wording ESI-only and decision-support only.

## Files Likely To Change In Phase 8B

- `app/backend/api/routes/reports.py`
- `app/backend/schemas/report.py`
- `app/backend/services/pdf_service.py`
- `app/backend/api/routes/assessments.py`
- `app/backend/db/repositories.py`
- `app/backend/db/models.py`
- `app/frontend/streamlit_app/services/api_client.py`
- `app/frontend/streamlit_app/api_client.py`
- `app/frontend/streamlit_app/pages/06_Assessment_Detail.py`
- `app/frontend/streamlit_app/pages/03_Result.py`
- `app/frontend/streamlit_app/pages/05_Dashboard.py`
- `tests/backend/test_reports.py`
- `tests/frontend/test_api_client.py`
- `docs/api_contract.md`
- `docs/frontend.md`

## Report Content Decisions

- Use ESI as the only acuity scale in the report.
- Include only model probabilities that exist in the current model output.
- Treat safety rules as transparent review flags, not diagnoses.
- Treat the model final ESI as model/safety output, not as the final clinical
  decision when a clinician review exists.
- Treat clinician final ESI as the documented human review outcome.
- Include audit events for demo and portfolio value, but keep them readable.
- Phase 8B should replace the placeholder report route with real generated PDF
  output while preserving decision-support wording.

## Phase 8B Implementation Notes

- Generate PDFs under `reports/generated/`.
- Do not commit generated PDF artifacts.
- Prefer `GET /reports/{report_id}/download` over exposing arbitrary file paths
  as a download mechanism.
- Assessment Detail should be the primary frontend entry point for generating
  an assessment report.

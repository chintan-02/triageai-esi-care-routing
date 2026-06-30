# Clinician Review UX Audit

## Scope

This audit compares clinician-review-adjacent workflows in Khushal's archived
project with the current TriageAI FastAPI and Streamlit implementation. It is a
documentation-only planning artifact for Phase 6B.

The review workflow must remain ESI-only, decision-support only, and clinician
judgment centered. Legacy CTAS/KTAS terminology, model code, local database
patterns, PyCaret/pickle concepts, and diagnostic claims must not be copied into
active modules.

## Legacy UX Files Inspected

- `legacy/khushal_reference/front_end/app.py`
- `legacy/khushal_reference/front_end/auth_page.py`
- `legacy/khushal_reference/front_end/form_page.py`
- `legacy/khushal_reference/front_end/result_page.py`
- `legacy/khushal_reference/front_end/ui_helpers.py`
- `legacy/khushal_reference/front_end/config.py`
- `legacy/khushal_reference/front_end/database.py`
- `legacy/khushal_reference/front_end/db_helper.py`
- `legacy/khushal_reference/front_end/logic.py`
- `legacy/khushal_reference/front_end/triage_utils.py`
- `legacy/khushal_reference/README.md`

## Current UX And Backend Files Inspected

- `app/frontend/streamlit_app/pages/03_Result.py`
- `app/frontend/streamlit_app/pages/04_Clinician_Review.py`
- `app/frontend/streamlit_app/pages/05_Dashboard.py`
- `app/frontend/streamlit_app/pages/06_Assessment_Detail.py`
- `app/frontend/streamlit_app/components/result_card.py`
- `app/frontend/streamlit_app/components/summary_card.py`
- `app/frontend/streamlit_app/services/api_client.py`
- `app/backend/api/routes/clinician_review.py`
- `app/backend/schemas/clinician_review.py`
- `app/backend/db/repositories.py`
- `tests/backend/test_clinician_review.py`

## Legacy Clinician Review UX Summary

The legacy app does not contain a separate accept/override clinician review
form. Review is implied through the result page, clinician/session identity,
report generation, and language that repeatedly says the attending clinician is
responsible for the final triage decision.

Important review-adjacent patterns in the legacy UI:

- Result page starts from a strong final triage hero card.
- Clinician identity is shown near the result when the user is signed in.
- Guest sessions are explicitly labeled and treated as less persistent.
- The result page exposes rule/model decision values in an explainable
  "decision pathway" section.
- PDF report generation turns result details into a clinician-facing artifact.
- Email report support is available for signed-in users.
- Saved assessment records include prediction, final result, confidence, and
  final source fields.
- The result page includes clinical disclaimer language near the report output.

The legacy app's strongest useful concept is not a literal review form; it is
the idea that the model output becomes a clinician-facing review artifact with
identity, explanation, saved result metadata, and report continuity.

## Current Clinician Review UX Summary

The current frontend result page displays backend-generated ESI output clearly:
final ESI, predicted ESI, confidence, probabilities, safety review,
recommendation, explanation, clinician handoff summary, and model/audit details.

The current clinician review page is a placeholder:

- `app/frontend/streamlit_app/pages/04_Clinician_Review.py` only renders the
  title "Clinician Review".

The current backend review contract is already meaningful:

- `POST /clinician-review` accepts `assessment_id`, `clinician_id`, `action`,
  optional `final_esi`, `override_reason`, and `notes`.
- `action` supports `accept`, `override`, and `needs_review`.
- Override requires `override_reason`.
- Unknown assessment returns `404`.
- Successful review persists a clinician review row.
- Assessment status updates to `review_completed` for `accept` or `override`.
- Assessment status updates to `needs_review` for `needs_review`.
- An audit log is created with actor, action, assessment ID, and request details.

The current dashboard and assessment detail frontend pages are placeholders, but
the backend dashboard summary already reads assessment counts, review status,
ESI distribution, high-risk flags, and recent assessments.

## Comparison

### How Review Starts

Legacy:
- Review starts after model output on the result page.
- The result page is the clinical review surface and report source.
- There is no explicit accept/override action.

Current:
- Result page holds the latest prediction in Streamlit session state.
- Backend has a separate review endpoint.
- Frontend review page is not connected yet.

Phase 6B direction:
- Start review from the result page with a clear "Open Clinician Review" action.
- Carry `assessment_id`, final ESI, predicted ESI, safety state, and summary
  into the review page.
- Keep the review page separate enough to make the clinician action deliberate.

### What The Clinician Sees Before Deciding

Legacy:
- Final triage hero, confidence, probability breakdown, patient/vitals summary,
  decision pathway, and disclaimer.

Current:
- Result page already shows final/predicted ESI, probabilities, safety rules,
  recommendation, explanation, summary, and model details.

Phase 6B direction:
- The review page should restate the essential result in a compact review card:
  final ESI, predicted ESI, confidence, safety-rule status, and clinician
  handoff summary.
- It should include a link or affordance back to the full result page.

### Accept Model Result Flow

Legacy:
- No explicit accept button.
- Report/download/email implies clinician acknowledgement, but does not persist
  a review action.

Current:
- Backend supports `action="accept"` and stores review_completed status.

Phase 6B direction:
- Add an "Accept final ESI" option.
- Require clinician identifier before submitting.
- Optionally allow notes.
- Submit to `POST /clinician-review`.
- Show success with review ID and updated assessment status.

### Override Final ESI Flow

Legacy:
- Rule overrides are system-generated, not clinician-entered.
- No manual final triage override UX was found.

Current:
- Backend supports `action="override"` with required `override_reason` and
  optional `final_esi`.

Phase 6B direction:
- Add an "Override final ESI" option.
- Require clinician-selected final ESI and override reason.
- Make reason field prominent and non-optional.
- Warn that override is a clinician decision and will be audited.
- Explain that the deployed model predicts ESI 3-5, while clinician final
  override supports ESI 1-5 so additional clinical context or safety concerns
  can be escalated and documented.
- Do not let the UI imply the model is being retrained or corrected.

### Needs Review Flow

Legacy:
- Guest/session and disclaimer language imply review responsibility, but no
  explicit "needs review" status exists.

Current:
- Backend supports `action="needs_review"` and updates assessment status.

Phase 6B direction:
- Add "Mark as needs review" for cases where clinician cannot finalize.
- Require or strongly encourage notes.
- Dashboard should surface these records as pending/needs review.

### Required Note Or Reason

Legacy:
- Report text and PDF contain narrative explanations, but no clinician note
  input pattern was found.

Current:
- Backend requires `override_reason` for override.
- `notes` are optional for all actions.

Phase 6B direction:
- Keep override reason required.
- Add optional notes for accept.
- Encourage notes for needs_review.
- Make wording concise and audit-aware.

### Audit Trail Creation

Legacy:
- Assessments/results are saved with prediction metadata and final source.
- There is no discrete audit log table for review actions.

Current:
- Backend writes `AuditLog` records on clinician review.

Phase 6B direction:
- Surface audit creation in the UI after submit:
  "Review saved and audit log recorded."
- Show review ID, assessment ID, clinician ID, action, and status.
- Keep full audit-log browsing for a later phase unless required.

### Result And Dashboard Update

Legacy:
- Saved assessment/report continuity exists, but no separate dashboard page was
  found in active legacy frontend files.

Current:
- Backend status updates support dashboard counts.
- Frontend dashboard page is placeholder.

Phase 6B direction:
- After review submit, provide navigation to Dashboard and Assessment Detail.
- Dashboard should later show pending reviews, completed reviews, high-risk
  flags, ESI distribution, and recent assessments.

### Report/PDF Readiness

Legacy:
- PDF report generation is a major result-page feature.
- Email report is available for signed-in users.

Current:
- Backend `/reports/generate` stores report metadata only.
- Frontend does not yet expose report generation.

Phase 6B direction:
- Carry forward report continuity as a secondary action:
  "Generate report metadata" after review completion.
- Do not build real PDF/email in Phase 6B unless explicitly requested.
- Avoid implying a downloadable clinical PDF exists until backend supports it.

### Safety Disclaimer Placement

Legacy:
- Disclaimer appears in the result/report path and states the system supports,
  not replaces, clinician judgment.

Current:
- Result page disclaimer is visible.
- Review page is placeholder.

Phase 6B direction:
- Add a compact disclaimer to the review page near the submit button.
- Repeat that the clinician action is the recorded decision, and the model is
  decision support only.

## Carry Forward From Khushal

- Review begins from a strong result page rather than a disconnected form.
- Clinician/session identity should be visible near review actions.
- The result explanation should remain available during review.
- Saved assessment and report continuity should be obvious.
- The final decision should be framed as clinician-owned.
- Report-ready wording and audit metadata should be easy to inspect.
- Clinical blue card styling and compact status chips can be reused visually.

## Do Not Carry Forward

- CTAS/KTAS labels or old triage level names.
- Legacy model claims or old model file names.
- Diagnostic language.
- Any wording that makes the model appear to make the final clinical decision
  without clinician oversight.
- Monolithic Streamlit router patterns.
- Legacy SQLite/auth helper code.
- PDF/email behavior that bypasses current backend report contracts.
- Old rule names that do not map to current ESI safety rules.

## Continuity Decisions

- Keep result-to-review as the main clinician journey.
- Preserve the legacy "clinician-facing artifact" feel: final result, summary,
  explanation, metadata, and report/audit readiness.
- Keep review actions visually close to the model output but deliberate enough
  to avoid accidental submission.
- Use ESI-only language throughout the active UI.
- Carry forward the idea of clinician identity, but implement it through current
  backend `clinician_id` request data rather than legacy auth code.

## Modernization Decisions

- Use the current FastAPI endpoint as the source of truth:
  `POST /clinician-review`.
- Use the existing `assessment_id` returned by `/predict`.
- Add a frontend API client function for review submission in Phase 6B.
- Use Streamlit multi-page navigation instead of rebuilding the old custom
  router.
- Keep model/audit details in compact expanders where possible.
- Make review success/failure states explicit and friendly.

## Safety And Responsible AI Decisions

- The review page must say the model output is decision-support only.
- The submit action must clearly record a clinician review decision.
- Override must require a reason and final ESI.
- Needs-review should not be styled as failure; it is a safe workflow state.
- Safety-rule overrides should remain visible during review.
- The UI should never imply the model diagnosed the patient.
- The UI should never suggest ignoring emergency symptoms.
- Audit logging should be described as a transparency feature, not a punitive
  feature.

## Phase 6B Implementation Checklist

- Add `submit_clinician_review(payload)` to the Streamlit API client.
- Expand `pages/04_Clinician_Review.py` from placeholder into a real review
  page.
- Pull latest prediction/result from `st.session_state`.
- If no result exists, show a friendly empty state with navigation to New
  Assessment.
- Display compact review context:
  final ESI, predicted ESI, confidence, final source, safety status,
  recommendation, and clinician summary.
- Add clinician ID input.
- Add action selection:
  `accept`, `override`, `needs_review`.
- For accept:
  optional notes, submit final ESI from backend result.
- For override:
  required final ESI selection and required override reason.
- For needs_review:
  notes strongly encouraged.
- Submit to backend `/clinician-review`.
- On success, show review ID, assessment ID, new status, and audit-log message.
- Store review response in `st.session_state`.
- Add navigation to Dashboard and Assessment Detail.
- Keep disclaimer visible near submit.
- Add API-client tests without requiring a live backend.

## Files Likely To Change In Phase 6B

- `app/frontend/streamlit_app/services/api_client.py`
- `app/frontend/streamlit_app/api_client.py`
- `app/frontend/streamlit_app/pages/04_Clinician_Review.py`
- `app/frontend/streamlit_app/pages/03_Result.py`
- `app/frontend/streamlit_app/pages/05_Dashboard.py`
- `app/frontend/streamlit_app/pages/06_Assessment_Detail.py`
- `app/frontend/streamlit_app/components/layout.py`
- `app/frontend/streamlit_app/components/result_card.py`
- `app/frontend/streamlit_app/components/summary_card.py`
- `tests/frontend/test_api_client.py`
- `docs/frontend.md`

Backend behavior likely does not need to change for the first Phase 6B UI pass.
If backend changes become necessary later, they should be limited to response
shape or read endpoints needed by the UI, not model inference or artifacts.

## Bottom Line

Khushal's legacy project should inform the review experience as a clinical
handoff and report/audit workflow, not as code to copy. Phase 6B should turn the
current placeholder review page into a deliberate clinician decision surface:
review model output, accept or override with reason, mark needs-review when
appropriate, write the audit trail, and keep clinician judgment visibly central.

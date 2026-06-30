# UI Reference Audit

## Scope

This audit compares Khushal's archived Streamlit UI under
`legacy/khushal_reference/front_end/` with the current TriageAI Streamlit app
under `app/frontend/streamlit_app/`. The purpose is to guide Phase 5B frontend
polish while preserving ESI-only terminology and the current FastAPI-backed
architecture.

This audit is about UI/UX continuity only. Legacy model code, PyCaret code,
old triage logic, old model names, CTAS/KTAS terminology, and old database code
must not be copied into active modules.

## Legacy UI Files Inspected

- `legacy/khushal_reference/front_end/app.py`
- `legacy/khushal_reference/front_end/auth_page.py`
- `legacy/khushal_reference/front_end/form_page.py`
- `legacy/khushal_reference/front_end/result_page.py`
- `legacy/khushal_reference/front_end/ui_helpers.py`
- `legacy/khushal_reference/front_end/config.py`
- `legacy/khushal_reference/front_end/logic.py`
- `legacy/khushal_reference/front_end/triage_utils.py`
- `legacy/khushal_reference/front_end/db_helper.py`

## Current UI Files Inspected

- `app/frontend/streamlit_app/Home.py`
- `app/frontend/streamlit_app/pages/02_New_Assessment.py`
- `app/frontend/streamlit_app/pages/03_Result.py`
- `app/frontend/streamlit_app/pages/04_Clinician_Review.py`
- `app/frontend/streamlit_app/pages/05_Dashboard.py`
- `app/frontend/streamlit_app/pages/06_Assessment_Detail.py`
- `app/frontend/streamlit_app/components/intake_form.py`
- `app/frontend/streamlit_app/components/layout.py`
- `app/frontend/streamlit_app/components/result_card.py`
- `app/frontend/streamlit_app/components/probability_chart.py`
- `app/frontend/streamlit_app/components/dashboard_cards.py`
- `app/frontend/streamlit_app/components/summary_card.py`
- `app/frontend/streamlit_app/components/audio_recorder.py`
- `app/frontend/streamlit_app/assets/styles.py`
- `app/frontend/streamlit_app/services/api_client.py`

## Summary Of Khushal UI Style

The legacy frontend is a custom-routed Streamlit application with a polished
clinical SaaS feel. It hides much of the default Streamlit chrome, uses a
centered 780px layout, and relies heavily on custom HTML/CSS cards. The visual
language is blue-forward, with soft white cards, subtle shadows, rounded
containers, status chips, thin dividers, and a fixed top accent bar.

The intake flow is split into clear sections: patient information, chief
complaint, vital signs, warning chips, and submit action. Vital signs are
presented as compact clinical tiles with current value, unit, reference range,
normal/abnormal status, and optional N/A handling. The old UI also includes
voice input for chief complaint and a guest/session banner.

The result page is dense and report-like. It includes a hero triage result
card, confidence display, probability breakdown, explanatory decision pathway,
patient/vital summary, PDF report generation, email report support, and a
clinical disclaimer. Its strongest UX idea is not any old model logic, but the
layered explanation: rules first, model second, final decision third.

## Current UI Style

The current frontend is cleaner and more modular. It uses Streamlit's native
multi-page navigation, a `services/api_client.py` client, and distinct component
files for intake, layout, probability display, and result card rendering. This
is a better architecture than the legacy monolithic router because it maps
directly to the current FastAPI backend.

The current intake page collects backend-compatible fields and submits to
`POST /predict`. The result page displays final ESI, predicted ESI, confidence,
final source, probabilities, safety rules, recommendation, explanation,
clinician summary, model metadata, and the decision-support disclaimer.

The current visual style is restrained and professional, but still sparse. It
does not yet carry forward the legacy app's distinctive top navigation, section
badges, vital-sign tiles, result hero treatment, or report-style clinical
summary hierarchy.

## Comparison

### Sidebar And Navigation

Legacy:
- Uses a custom sticky top nav with TriageAI brand, session status, and sign-out.
- Hides Streamlit's sidebar and routes pages through `st.session_state.page`.
- Feels more like a single clinical workflow.

Current:
- Uses Streamlit's native multi-page sidebar.
- Adds backend/model/database status in the sidebar.
- Easier to maintain and more transparent for a capstone/demo workflow.

Continuity decision:
- Keep Streamlit's native page structure.
- Carry forward a lightweight top status/header band for brand and workflow
  continuity.
- Keep the current backend readiness sidebar because it is valuable and did not
  exist in the old model-local app.

### Page Titles

Legacy:
- Uses compact section headers with a colored vertical accent and uppercase
  micro-labels.
- "New Assessment" and "Assessment Result" are strong familiar anchors.

Current:
- Uses direct Streamlit titles and captions.

Continuity decision:
- Keep page names: `New Assessment`, `Assessment Result`, `Clinician Review`,
  `Dashboard`, and `Assessment Detail`.
- Add legacy-inspired section labels and subtle header bands, but use ESI
  wording only.

### Intake Flow

Legacy:
- Strong stepped flow: patient info, chief complaint, vital signs, abnormal
  warning chips, submit.
- Vital inputs are polished clinical tiles with normal ranges and N/A support.
- Chief complaint voice input is present, but tied to legacy Azure code.

Current:
- Backend-compatible form with patient demographics, chief complaint, vitals,
  safety context, and additional context.
- Simpler two-column layout with standard inputs.

Continuity decision:
- Preserve the current payload contract.
- Upgrade visual grouping to mirror the old patient/chief complaint/vitals/safety
  sections.
- Consider legacy-style vital tiles and abnormal chips in Phase 5B-2.
- Do not copy old speech code; use the current backend `/speech/transcribe`
  contract in a later phase if needed.

### Result Layout

Legacy:
- Hero card emphasizes final triage level and confidence.
- Probability breakdown is tabular/report-like.
- Decision pathway narrative explains rule evaluation, model prediction, and
  final decision.
- Report generation/email concepts are prominent.

Current:
- Main metrics show final ESI, predicted ESI, confidence, and final source.
- Probability section uses progress bars.
- Safety, recommendation, explanation, summary, and model info are separate.

Continuity decision:
- Keep the current backend fields.
- Make the result page more like the legacy hero/report layout:
  final ESI hero, confidence ring or prominent percentage, probability bars,
  safety status card, decision pathway, clinician summary, and model metadata.
- Convert legacy CTAS language to ESI and remove response-time promises unless
  explicitly validated for ESI workflows.

### Probability And Confidence Display

Legacy:
- Uses a large confidence treatment and selected-level highlighting.
- Shows class probabilities as part of a report.

Current:
- Shows ESI 3/4/5 progress bars.

Continuity decision:
- Keep progress bars because they are clear.
- Add selected ESI highlighting and a stronger confidence visual.
- Do not invent probabilities or display CTAS 1/2 probabilities; the current
  model predicts ESI 3/4/5 only.

### Clinician Review Flow

Legacy:
- Has logged-in/guest identity concepts and saves assessments for logged-in
  users.
- Result page includes assessor identity in reports.

Current:
- Clinician review page is still a placeholder.
- Backend has DB-backed `/clinician-review`.

Continuity decision:
- Carry forward the idea of clinician identity/review status, but implement it
  through current backend clinician review contracts.
- Add accept/override/needs-review workflow in Phase 5B-2 or later.
- Do not reuse legacy authentication/database code.

### Dashboard Style

Legacy:
- No fully separate dashboard page was found in the active legacy frontend; the
  strongest dashboard-like assets are saved assessments and report summaries.

Current:
- Dashboard page is a placeholder.
- Backend has `/dashboard/summary`.

Continuity decision:
- Build the current dashboard around backend summary counts, pending/completed
  review status, high-risk flags, ESI distribution, and recent assessments.
- Use compact metric cards inspired by legacy vital/result cards.

### Color Palette And Spacing

Legacy:
- Dominant palette: clinical blues, soft sky accents, white cards, pale warning
  amber/red/green status chips.
- Uses rounded 10-16px cards and noticeable custom CSS.

Current:
- More restrained: white cards, gray-blue borders, muted teal result band.

Continuity decision:
- Keep a restrained clinical palette, but reintroduce the legacy blue accent
  system in a subtler way.
- Avoid overusing gradients and large radius cards; align with current app's
  simpler 8px card radius where practical.

### Disclaimer Placement

Legacy:
- Disclaimer appears in result/report output and email/PDF wording.
- It generally says AI supports, not replaces, clinician judgment.

Current:
- Disclaimer appears on Home and Result pages.

Continuity decision:
- Keep the disclaimer always visible on result pages.
- Add a compact disclaimer in intake footer or sidebar.
- Keep wording conservative: decision-support only, not diagnosis, not a
  substitute for clinician judgment.

## Carry Forward From Khushal

- Familiar page flow: login/session context -> new assessment -> result -> review/report.
- Sectioned intake structure with patient info, chief complaint, vitals, and
  safety warnings.
- Vital-sign cards with value, unit, reference hint, and normal/abnormal status.
- Result hero card with final triage level and confidence.
- Probability breakdown with selected-level emphasis.
- Decision pathway narrative explaining model output plus safety rules.
- Report-ready clinician summary and audit-minded metadata.
- Clear guest/backend/session status messaging.
- Clinical blue palette with subtle status chips.

## Do Not Carry Forward

- CTAS/KTAS terminology in active UI.
- Legacy PyCaret, pickle, and `model_by_kp.pkl` loading concepts.
- Old synthetic metrics or unverified model performance claims.
- Monolithic Streamlit router and hidden sidebar as the main navigation pattern.
- Legacy local database/auth code.
- Diagnostic or overconfident clinical claims.
- Response-time promises unless validated and explicitly scoped to ESI workflow.
- Old Azure Speech implementation; use current backend speech contract in a
  later phase.
- Direct model calls from Streamlit.

## Modernization Decisions

- Keep current Streamlit multi-page structure.
- Keep the current `api_client.py` backend boundary.
- Keep `/predict`, `/ready`, `/clinician-review`, `/dashboard/summary`, and
  `/reports/generate` as the source of truth.
- Use ESI-only labels and ESI 3/4/5 probability display.
- Treat safety-rule escalation as a first-class visual state.
- Make the UI feel clinical and recruiter-friendly without hiding backend
  readiness, model status, or placeholder fallback state.

## Result Page Design Recommendations

1. Add a hero result band:
   - Final ESI as the largest signal.
   - Predicted ESI, confidence, and final source nearby.
   - Use color status by ESI level, but keep colors restrained.

2. Add selected-probability emphasis:
   - Keep ESI 3/4/5 progress bars.
   - Highlight the predicted class.
   - Show confidence as the max probability.

3. Add a decision pathway section:
   - Step 1: model probability output.
   - Step 2: ESI 5 threshold behavior when applicable.
   - Step 3: safety rule review and final ESI.
   - Step 4: clinician review required.

4. Improve safety-rule display:
   - Separate "No safety-rule escalation" from "Safety-rule override".
   - Show triggered rule IDs and explanations.
   - Make safety override visually distinct from model-only final source.

5. Elevate clinician summary:
   - Use note-style clinical summary card.
   - Include age/sex, chief complaint, vitals, predicted/final ESI, safety state.

6. Add report/audit affordances:
   - Display request ID and assessment ID clearly.
   - Prepare space for report metadata and clinician review status.
   - Do not build PDF/email unless it is part of a later phase.

## Specific Phase 5B Implementation Checklist

- Add a reusable top header component inspired by legacy `nav_bar`, but keep
  Streamlit sidebar navigation.
- Upgrade `components/intake_form.py` with section containers:
  patient, complaint, vitals, safety context.
- Add vital tiles or compact status chips for HR, BP, RR, O2, temperature, and
  pain score.
- Add inline abnormal-vital messaging derived from entered values.
- Upgrade `components/result_card.py` into a true ESI hero component.
- Upgrade `components/probability_chart.py` to highlight selected/predicted ESI.
- Add a decision pathway component for model output, threshold selection, safety
  rules, and final source.
- Add a safety-rule component with model-only vs override states.
- Add a clinician-summary card component.
- Update `pages/03_Result.py` to use the new result components.
- Keep placeholder warning behavior when backend returns `model_loaded=false`.
- Avoid changes to backend model inference and artifacts during this UI polish.

## Files Likely To Change In Phase 5B-2

- `app/frontend/streamlit_app/assets/styles.py`
- `app/frontend/streamlit_app/components/layout.py`
- `app/frontend/streamlit_app/components/intake_form.py`
- `app/frontend/streamlit_app/components/result_card.py`
- `app/frontend/streamlit_app/components/probability_chart.py`
- `app/frontend/streamlit_app/components/summary_card.py`
- `app/frontend/streamlit_app/components/dashboard_cards.py`
- `app/frontend/streamlit_app/pages/02_New_Assessment.py`
- `app/frontend/streamlit_app/pages/03_Result.py`
- `app/frontend/streamlit_app/pages/04_Clinician_Review.py`
- `app/frontend/streamlit_app/pages/05_Dashboard.py`
- `app/frontend/streamlit_app/pages/06_Assessment_Detail.py`

## Bottom Line

Phase 5B should not recreate the legacy app. It should carry forward the parts
that made it feel clinical and complete: sectioned intake, rich vital cards,
hero result summary, probability breakdown, decision pathway, and report-ready
language. The active app should remain ESI-only, modular, backend-backed, and
transparent about model status and clinician oversight.

# TriageAI Screenshot Checklist

## Screenshot Standards

- [ ] Use fictional patient data only.
- [ ] Use one consistent synthetic assessment across workflow screenshots `01` through `11`.
- [ ] Keep browser zoom at 100%.
- [ ] Use a consistent browser width and viewport across application screenshots.
- [ ] Hide bookmarks, notifications, personal accounts, browser profiles, and unrelated tabs.
- [ ] Show backend-connected and model-ready states when relevant.
- [ ] Do not capture loading, error, empty, mock, or disconnected states unless the screenshot intentionally documents one.
- [ ] Preserve enough page title, navigation, and workflow context for each screenshot to be understandable on its own.
- [ ] Do not state or imply clinical validation.
- [ ] Capture and export in PNG format.
- [ ] Store final files in `docs/assets/screenshots/`.
- [ ] Keep identifiers, review decisions, and report records consistent across the assessment workflow.

## Synthetic Screenshot Case

> “62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2. Patient looks pale and dizzy.”

This case is fictional and is used only for workflow demonstration.

## File Naming Convention

1. `01-command-center.png`
2. `02-new-intake-note.png`
3. `03-nlp-review-evidence.png`
4. `04-reviewed-structured-intake.png`
5. `05-prediction-result.png`
6. `06-clinician-review.png`
7. `07-assessment-detail.png`
8. `08-audit-trail.png`
9. `09-reports-page.png`
10. `10-pdf-summary.png`
11. `11-model-monitoring.png`
12. `12-github-actions.png`
13. `13-system-architecture.png`

## Capture Checklist

### 01 Command Center

- **Filename:** `01-command-center.png`
- **Page or source:** React `/command-center`
- **Must be visible:** Backend-connected and model-ready status; Command Center title; useful summary cards; recent synthetic assessments; clean primary navigation.
- **Must not be visible:** Empty, loading, error, disconnected, or mock states; real patient information; personal browser content; inconsistent assessment totals.
- **Why it matters:** Establishes the full-stack product surface and shows that dashboard data comes from the connected backend.
- **Suggested portfolio caption:** “Backend-connected Command Center with persisted assessment activity and model readiness.”
- **Required for:**
  - GitHub README: **Required**
  - Portfolio case study: **Required**
  - Professor presentation: **Required**
  - LinkedIn: **Required**

### 02 New Intake Note

- **Filename:** `02-new-intake-note.png`
- **Page or source:** React `/new-assessment`, New Intake note/transcript state
- **Must be visible:** The exact synthetic note; note or transcript input; recorded-audio control; decision-support wording; page title and current intake context.
- **Must not be visible:** Real patient identifiers; an active prediction result; unsupported speech claims; browser microphone details containing personal device names.
- **Why it matters:** Shows that the workflow accepts typed, pasted, or recorded intake before any extraction or prediction begins.
- **Suggested portfolio caption:** “New Intake supports typed, pasted, or recorded clinical notes while keeping downstream actions explicit.”
- **Required for:**
  - GitHub README: **Optional**
  - Portfolio case study: **Required**
  - Professor presentation: **Optional**
  - LinkedIn: **Optional**

### 03 NLP Review Evidence

- **Filename:** `03-nlp-review-evidence.png`
- **Page or source:** React `/new-assessment`, Clinical NLP review after `POST /nlp/extract-intake`
- **Must be visible:** Extracted age, chief complaint, symptoms, and vital signs; source-text evidence snippets; safety cues; respiratory rate marked missing; editable fields; review-required state before confirmation.
- **Must not be visible:** A completed prediction; invented respiratory rate; unchecked evidence presented as verified; raw technical payloads; diagnostic or treatment wording.
- **Why it matters:** This is the strongest responsible-AI screenshot because it shows evidence, missing-data handling, editability, and the mandatory human review boundary.
- **Suggested portfolio caption:** “Evidence-linked NLP extraction keeps fields editable, surfaces safety cues, and leaves undocumented respiratory rate missing.”
- **Required for:**
  - GitHub README: **Required**
  - Portfolio case study: **Required**
  - Professor presentation: **Required**
  - LinkedIn: **Required**

### 04 Reviewed Structured Intake

- **Filename:** `04-reviewed-structured-intake.png`
- **Page or source:** React `/new-assessment`, reviewed intake state immediately before prediction
- **Must be visible:** Corrected or confirmed structured fields; completed clinician review confirmation; enabled decision-support action; the same synthetic assessment context.
- **Must not be visible:** Unreviewed extracted fields; a disabled confirmation hidden from view; a prediction result that suggests review was bypassed; inconsistent values from the synthetic note.
- **Why it matters:** Demonstrates the enforced correction and confirmation gate between NLP extraction and model inference.
- **Suggested portfolio caption:** “Clinician-confirmed structured intake is required before ESI decision support can run.”
- **Required for:**
  - GitHub README: **Not needed**
  - Portfolio case study: **Required**
  - Professor presentation: **Optional**
  - LinkedIn: **Not needed**

### 05 Prediction Result

- **Filename:** `05-prediction-result.png`
- **Page or source:** Prediction result shown after `POST /predict`
- **Must be visible:** LightGBM-assisted ESI result; predicted and final ESI where displayed; probabilities or confidence; safety-rule status; final-source explanation; model information when available; decision-support disclaimer.
- **Must not be visible:** Fake or unsupported metrics; an unexplained final ESI change; wording that implies an autonomous decision; diagnosis or treatment claims; disconnected model state.
- **Why it matters:** Shows how model inference and transparent safety-rule escalation are presented as separate, reviewable parts of ESI care routing.
- **Suggested portfolio caption:** “LightGBM-assisted ESI output with visible probabilities, safety-rule status, and decision-support boundaries.”
- **Required for:**
  - GitHub README: **Required**
  - Portfolio case study: **Required**
  - Professor presentation: **Required**
  - LinkedIn: **Required**

### 06 Clinician Review

- **Filename:** `06-clinician-review.png`
- **Page or source:** Clinician review controls for the persisted assessment
- **Must be visible:** Accept, override, and further-review choices where available; model-and-safety result being reviewed; clinician decision-support wording; documented reason field if override is selected.
- **Must not be visible:** A completed action that conflicts with the later audit screenshot; an override without its required reason; wording that transfers final authority to the model.
- **Why it matters:** Makes the human-in-the-loop decision point explicit and shows that clinician judgment remains required.
- **Suggested portfolio caption:** “Clinicians can accept, document an override, or request further review before the workflow is completed.”
- **Required for:**
  - GitHub README: **Optional**
  - Portfolio case study: **Required**
  - Professor presentation: **Optional**
  - LinkedIn: **Optional**

### 07 Assessment Detail

- **Filename:** `07-assessment-detail.png`
- **Page or source:** React `/assessments/{assessment_id}`
- **Must be visible:** Persisted intake summary; model result; safety-rule status; probabilities or confidence where available; clinician-review status; assessment identifier; navigation to related audit or report actions.
- **Must not be visible:** A different assessment from earlier screenshots; stale or contradictory review status; real identifiers; browser-only or mock state.
- **Why it matters:** Proves that intake, prediction, safety, and clinician review remain available as one backend-owned assessment record.
- **Suggested portfolio caption:** “Assessment Detail unifies persisted intake, model output, safety status, and clinician review.”
- **Required for:**
  - GitHub README: **Optional**
  - Portfolio case study: **Required**
  - Professor presentation: **Optional**
  - LinkedIn: **Not needed**

### 08 Audit Trail

- **Filename:** `08-audit-trail.png`
- **Page or source:** React `/audit` or assessment-specific audit view
- **Must be visible:** Reviewed NLP evidence event; prediction event; safety-rule escalation or safety status within the recorded decision path; clinician decision; PDF generation event when available; timestamps or event order; the consistent synthetic assessment identifier.
- **Must not be visible:** Raw recorded audio; raw clinical note text in NLP evidence; secrets; unrelated assessments that obscure the narrative; an event sequence inconsistent with the captured workflow.
- **Why it matters:** Demonstrates traceability across extraction, prediction, safety handling, human review, and reporting.
- **Suggested portfolio caption:** “The backend audit trail preserves reviewed NLP evidence, prediction, safety context, clinician action, and reporting events.”
- **Required for:**
  - GitHub README: **Required**
  - Portfolio case study: **Required**
  - Professor presentation: **Required**
  - LinkedIn: **Optional**

### 09 Reports Page

- **Filename:** `09-reports-page.png`
- **Page or source:** React `/reports`
- **Must be visible:** Generated report record for the same synthetic assessment; report status; generated timestamp; download or preview action; clean report navigation.
- **Must not be visible:** Failed or queued-only record presented as complete; unrelated reports with real data; a download action pointing to a missing artifact.
- **Why it matters:** Shows that reports are tracked as backend records rather than created as an untraceable browser-only export.
- **Suggested portfolio caption:** “Backend report records keep PDF generation connected to the persisted assessment workflow.”
- **Required for:**
  - GitHub README: **Not needed**
  - Portfolio case study: **Required**
  - Professor presentation: **Optional**
  - LinkedIn: **Not needed**

### 10 PDF Summary

- **Filename:** `10-pdf-summary.png`
- **Page or source:** First page or most informative page of the backend-generated PDF from `GET /assessments/{assessment_id}/report/pdf`
- **Must be visible:** Report title; synthetic assessment identifier; structured intake context; ESI decision-support result; safety status; clinician-review state; reviewed NLP evidence where it fits; clear decision-support disclaimer.
- **Must not be visible:** Real patient information; raw note text; unsupported medical claims; frontend-generated mock PDF; content that conflicts with Assessment Detail or the audit trail.
- **Why it matters:** Shows the final portable evidence artifact generated from the backend source-of-truth record.
- **Suggested portfolio caption:** “Backend-generated PDF decision-support summary with persisted intake, safety context, clinician review, and reviewed evidence.”
- **Required for:**
  - GitHub README: **Required**
  - Portfolio case study: **Required**
  - Professor presentation: **Required**
  - LinkedIn: **Optional**

### 11 Model Monitoring

- **Filename:** `11-model-monitoring.png`
- **Page or source:** React `/model-monitoring`
- **Must be visible:** Model version `lightgbm_v2_weight_threshold_esi345`; model loaded state; feature count 273; class order when available; operational status; verified metrics shown in the existing UI: 78.32% accuracy, 70.37% Macro F1, 78.88% Weighted F1, 54.70% ESI 5 F1, and 0.68% unsafe ESI 3-to-ESI 5 downgrade rate.
- **Must not be visible:** Placeholder or disconnected status; invented live-monitoring data; unsupported metrics; an incorrect model version, feature count, or class scope.
- **Why it matters:** Connects the visible application to the verified LightGBM V2 ESI 3/4/5 artifact and readiness metadata.
- **Suggested portfolio caption:** “Model Monitoring exposes the loaded version, 273-feature contract, operational readiness, and verified evaluation metrics.”
- **Required for:**
  - GitHub README: **Optional**
  - Portfolio case study: **Required**
  - Professor presentation: **Optional**
  - LinkedIn: **Optional**

### 12 GitHub Actions

- **Filename:** `12-github-actions.png`
- **Page or source:** GitHub Actions CI workflow for the final branch or `main`
- **Must be visible:** Repository and workflow name; final or `main` branch; passing backend test job; passing frontend test and build job; successful overall workflow state; relevant commit identifier or timestamp.
- **Must not be visible:** Failed or cancelled jobs presented as final validation; secret values; private notifications; unrelated repositories, tabs, or account details.
- **Why it matters:** Provides external evidence that backend tests, frontend tests, and the React build are enforced by CI.
- **Suggested portfolio caption:** “GitHub Actions validates backend tests, frontend tests, and the React production build.”
- **Required for:**
  - GitHub README: **Optional**
  - Portfolio case study: **Optional**
  - Professor presentation: **Not needed**
  - LinkedIn: **Optional**

### 13 System Architecture

- **Filename:** `13-system-architecture.png`
- **Page or source:** Existing Mermaid diagram in `docs/architecture/triageai_system_architecture.md` or the concise case-study diagram in `docs/portfolio/portfolio-case-study.md`
- **Must be visible:** React intake; optional speech path; `POST /nlp/extract-intake`; clinician correction and confirmation; `POST /predict`; LightGBM V2 ESI 3/4/5; safety-rule escalation; clinician decision; backend database; audit trail; PDF decision-support summary.
- **Must not be visible:** Redesigned or invented components; unsupported cloud services; an automatic path that bypasses review gates; obsolete Streamlit-only architecture; diagnosis or treatment wording.
- **Why it matters:** Explains how frontend, APIs, model inference, human review, persistence, audit, and reporting form one controlled workflow.
- **Suggested portfolio caption:** “Review gates separate speech, NLP extraction, model inference, safety escalation, clinician review, and reporting.”
- **Required for:**
  - GitHub README: **Required**
  - Portfolio case study: **Required**
  - Professor presentation: **Required**
  - LinkedIn: **Optional**

## Recommended README Screenshot Set

Use these six images:

1. `01-command-center.png`
2. `03-nlp-review-evidence.png`
3. `05-prediction-result.png`
4. `08-audit-trail.png`
5. `10-pdf-summary.png`
6. `13-system-architecture.png`

These provide the strongest product, responsible-AI, inference, traceability, reporting, and architecture evidence without repeating every intermediate state. Placing all 13 images in the README would make it slow to scan, add page weight, duplicate closely related workflow states, and weaken the recruiter-facing narrative. Keep the complete set for the portfolio case study and presentation materials.

## Recommended Portfolio Screenshot Order

Use the complete set in this narrative order:

1. `01-command-center.png` — establish the product and backend-ready state.
2. `13-system-architecture.png` — explain the review-first system before the detailed walkthrough.
3. `02-new-intake-note.png` — introduce typed, pasted, and recorded intake.
4. `03-nlp-review-evidence.png` — show evidence, safety cues, and missing-data handling.
5. `04-reviewed-structured-intake.png` — show mandatory clinician confirmation.
6. `05-prediction-result.png` — present model output and safety-rule status.
7. `06-clinician-review.png` — show accept, override, and further-review controls.
8. `07-assessment-detail.png` — show persisted workflow state.
9. `08-audit-trail.png` — demonstrate traceability.
10. `09-reports-page.png` — show report records and actions.
11. `10-pdf-summary.png` — show the final backend-generated evidence artifact.
12. `11-model-monitoring.png` — connect the UI to the verified model and readiness contract.
13. `12-github-actions.png` — close with automated engineering validation.

## Professor Presentation Screenshot Set

Prepare this minimum six-image backup set in presentation order:

1. `01-command-center.png`
2. `03-nlp-review-evidence.png`
3. `05-prediction-result.png`
4. `08-audit-trail.png`
5. `10-pdf-summary.png`
6. `13-system-architecture.png`

This set can support the full explanation if the live application is unavailable: product readiness, review-first extraction, model and safety output, human-in-the-loop traceability, reporting, and architecture.

## LinkedIn Screenshot Set

Use a four-image carousel:

1. `01-command-center.png` — polished full-stack product overview.
2. `03-nlp-review-evidence.png` — strongest responsible-AI and human-review evidence.
3. `05-prediction-result.png` — LightGBM-assisted ESI care routing and transparent safety status.
4. `08-audit-trail.png` — persisted review and auditability.

Keep captions brief and state that this is a completed local demonstration, not a clinically validated system.

## Final Privacy and Accuracy Review

- [ ] Every patient and assessment record is fictional.
- [ ] No personal browser information, profile, bookmarks, notifications, or unrelated tabs are visible.
- [ ] No secrets, tokens, credentials, environment variables, terminal history, or local file paths are visible.
- [ ] All displayed metrics match the verified final model metrics; no unsupported metrics appear.
- [ ] Model version is `lightgbm_v2_weight_threshold_esi345`.
- [ ] Feature count is 273.
- [ ] Model scope and class order remain LightGBM V2 ESI 3/4/5 and `ESI_3`, `ESI_4`, `ESI_5`.
- [ ] Decision-support wording is clear, and clinician judgment remains required.
- [ ] No diagnosis, treatment, autonomous-decision, clinical-validation, or production-readiness claim appears.
- [ ] No screenshot shows an inconsistent, failed, stale, loading, error, mock, or disconnected state.
- [ ] Assessment identifiers, reviewed values, safety status, clinician decision, audit events, and PDF content are consistent across the workflow.
- [ ] PNG filenames exactly match the required convention and files are stored in `docs/assets/screenshots/`.

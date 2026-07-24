# TriageAI Recruiter Content Pack

## One-Sentence Project Description

TriageAI is a full-stack, human-in-the-loop clinical decision-support workflow that converts typed, pasted, or recorded structured intake into reviewable ESI care routing with transparent safety-rule escalation, clinician review, an audit trail, and a PDF decision-support summary.

## Portfolio Card Summary

TriageAI is a full-stack, human-in-the-loop clinical decision-support workflow built with React, TypeScript, FastAPI, SQLAlchemy, and LightGBM. It turns typed, pasted, or recorded intake into evidence-linked structured fields, requires clinician confirmation before prediction, applies transparent safety-rule escalation, and preserves clinician review in an audit trail and backend-generated PDF decision-support summary. A versioned 273-feature model registry, 90 passing backend tests, 38 frontend tests, CI, and Docker validation support the completed local demonstration while clinician judgment remains required.

## GitHub Repository Subtitle

Full-stack human-in-the-loop clinical decision-support workflow for structured intake, LightGBM ESI care routing, audit trails, and PDF summaries.

## Resume Bullets — AI Engineer

- Built a React and TypeScript frontend integrated with FastAPI APIs, SQLAlchemy persistence, and backend-owned assessment state.
- Implemented evidence-linked clinical NLP plus recorded-audio intake through Azure Speech when configured and a safe backend fallback otherwise.
- Integrated LightGBM V2 ESI 3/4/5 inference from a versioned 273-feature model registry with a 0.60 decision threshold.
- Delivered safety-rule escalation, clinician accept/override review, audit trail persistence, and backend PDF summaries; verified 90 backend tests, 38 frontend tests, a passing React build, and a passing Docker full-stack run.

## Resume Bullets — Data Scientist

- Engineered structured preprocessing and a 273-feature inference pipeline from reviewed clinical intake fields.
- Evaluated multiclass LightGBM performance using accuracy, Macro F1, Weighted F1, ESI 5 F1, and an unsafe downgrade metric.
- Selected a 0.60 decision threshold and retained raw LightGBM probabilities after evaluating calibration against configured safety guardrails.
- Deployed the selected model through a versioned registry and documented class scope, missing-data boundaries, clinician review requirements, and clinical validation limitations.

## Resume Bullets — Junior ML/MLOps Engineer

- Packaged the trained model, preprocessing artifacts, feature list, class mapping, threshold configuration, and deployment metadata in a versioned registry.
- Implemented `/health` and `/ready` checks for database connectivity, model loading, metadata, 273 features, and class order.
- Containerized the React and FastAPI application with Docker Compose, SQLite demo persistence, generated-report storage, and a verified full-stack run.
- Automated GitHub Actions CI for backend persistence and audit behavior, frontend contracts, and builds, with 90 backend tests and 38 frontend tests.

## LinkedIn Project Description

TriageAI / SympDirect is a completed local demonstration of a full-stack, human-in-the-loop clinical decision-support workflow for structured intake and ESI care routing.

I built the workflow with React, TypeScript, FastAPI, SQLAlchemy, and a versioned LightGBM model registry. Clinicians can type or paste intake notes, or submit recorded audio through an optional Azure Speech path with a safe backend fallback. The Clinical NLP Safety Layer extracts editable fields, source-text evidence, safety cues, and missing-information indicators. A mandatory confirmation gate prevents unreviewed NLP output from reaching prediction.

The backend loads the LightGBM V2 ESI 3/4/5 model, builds the approved 273-feature representation, and applies transparent safety-rule escalation after inference. Clinicians can accept, override with documented context, or request further review. The backend persists assessment and review state, stores reviewed evidence in an audit trail, and generates a PDF decision-support summary.

The demo-freeze validation completed 90 passing backend tests, 12 frontend test files with 38 tests, a passing React production build, and a passing Docker full-stack run. The project is a software and machine-learning demonstration, not a clinically validated or production-ready system; clinician judgment remains required.

## LinkedIn Completion Post

I have completed the demo-freeze stage of TriageAI / SympDirect, a full-stack, human-in-the-loop clinical decision-support workflow for structured intake and ESI care routing.

The final workflow now includes:

- review-first clinical NLP with evidence snippets, safety cues, and missing-information handling;
- typed, pasted, and recorded-audio intake through `/speech/transcribe`, with Azure Speech support when configured and a safe backend fallback otherwise;
- clinician correction and confirmation before reviewed fields can reach `/predict`;
- a versioned LightGBM V2 ESI 3/4/5 model registry and 273-feature inference pipeline;
- transparent safety-rule escalation shown separately from the model result;
- clinician accept, override, and further-review actions;
- backend persistence, an audit trail, and a PDF decision-support summary containing reviewed NLP evidence;
- Docker Compose packaging and GitHub Actions CI.

Final local validation completed 90 passing backend tests, 12 frontend test files with 38 tests, a passing React production build, and a passing Docker full-stack run.

The most important design choice was to keep every AI-assisted stage reviewable. Transcription does not automatically trigger extraction, extraction does not automatically trigger prediction, and model output does not replace clinician review.

This remains a portfolio and educational demonstration. It has not completed prospective clinical validation, usability or fairness studies, production security hardening, governance review, or regulatory assessment. Clinician judgment remains required.

## Thirty-Second Interview Explanation

“TriageAI is a full-stack clinical decision-support workflow I built around a LightGBM ESI care-routing model. React handles structured, pasted, or recorded intake, while FastAPI owns NLP extraction, model inference, safety rules, persistence, audit history, and PDF generation. The key design is human-in-the-loop: evidence-linked NLP fields must be corrected and confirmed before prediction, and clinicians can accept, override, or request further review. The completed local demo has 90 passing backend tests, 38 frontend tests, and a verified Docker run.”

## Ninety-Second Interview Explanation

“TriageAI started from a practical question: how do you turn a trained classifier into a reviewable clinical decision-support workflow instead of stopping at a notebook prediction?

I built a React and TypeScript frontend connected to a FastAPI backend. Intake can be structured, pasted from a note, or submitted as recorded audio. The NLP layer returns editable fields, evidence snippets, safety cues, and missing-data indicators. It cannot silently trigger prediction; a clinician must correct and confirm the extraction first.

FastAPI then builds the approved 273-feature representation and loads the LightGBM V2 ESI 3/4/5 model from a versioned registry containing the model, preprocessing artifacts, feature list, threshold configuration, class mapping, and metadata. Transparent safety rules run separately and can escalate configured high-risk cases for urgent clinician review. The clinician can accept the result, override it with a reason, or request further review.

The backend remains the source of truth for assessments, predictions, clinician actions, the audit trail, and PDF decision-support summaries. I validated the local workflow with 90 passing backend tests, 38 frontend tests across 12 files, a passing React production build, and a passing Docker full-stack run. It is not clinically validated or production-ready; clinician judgment remains required.”

## Technical Interview Questions and Answers

### What problem does TriageAI solve?

It connects mixed-format clinical intake to reviewable ESI care routing. The workflow structures notes, makes extraction evidence and missing data visible, runs model inference and safety-rule escalation, and preserves the clinician decision in an audit trail.

### Why is this more than a model demo?

The model is one controlled stage inside a full-stack workflow. TriageAI adds typed and recorded intake, NLP review gates, API validation, persistence, transparent safety rules, clinician review, auditability, reporting, tests, CI, and Docker.

### Why did you choose LightGBM?

The selected LightGBM artifact balanced overall multiclass performance with safety-sensitive ESI 5 behaviour and downgrade-risk controls. It also supports fast, reproducible inference over the approved structured feature representation.

### How is the model loaded and versioned?

FastAPI loads the model, preprocessing artifacts, 273-feature list, threshold configuration, class mapping, and deployment metadata from `model_registry/esi_345_lightgbm_v2/`. The deployed version is `lightgbm_v2_weight_threshold_esi345`, and readiness exposes the loaded metadata.

### How do you prevent NLP errors from automatically reaching the model?

Extraction and prediction are separate explicit actions. NLP output remains editable, source evidence and missing fields stay visible, and the frontend requires clinician confirmation before reviewed fields can be submitted to `/predict`.

### What happens when safety rules disagree with the model?

The LightGBM prediction and safety-rule escalation remain visible separately. A configured rule can escalate the routing result for urgent review, after which the clinician can accept, override with a documented reason, or request further review.

### Why is the backend the source of truth?

Backend ownership keeps assessments, predictions, reviews, audit events, and reports consistent across every frontend view. It also keeps model execution and official PDF generation out of browser-only state.

### How is the workflow tested?

The final demo freeze completed 90 passing backend tests and 38 frontend tests across 12 files. Coverage includes NLP extraction, model and readiness contracts, safety rules, persistence, clinician review, audit behaviour, PDF generation, frontend API behaviour, and UI helpers; the React production build and Docker full-stack run also passed.

### What are the current limitations?

The model is limited to ESI 3/4/5, NLP output still requires correction and confirmation, Azure Speech depends on external configuration, and the local demo uses SQLite, demo authentication behaviour, and local report storage. The project has not completed prospective clinical validation, usability studies, subgroup fairness evaluation, or production security and governance work.

### What would be required for production deployment?

It would require prospective clinical validation, workflow usability and subgroup fairness studies, calibration and drift monitoring, production authentication and role-based access control, managed PostgreSQL, privacy and security controls, secret management, centralized observability, managed report storage, controlled cloud deployment, governance, and regulatory assessment.

## Role-Specific Positioning

### AI Engineer

TriageAI demonstrates the ability to integrate model inference into a complete product workflow. It connects React, FastAPI, evidence-linked NLP, safety logic, human review, persistence, auditability, and reporting without allowing automated output to bypass clinician confirmation.

### Data Scientist

TriageAI demonstrates structured feature engineering, multiclass evaluation, class-level analysis, safety-sensitive error measurement, threshold selection, and responsible interpretation. The selected model is documented with exact metrics, class scope, model-registry artifacts, and clinical validation limitations.

### Junior ML Engineer

TriageAI demonstrates the transition from evaluated artifacts to reproducible backend inference. The project packages preprocessing, 273 ordered features, labels, thresholds, metadata, and the trained LightGBM model behind typed APIs and readiness checks.

### Junior MLOps Engineer

TriageAI demonstrates versioned artifact management, deployment metadata, health and readiness checks, Docker Compose, GitHub Actions CI, regression testing, and backend persistence. The local demo also makes audit and report behaviour testable across the full workflow.

### Full-Stack AI Developer

TriageAI demonstrates end-to-end ownership across React, TypeScript, FastAPI, SQLAlchemy, ML inference, clinical NLP, and ReportLab. The frontend exposes review and correction controls while the backend maintains the source-of-truth assessment, audit trail, and PDF decision-support summary.

## Verified Facts

| Fact | Verified value |
|---|---|
| model | LightGBM V2 ESI 3/4/5 |
| model version | `lightgbm_v2_weight_threshold_esi345` |
| registry | `model_registry/esi_345_lightgbm_v2/` |
| feature count | 273 |
| class order | `ESI_3`, `ESI_4`, `ESI_5` |
| decision threshold | 0.60 |
| accuracy | 78.32% |
| Macro F1 | 70.37% |
| Weighted F1 | 78.88% |
| ESI 5 F1 | 54.70% |
| unsafe ESI 3-to-ESI 5 downgrade rate | 0.68% |
| backend | 90 passing tests |
| frontend | 12 test files and 38 tests |
| React production build | passed |
| Docker full-stack run | passed |

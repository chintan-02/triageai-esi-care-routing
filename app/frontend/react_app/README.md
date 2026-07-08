# TriageAI React Frontend v2.1

Premium React + TypeScript frontend for the TriageAI / SympDirect ESI clinical intake and care-routing workflow.

This is structured as a real product frontend, not a throwaway UI prototype. It runs standalone with synthetic local records for development, but the intended architecture is:

```text
React + TypeScript frontend
→ FastAPI assessment adapter
→ final LightGBM model artifacts
→ safety gate escalation
→ clinician review / override
→ audit trail
→ official backend PDF report generation
```

## Final model source of truth wired into v2.1

Based on the executed notebook you provided:

```text
ESI_345_FINAL_DEPLOYMENT_LIGHTGBM_V2_SAFETY_TUNED_FINAL_VERDICT_CHECKED.ipynb
```

The frontend now exposes the final model values through a separate model-status contract:

| Item | Value |
|---|---:|
| Model | LightGBM V2 Weight + Threshold |
| Model version | lightgbm_v2_weight_threshold_esi345_safety_tuned |
| Selected threshold | 0.60 |
| Deployment threshold | 0.60 |
| ESI 5 weight multiplier | 0.75 |
| Feature count | 273 |
| Accuracy | 78.32% |
| Macro F1 | 70.37% |
| Weighted F1 | 78.88% |
| ESI 5 F1 | 54.70% |
| Unsafe ESI 3 → ESI 5 downgrade rate | 0.68% |
| Calibration deployment | Raw LightGBM probabilities; calibrated probabilities not deployed |

Important wording:

> The model predicts ESI 3/4/5. Safety rules and clinician review can escalate the final routing decision to ESI 1/2 when high-risk criteria are present.

Do not claim the model directly predicts ESI 1–5.

## Major upgrades in v2.1

- Upgraded `jspdf` to the newer major version target and kept PDF generation lazy-loaded.
- Added route-level lazy loading to reduce the initial JavaScript bundle.
- Added a separate model-status endpoint contract: `GET /api/v1/model/status`.
- Moved final notebook metrics out of patient prediction display and into model monitoring.
- Added true stepper intake: Patient → Complaint → Vitals → Risk Flags → Review & Predict.
- Rebuilt the vitals section with premium horizontal slider cards for SpO₂, heart rate, BP, temperature, respiratory rate, and pain score.
- Added age-aware vital display ranges for infant/toddler/child/adolescent/adult patients.
- Added a final decision banner on the result page.
- Added a visible “why final ESI changed” comparison when safety rules escalate the model output.
- Added role-based UI permissions for Nurse, Doctor, and Admin workflows.
- Made topbar search functional by routing to the assessment queue with a search parameter.
- Added error state, retry handling, and runtime environment validation.
- Added Vitest tests for vitals, safety escalation, percent formatting, and intake validation.

## Role permissions

| Role | Access |
|---|---|
| Nurse | Create assessments, read assessments, accept decisions, generate reports |
| Doctor | Create assessments, read assessments, accept/override decisions, generate reports, read audit trail |
| Admin | Read assessments, generate reports, model monitoring, settings, audit trail |

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Local mock sign-in:

```text
Password: triage2026
```

This password is only for local standalone frontend mode. Live deployment should use FastAPI JWT or secure httpOnly session auth.

## Quality checks

```bash
npm run lint
npm run test
npm run build
npm audit
```

## Environment

```env
# Local standalone development
VITE_USE_MOCK_API=true
VITE_USE_MOCK_AUTH=true
VITE_API_BASE_URL=http://localhost:8000

# Live backend adapter
VITE_USE_MOCK_API=false
VITE_USE_MOCK_AUTH=false
VITE_API_BASE_URL=http://localhost:8000
```

## Backend adapter endpoints

```text
GET    /api/v1/dashboard/summary
GET    /api/v1/model/status
GET    /api/v1/assessments
GET    /api/v1/assessments/{id}
POST   /api/v1/assessments
POST   /api/v1/assessments/{id}/review
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/users/me
POST   /api/v1/auth/logout
```

Keep your existing `/health`, `/ready`, and `/predict` backend routes. Add the frontend-facing adapter layer above them.

## PDF strategy

The frontend still includes client-side PDF generation for standalone operation and fast UI testing. For the real product, make backend ReportLab the official PDF engine so report generation is controlled, auditable, consistent, and not dependent on browser behavior.

## Safety wording

This project is clinical decision support only. It is not a diagnostic tool and does not replace clinicians. Use wording such as structured intake, ESI care routing, safety-rule escalation, clinician review, human-in-the-loop override, audit trail, and PDF decision-support summary.

## v2.2 intake UI correction

This version adjusts the New Intake screen based on bedside usability feedback:

- The New Assessment page is now a fixed one-screen clinical workstation on desktop.
- The active intake panel, stepper, action buttons, and live summary stay in one viewport.
- The vitals section is the only area designed for horizontal scrolling.
- Vitals sliders now show stable normal reference ranges/bands while the current value changes.
- Age-aware flags remain active, but the normal range text stays visible so the user can compare current value vs reference without losing context.

The goal is closer to a real hospital intake console: less full-page scrolling, faster clinical scanning, and more stable vital-sign interpretation.


## v2.3 authentication UI correction

- Rebuilt the authentication screen as a balanced premium clinical-console entry page.
- Added Sign in / Create account tabs instead of sign-in only.
- Added local account creation fields: full name, role, work email, organization, unit, and local access code.
- Local accounts are for standalone development only; production should route registration through backend approval and secure session/JWT auth.

# TriageAI React Frontend — Backend Contract v2.1

This frontend is designed for a real FastAPI-backed clinical decision-support workflow. It can run independently with synthetic records, but production use should connect the API adapter described below.

## Important clinical scope

The final safety-tuned notebook baseline is:

- Model display name: `LightGBM V2 Weight + Threshold`
- Model version: `lightgbm_v2_weight_threshold_esi345_safety_tuned`
- Classifier scope: ESI 3 / ESI 4 / ESI 5
- Safety gate: enabled before/around prediction for ESI 1/2 escalation logic
- Selected threshold: `0.60`
- Deployment threshold: `0.60`
- ESI 5 weight multiplier: `0.75`
- Feature count: `273`
- Calibration deployment: raw LightGBM probabilities; calibrated probabilities are not deployed
- Final test accuracy: `78.32%`
- Final test Macro F1: `70.37%`
- Final test Weighted F1: `78.88%`
- Final test ESI 5 F1: `54.70%`
- Unsafe ESI 3 → ESI 5 downgrade rate: `0.68%`

Use this wording in the UI/API/PDF:

> The model predicts ESI 3/4/5. Safety rules and clinician review can escalate the final routing decision to ESI 1/2 when high-risk criteria are present.

Do not claim that the model directly predicts ESI 1–5.

## Required frontend-facing endpoints

```http
GET  /api/v1/dashboard/summary
GET  /api/v1/model/status
GET  /api/v1/assessments
GET  /api/v1/assessments/{id}
POST /api/v1/assessments
POST /api/v1/assessments/{id}/review
POST /api/v1/auth/login
POST /api/v1/auth/register
GET  /api/v1/users/me
POST /api/v1/auth/logout
```

Your current backend may already expose `/health`, `/ready`, and `/predict`. Do not break those. Add an adapter layer instead:

```text
React POST /api/v1/assessments
→ FastAPI stores intake/patient record
→ adapter calls internal prediction_service.predict()
→ safety gate applies ESI 1/2 escalation rules
→ audit event is saved
→ frontend receives AssessmentRecord
```

## Model status response

Model-level metrics should come from `GET /api/v1/model/status`, not from each patient prediction.

```json
{
  "apiContractVersion": "triageai.frontend.v2.1",
  "backendAdapterRequired": true,
  "activeModel": {
    "modelVersion": "lightgbm_v2_weight_threshold_esi345_safety_tuned",
    "modelDisplayName": "LightGBM V2 Weight + Threshold",
    "modelFamily": "LightGBM",
    "deploymentStage": "production-ready-baseline",
    "sourceNotebook": "ESI_345_FINAL_DEPLOYMENT_LIGHTGBM_V2_SAFETY_TUNED_FINAL_VERDICT_CHECKED.ipynb",
    "trainedRuntime": "Python 3.11.15 • LightGBM 4.6.0 • macOS arm64",
    "featureCount": 273,
    "selectedThreshold": 0.6,
    "deploymentThreshold": 0.6,
    "esi5WeightMultiplier": 0.75,
    "thresholdProfile": "safety_tuned_threshold_0_60_esi5_weight_0_75_raw_probabilities",
    "calibrationMethod": "raw_lightgbm_probability",
    "deployCalibratedProbabilities": false,
    "safetyGateEnabled": true,
    "classScope": "ESI_3_4_5_MODEL_WITH_RULE_ESCALATION",
    "metrics": {
      "accuracy": 0.7832,
      "macroF1": 0.7037,
      "weightedF1": 0.7888,
      "esi5F1": 0.547,
      "unsafeDowngradeRate": 0.0068
    },
    "artifactCheck": {
      "status": "passed",
      "checkedAtLabel": "Final notebook artifact check passed after run-all validation",
      "requiredArtifacts": [
        "esi_345_lightgbm_v2_model.txt",
        "esi_345_lightgbm_v2_preprocessing_artifacts.joblib",
        "esi_345_lightgbm_v2_threshold_config.json",
        "esi_345_label_mapping.json"
      ]
    },
    "notes": []
  }
}
```

## Authentication and roles

The frontend includes local mock auth and local account creation so it can run before backend auth exists. Real deployment should use FastAPI JWT or secure httpOnly session cookies, server-side password hashing, role approval, and organization-based account provisioning.

Default UI permissions:

| Role | Permissions |
|---|---|
| Nurse | create assessment, read assessments, accept decision, generate report |
| Doctor | create assessment, read assessments, accept/override decision, generate report, read audit |
| Admin | read assessments, generate reports, read audit, model monitoring, settings |

## PDF strategy

The frontend can generate a polished PDF for standalone use. For the real product, backend ReportLab should be the official report engine because it can produce controlled, auditable reports and avoid exposing report-generation logic to the browser.


### Register request recommendation

```http
POST /api/v1/auth/register
```

```json
{
  "name": "Priya Nair",
  "email": "priya.nair@hospital.ca",
  "organization": "Calgary Emergency Care Network",
  "unit": "Emergency Department",
  "role": "Nurse",
  "password": "server-side-handled-secret-or-invite-code"
}
```

For a real clinical product, registration should create a pending account until an Admin approves the requested role.

# TriageAI Demo Runbook

## Demo Scope

This runbook prepares and delivers the completed local TriageAI demonstration workflow for a professor or recruiter. TriageAI is a human-in-the-loop clinical decision-support workflow for structured intake, ESI care routing, safety-rule escalation, clinician review, an audit trail, and a PDF decision-support summary.

This runbook does not describe clinical deployment. The demonstration does not diagnose patients, recommend treatment, or replace clinician judgment.

## One Day Before the Demo

- [ ] **Confirm the branch and working tree.** Verify that the intended approved branch is checked out and investigate every unexpected change:

  ```bash
  git status --short --branch
  ```

  Do not pull or prepare the demo until the working tree is clean or every remaining change is explicitly approved.

- [ ] **Pull the latest approved changes.** Use a fast-forward-only pull so preparation does not create an unplanned merge:

  ```bash
  git pull --ff-only
  ```

- [ ] **Verify Docker Compose is available:**

  ```bash
  docker compose version
  ```

- [ ] **Verify the documented demo environment.** Review `.env.example`, `app/frontend/react_app/.env.example`, and `docker-compose.yml`. Confirm the local demo uses:

  - `DATABASE_URL` for local SQLite;
  - `MODEL_REGISTRY_DIR=model_registry/esi_345_lightgbm_v2`;
  - `REPORT_OUTPUT_DIR=reports/generated`;
  - `VITE_USE_MOCK_API=false`;
  - `VITE_API_BASE_URL=http://localhost:8001`.

  Azure Speech credentials are optional; the manual transcript workflow remains available when Azure Speech is not configured. Do not add or display secrets during the demo.

- [ ] **Validate the final model registry:**

  ```bash
  python scripts/validate_model_registry.py
  ```

- [ ] **Test the full Docker workflow.** Run the stack in a dedicated terminal:

  ```bash
  docker compose up --build
  ```

  From another terminal, run the documented smoke test:

  ```bash
  python scripts/api_smoke_test.py --base-url http://127.0.0.1:8001
  ```

  Stop the test stack afterward:

  ```bash
  docker compose down
  ```

- [ ] **Confirm the backend test suite:**

  ```bash
  python -m pytest
  ```

- [ ] **Confirm frontend tests and the React production build.** From the React application directory:

  ```bash
  cd app/frontend/react_app
  npm ci
  npm run test
  npm run build
  cd ../../..
  ```

- [ ] **Confirm PDF generation.** Create a synthetic assessment through the UI, complete clinician review, generate its PDF decision-support summary from Assessment Detail, and verify that the downloaded report matches the stored assessment and reviewed NLP evidence.

- [ ] **Confirm synthetic demo data.** Use only the documented local SQLite workflow:

  ```bash
  python scripts/demo_reset_seed.py --backup --reset --seed --yes
  ```

  The script must report a local SQLite database. Never point the reset workflow at shared, production-like, or externally hosted data.

- [ ] **Inspect all visible demo records.** Confirm that every record is synthetic and that no real patient information, personal data, credentials, or secrets are present.

## Fifteen Minutes Before the Demo

- [ ] Start the existing Compose stack in a dedicated terminal:

  ```bash
  docker compose up --build
  ```

- [ ] In a second terminal, inspect service status:

  ```bash
  docker compose ps
  ```

- [ ] Check FastAPI health on port 8001:

  ```bash
  curl http://localhost:8001/health
  ```

- [ ] Check readiness and inspect the full response:

  ```bash
  curl http://localhost:8001/ready | python -m json.tool
  ```

- [ ] Do not proceed until `/ready` shows `model_loaded: true`, `feature_count: 273`, the expected model registry metadata, and a connected database.

- [ ] Open `http://localhost:5173` and confirm the frontend shows the backend-connected state. Confirm it is using `VITE_API_BASE_URL=http://localhost:8001`, not mock data or another backend.

- [ ] If a fresh Compose dataset is required, run the existing SQLite-safe reset/seed workflow inside the active backend service so it targets the Compose demo database:

  ```bash
  docker compose exec backend python scripts/demo_reset_seed.py --backup --reset --seed --yes
  ```

- [ ] Open **New Intake**, select **Use demo note**, and confirm the synthetic note appears without automatically running NLP extraction or prediction.

- [ ] Complete one backup synthetic assessment through prediction and clinician review. Confirm its Assessment Detail and Audit Trail are consistent.

- [ ] Generate and download one backup PDF decision-support summary. Keep it ready in case live PDF preview is slow.

- [ ] Copy the synthetic demo note below to the clipboard.

- [ ] Close notifications, messaging applications, unrelated browser tabs, and any window that could expose personal information.

## Synthetic Demo Case

> “62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2. Patient looks pale and dizzy.”

This case is fictional and is used only for workflow demonstration.

## Demonstration Page Order

1. Command Center
2. New Intake
3. Clinical NLP review
4. Prediction result
5. Clinician review
6. Assessment Detail
7. Audit Trail
8. Reports and PDF summary
9. Model Monitoring only when time permits

## Live Validation Checklist

- [ ] Backend connected
- [ ] Model loaded
- [ ] Feature count is 273
- [ ] NLP extraction does not auto-run prediction
- [ ] Clinician confirmation is required before prediction
- [ ] Prediction completes
- [ ] Safety-rule status is visible
- [ ] Clinician action persists after navigation or refresh
- [ ] Reviewed NLP evidence appears in the audit trail
- [ ] PDF generation succeeds and matches the stored assessment

## Recovery Procedures

### Docker service does not start

1. Confirm the Docker engine or Docker Desktop is running.
2. Stop the partial stack:

   ```bash
   docker compose down
   ```

3. Retry the documented build and start command:

   ```bash
   docker compose up --build
   ```

4. If it still fails, do not troubleshoot dependencies live. Use the pre-generated PDF to explain the workflow and omit the interactive walkthrough.

### Backend health fails

1. Check the backend service log:

   ```bash
   docker compose logs backend
   ```

2. Restart with `docker compose down`, then `docker compose up --build`.
3. If `/health` still fails, stop the live workflow and use the prepared PDF rather than implying the backend is operational.

### Readiness reports model not loaded

1. Run the repository validator:

   ```bash
   python scripts/validate_model_registry.py
   ```

2. Confirm the registry is `model_registry/esi_345_lightgbm_v2/`, then restart the stack and recheck `/ready`.
3. Do not run or present a prediction unless `model_loaded` is `true` and `feature_count` is `273`.

### Frontend cannot reach backend

1. Confirm `http://localhost:8001/health` succeeds.
2. Confirm the Compose frontend uses `VITE_API_BASE_URL=http://localhost:8001`.
3. Restart the stack once. If the frontend still cannot connect, do not switch to mock data; use the prepared PDF and describe the persisted workflow.

### Azure Speech is unavailable

Use the safe manual path. Paste the synthetic note or enter the transcript directly, explain that Azure Speech is optional, and continue with clinician-reviewed NLP extraction.

### NLP extraction misses a field

Treat the miss as expected review behavior. Correct the editable field, show its evidence or missing status, and confirm clinician review before prediction. Do not rerun extraction repeatedly or claim the original value was verified.

### Prediction request fails

Check `/ready` once. If readiness passes, use the already prepared synthetic assessment to continue with clinician review, audit, and reporting. If readiness fails or the live record is inconsistent, stop the prediction portion.

### Audit event is delayed

Refresh Assessment Detail or Audit Trail once. If the event still does not appear, use the prepared assessment with verified audit evidence and do not claim that the delayed action persisted.

### PDF generation is slow

Keep the request open, move to Assessment Detail or Audit Trail, and show the same stored evidence there. Use the pre-generated backup PDF instead of debugging report generation during the presentation.

### Browser becomes unresponsive

Reopen `http://localhost:5173` once and load the prepared assessment. If the browser remains unstable, continue from the backup PDF and the spoken demo script.

## Demo Stop Conditions

Do not continue the live decision-support workflow when:

- the model is not loaded;
- `/ready` reports a feature count other than 273;
- the frontend is connected to the wrong backend or mock data;
- real patient information, personal data, or secrets are visible;
- prediction, clinician review, or audit persistence is inconsistent;
- report content does not match the stored assessment.

Pause, protect any visible information, and move to the prepared non-interactive material. Do not debug these conditions live or make claims unsupported by the current system state.

## After the Demo

- [ ] Stop Docker services:

  ```bash
  docker compose down
  ```

- [ ] Remove temporary synthetic records if needed through the documented local demo reset/seed workflow before the next presentation. Do not manually delete model artifacts, source files, shared data, or Docker volumes.
- [ ] Confirm that no secrets, personal data, or real patient information appeared on screen, in terminal output, in downloaded reports, or in shared materials.
- [ ] Save professor or recruiter feedback separately from the frozen product.
- [ ] Do not modify the demo-frozen product during the presentation. Review and prioritize feedback afterward through the normal development workflow.

## Final Quick Checklist

- [ ] Correct approved branch; clean working tree
- [ ] Docker Compose available
- [ ] Backend and frontend services running
- [ ] `/health` passes on port 8001
- [ ] `/ready` passes
- [ ] `model_loaded: true`
- [ ] Final registry: `model_registry/esi_345_lightgbm_v2/`
- [ ] `feature_count: 273`
- [ ] Frontend connected to `http://localhost:8001`
- [ ] Synthetic case ready; no real patient information
- [ ] Clinician review confirmation tested
- [ ] Prediction, safety status, and clinician action verified
- [ ] Audit evidence verified
- [ ] Backup PDF decision-support summary ready
- [ ] Notifications and unrelated applications closed

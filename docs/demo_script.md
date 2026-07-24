# TriageAI Professor Demo Script

## Demo Positioning

TriageAI is a human-in-the-loop clinical decision-support workflow for structured intake and ESI care routing. It combines evidence-linked intake extraction, model inference, safety-rule escalation, clinician review, an audit trail, and a PDF decision-support summary. It does not diagnose patients, recommend treatment, or replace clinician judgment.

## Synthetic Demo Case

> “62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2. Patient looks pale and dizzy.”

This case is entirely synthetic and is used only to demonstrate the software workflow.

## Two-Minute Demo Script

### 0:00–0:15 — Introduction and positioning

**Show:** Command Center title and navigation.

**Say:** “TriageAI is a human-in-the-loop clinical decision-support workflow for structured intake and ESI care routing. It does not diagnose, recommend treatment, or replace clinician judgment. I’ll show how it makes every AI-assisted step reviewable.”

### 0:15–0:30 — Command Center and backend/model readiness

**Show:** Command Center summary cards and the backend/model readiness indicator.

**Say:** “The React application is connected to FastAPI, and the backend confirms that the model and database are ready. The backend is the source of truth for assessments, predictions, reviews, audit events, and reports.”

### 0:30–0:55 — New Intake and clinical NLP extraction

**Show:** Open **New Intake**, select **Use demo note**, point to the note, and click **Extract Intake Fields**.

**Say:** “I’m using a synthetic note with chest pain, shortness of breath, abnormal vital signs, and one missing vital. The same workflow also accepts an editable transcript from recorded audio. Extraction runs only when I request it through `/nlp/extract-intake`.”

### 0:55–1:10 — Clinician review before prediction

**Show:** Clinical NLP review panel, evidence snippets, safety cues, missing respiratory rate, editable fields, and the review-confirmation control.

**Say:** “The system links extracted values to source evidence, flags respiratory rate as missing instead of inventing it, and keeps every field editable. Prediction remains blocked until the clinician reviews, corrects, and confirms the structured intake.”

### 1:10–1:30 — LightGBM prediction and safety-rule escalation

**Show:** Confirm review, run ESI decision support, and display the prediction result, probabilities, and safety escalation.

**Say:** “The reviewed intake is sent to `/predict`, where the LightGBM V2 ESI 3/4/5 model runs. Transparent safety rules evaluate high-risk signals separately and can escalate the routing result for urgent clinician review.”

### 1:30–1:45 — Clinician accept, override, or further review

**Show:** Clinician review controls for accept, override, and further review.

**Say:** “The output is not an autonomous decision. The clinician can accept it, override it with a documented reason, or mark the case for further review. Clinician judgment remains required.”

### 1:45–2:00 — Audit trail, PDF summary, and conclusion

**Show:** Assessment Detail or Audit Trail, then the PDF report action or preview.

**Say:** “Reviewed NLP evidence, prediction details, safety-rule escalation, clinician action, and report events remain visible in the audit trail. The backend-generated PDF decision-support summary carries the same evidence and disclaimer. The achievement is the reviewable workflow around the model.”

## Five-Minute Demo Script

### 0:00–0:35 — Problem and safe positioning

**Show:** Command Center landing page and the main workflow navigation.

**Say:** “Clinical intake arrives as structured fields, typed notes, pasted transcripts, or spoken narratives. A model-only prototype cannot show whether extracted data was correct, whether safety rules changed the result, or who made the final decision. TriageAI addresses that workflow gap. It is a human-in-the-loop clinical decision-support workflow for structured intake and ESI care routing. It does not diagnose patients, recommend treatment, make autonomous clinical decisions, or replace clinician judgment.”

### 0:35–1:05 — Architecture and source of truth

**Show:** System Architecture view if available; otherwise, use the navigation and Command Center readiness indicator to describe the flow.

**Say:** “The React frontend collects and displays workflow state, while FastAPI owns validation, speech and NLP services, model inference, safety rules, persistence, clinician review, the audit trail, and PDF generation. The backend and database are the source of truth, so the dashboard, assessment detail, review history, and reports all use the same persisted record. SQLite supports this local demo, and PostgreSQL is the recommended database for a controlled professional deployment.”

### 1:05–2:05 — Note or recorded-speech intake and NLP extraction

**Show:** Open **New Intake**. Briefly point to the recording control and transcript area, then use **Use demo note** and click **Extract Intake Fields**.

**Say:** “Intake can be typed, pasted, or recorded. Recorded audio is submitted explicitly to `/speech/transcribe`; Azure Speech is supported when configured, and the backend returns a safe fallback when it is unavailable. The transcript remains editable before it enters the clinical note. For a reliable live demo, I’ll use this synthetic note: 62-year-old male with chest pain and shortness of breath, heart rate 118, blood pressure 92 over 60, oxygen saturation 91 percent, temperature 38.2, and a pale, dizzy appearance. Selecting the note does not start extraction or prediction. I explicitly call `/nlp/extract-intake`, which returns structured fields, source-text evidence, safety cues, and missing-information indicators.”

### 2:05–2:40 — Evidence review and mandatory confirmation

**Show:** Expand or scroll through the Clinical NLP review panel. Point to age, chief complaint, symptoms, vital signs, evidence snippets, safety cues, missing respiratory rate, and the confirmation checkbox.

**Say:** “The extracted age, complaint, symptoms, and vital signs remain editable. Evidence snippets show where each value came from, while the safety cues highlight chest pain, shortness of breath, low oxygen, low blood pressure, and tachycardia. Respiratory rate is visibly missing because the system does not invent absent data. I must correct any errors and confirm that I reviewed the extraction before prediction is enabled.”

### 2:40–3:25 — LightGBM prediction and transparent safety layer

**Show:** Confirm clinician review, select **Run ESI Decision Support**, and point to predicted ESI, final ESI, confidence, probabilities, model metadata, and triggered safety rules.

**Say:** “The reviewed structured intake now goes to `/predict`. FastAPI validates it, builds the 273-feature representation, and runs the LightGBM V2 ESI 3/4/5 model. The model version is `lightgbm_v2_weight_threshold_esi345`, the class order is `ESI_3`, `ESI_4`, `ESI_5`, and the decision threshold is 0.60. The model output and safety-rule escalation are displayed separately. If a configured high-risk condition triggers, the safety layer can escalate the routing output for urgent clinician review; it does not create a diagnosis or bypass the clinician.”

### 3:25–4:05 — Clinician decision and audit trail

**Show:** Clinician review controls, submit or display an accept, override, or further-review decision, then open **Assessment Detail** or **Audit Trail**.

**Say:** “The clinician can accept the model-and-safety result, override it with a required reason, or mark the assessment for further review. That action is persisted rather than stored only in the browser. In the audit trail, I can trace assessment creation, prediction metadata, the reviewed NLP evidence, safety behavior, the clinician decision, an override reason when applicable, and report events. This makes correction and accountability part of the workflow instead of an afterthought.”

### 4:05–4:30 — Reports and PDF decision-support summary

**Show:** Reports or Assessment Detail, select the PDF action, and show the generated PDF summary or download control.

**Say:** “The official PDF is generated by the backend from the persisted assessment. It includes the structured intake, model and safety output, clinician review, reviewed NLP evidence, audit context, and a clear decision-support disclaimer. Backend generation keeps the downloadable summary consistent with the source-of-truth record.”

### 4:30–5:00 — Testing, limitations, and conclusion

**Show:** Return to Command Center or Model Monitoring and keep the readiness indicator visible.

**Say:** “The final demo freeze completed 90 passing backend tests, 12 frontend test files with 38 tests, a passing React production build, and a passing Docker full-stack run. The selected model’s accuracy is 78.32%, and its unsafe ESI 3-to-ESI 5 downgrade rate is 0.68%. These validate the local workflow and artifact; they are not clinical validation. The main result is an auditable, review-first engineering system around the model, with clinician judgment still required.”

### Verified Demo Facts

- model: LightGBM V2 ESI 3/4/5
- model version: `lightgbm_v2_weight_threshold_esi345`
- feature count: 273
- class order: `ESI_3`, `ESI_4`, `ESI_5`
- decision threshold: 0.60
- accuracy: 78.32%
- Macro F1: 70.37%
- Weighted F1: 78.88%
- ESI 5 F1: 54.70%
- unsafe ESI 3-to-ESI 5 downgrade rate: 0.68%
- backend: 90 passing tests
- frontend: 12 test files and 38 tests
- React production build passed
- Docker full-stack run passed

## Demo Page Order

1. Command Center
2. New Intake
3. Clinical NLP review
4. Prediction result
5. Clinician review
6. Assessment Detail or Audit Trail
7. Reports or PDF summary

## Questions the Professor May Ask

### Is this a diagnostic system?

No. TriageAI is a clinical decision-support workflow for structured intake and ESI care routing. It does not diagnose, recommend treatment, or replace clinician judgment.

### Why did you use LightGBM?

LightGBM performed well on the approved structured feature representation and supports fast, reproducible backend inference. The selected artifact balances overall classification quality with the safety-sensitive ESI 5 behavior measured during evaluation.

### Why is clinician review required before prediction?

NLP extraction can miss context or misread a value. Mandatory review prevents unverified extracted data from silently becoming model input and gives the clinician a clear correction point.

### What happens when the model and safety rules differ?

The model prediction and safety-rule escalation remain visible as separate stages. A configured safety rule can escalate the final routing output for urgent clinician review, after which the clinician can accept, override, or request further review.

### What is stored in the audit trail?

The backend records assessment and prediction events, reviewed structured NLP evidence, safety behavior, clinician decisions, override reasons when applicable, and report-generation events. Raw recorded audio is not persisted, and raw note text is excluded from NLP audit evidence.

### Why did you use backend-generated PDFs?

The backend can build the PDF decision-support summary from the same persisted assessment, prediction, review, and audit data used by the application. This prevents a browser-only report from drifting away from the source-of-truth record.

### Is the system ready for real clinical deployment?

No. It is ready for local demonstration, not clinical production. Prospective clinical validation, usability and fairness studies, production authentication, privacy and security controls, managed infrastructure, observability, governance, and regulatory assessment would still be required.

### What was the most difficult engineering problem?

The hardest part was preserving explicit review gates and evidence across the entire workflow. The implementation had to keep transcript review, NLP correction, prediction, safety escalation, clinician action, audit storage, and PDF reporting consistent without allowing one step to silently authorize the next.

### Why is the backend the source of truth?

Backend ownership gives every page the same persisted assessment, prediction, review, audit, and report state. It avoids browser-only records, keeps model execution off the frontend, and makes the workflow traceable.

### How did you validate the final workflow?

The demo freeze completed 90 passing backend tests, 12 frontend test files and 38 tests, a passing React production build, backend readiness checks, and a passing Docker full-stack run. Those results validate the local software workflow, not clinical effectiveness.

## Demo Recovery Lines

### Azure Speech is unavailable

“Azure Speech is optional. The backend has returned the safe fallback, so I’ll continue with the editable manual transcript path.”

### NLP misses or misreads a field

“This is why review is mandatory. I can correct the extracted field here, and the corrected value—not the unverified extraction—is submitted for prediction.”

### Respiratory rate is missing

“The note does not contain respiratory rate, so the NLP layer leaves it missing instead of inventing a value. I would document it before continuing if the workflow requires it.”

### Model confidence is limited

“The probabilities and confidence are visible rather than hidden. Limited confidence reinforces that this is decision-support only and that clinician judgment remains required.”

### A safety rule escalates the result

“The escalation is intentional and transparent. The model output remains visible, the safety rule explains why the routing result changed, and the clinician still makes the final decision.”

### PDF preview is slow

“The report is generated from the same persisted backend record. While it loads, I can show the equivalent reviewed evidence, prediction, clinician action, and report event in Assessment Detail and the audit trail.”

### The professor asks whether it can be used clinically

“No. This is a local portfolio and educational demonstration. Real clinical use would require prospective validation, security and privacy controls, governance, regulatory assessment, and organizational approval.”

## Final Closing Statement

“The main achievement in TriageAI is not simply producing an ESI class. It is the engineering workflow around that model: structured intake, evidence-linked extraction, correction before prediction, transparent safety-rule escalation, clinician review, an audit trail, and a backend-generated PDF decision-support summary. Every consequential step remains reviewable, and clinician judgment remains required.”

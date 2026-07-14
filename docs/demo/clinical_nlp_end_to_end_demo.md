# Clinical Intake NLP Safety Layer: End-to-End Demo

## Demo Note

> 62-year-old male with chest pain and shortness of breath. HR 118, BP 92/60, O2 91%, temp 38.2. Patient looks pale and dizzy.

Use this scenario only to demonstrate the reviewed clinical intake workflow. It is synthetic and intended for workflow testing.

## Demo Workflow

1. Open **New Assessment**.
2. Click **Use demo note**. Confirm that the note appears in the clinical note text area and that no extraction or prediction starts automatically.
3. Click **Extract Intake Fields**.
4. Review the extracted values and edit any structured fields if needed.
5. Check the clinician review confirmation: **I reviewed the extracted fields before prediction**.
6. Complete any required intake fields, then click **Run ESI Decision Support**.
7. Open **Assessment Detail** after the assessment is created.
8. Review the **Clinical NLP Review Evidence** card in the assessment audit trail.
9. Open the **Audit** page and locate the same reviewed NLP evidence for the assessment.
10. Generate or download the PDF report and locate the **Clinical NLP Review Evidence** section.

The **Use demo note** action fills the note field only. Extraction and ESI decision support remain separate, explicit actions, and reviewed NLP fields are not submitted until the clinician review confirmation is checked.

## Expected Extracted Fields

| Field | Expected value |
| --- | --- |
| Age | 62 |
| Gender | Male |
| Chief complaint | chest pain |
| Symptoms | chest pain; shortness of breath; dizziness |
| Heart rate | 118 |
| Systolic blood pressure | 92 |
| Diastolic blood pressure | 60 |
| Oxygen saturation | 91 |
| Temperature | 38.2 |
| Respiratory rate | Missing |

Expected evidence snippets include `62-year-old`, `chest pain`, `shortness of breath`, `dizzy`, `HR 118`, `BP 92/60`, `O2 91%`, and `temp 38.2`.

## Expected Safety Cues

- chest pain
- shortness of breath
- low oxygen
- low blood pressure
- tachycardia

The extraction should also flag **respiratory rate** as a missing field. These cues support visibility and clinician review; they do not independently determine or validate an ESI level.

## Safe Demo Explanation

The Clinical Intake NLP Safety Layer converts a synthetic note into editable structured intake fields and evidence snippets. The clinician reviews those fields before prediction. Once reviewed, the system records the structured extraction evidence in the existing assessment audit trail and presents the same safe evidence summary in Assessment Detail, the Audit page, and the PDF report.

The workflow does not auto-run prediction, bypass clinician review, or use the NLP extraction to make, confirm, or validate an ESI decision. It does not add treatment recommendations. Raw clinical note text is excluded from NLP audit metadata and PDF evidence; only approved structured fields and evidence snippets are shown. Clinician judgment and the existing backend safety rules remain authoritative.

## Portfolio Wording

> This demo shows structured intake extraction, clinician review before prediction, audit-trail evidence, and PDF decision-support documentation. It is not diagnosis and does not replace clinician judgment.

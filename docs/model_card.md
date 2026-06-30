# Model Card

## Purpose

The Phase 4 model integration supports ESI 3/4/5 decision-support routing for
clinical intake workflow testing. It is not diagnostic and does not replace
clinician judgment.

## Scope

The saved artifact target is ESI 3, ESI 4, and ESI 5 only. Higher-acuity safety
concerns are handled through transparent safety rules that can escalate the
final ESI recommendation for urgent clinician review.

## Training Data

Artifacts are generated outside FastAPI by the active ESI 3/4/5 training
pipeline. Raw datasets are not committed to the repository. Backend inference
uses only intake-safe fields such as age, chief complaint, symptom duration,
selected vitals, arrival context, and lightweight text-derived flags.

## Evaluation

Verified metrics for the saved artifact family:

- Accuracy: 78.35%
- Macro F1: 70.42%
- Weighted F1: 78.91%
- ESI 5 F1: 54.78%
- ESI 3 to ESI 5 safety error: 0.71%

## Leakage Prevention

The backend feature builder avoids post-triage leakage fields such as diagnosis,
disposition, lab results, medications, and outcomes. It builds features only from
the submitted intake request and the approved feature schema.

## Safety Rules

Transparent safety rules flag oxygen saturation below 92%, altered
consciousness wording, chest pain with shortness of breath, severe bleeding
wording, and pregnancy with bleeding wording. These rules are conservative
workflow safeguards and are not a complete clinical triage protocol.

## Limitations

The model is limited to ESI 3/4/5 classes and should be interpreted as
decision-support only. Missing, incomplete, or ambiguous intake data may reduce
reliability. The system does not diagnose, provide treatment instructions, or
tell patients to ignore emergency symptoms.

## Human Oversight

Every prediction requires clinician review before care routing decisions are
made. The API response includes a disclaimer and stores prediction metadata for
auditability.

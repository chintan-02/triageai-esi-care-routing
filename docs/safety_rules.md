# Safety Rules

## Escalation Rules

Phase 4 includes transparent, conservative safety flags:

- Oxygen saturation below 92% flags respiratory risk.
- Consciousness wording such as confusion, altered, or unresponsive flags altered consciousness.
- Chest pain or chest discomfort with shortness of breath flags a cardiopulmonary red flag.
- Severe or heavy bleeding wording flags a bleeding red flag.
- Pregnancy with bleeding wording flags a pregnancy red flag.

When a high-risk flag is triggered during model-backed prediction, the final ESI
may be escalated to ESI 2 for urgent clinician review. The response explains the
triggering rule.

## Guardrails

Safety rules are not a complete triage system and are not diagnostic. They are
workflow safeguards layered on top of the ESI 3/4/5 model output.

The system must not make clinical claims beyond the explicit rule messages, and
it must not advise a patient to ignore emergency symptoms.

## Review Requirements

All prediction outputs require clinician review. Clinician actions are persisted
with audit metadata in the Phase 3 database layer.

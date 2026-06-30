"""Transparent ESI safety rule helpers."""

from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import SafetyRuleResult


def evaluate_basic_safety_rules(
    intake: PatientIntakeRequest,
) -> list[SafetyRuleResult]:
    triggered_rules: list[SafetyRuleResult] = []
    complaint = (intake.chief_complaint or "").lower()
    context = (intake.additional_context or "").lower()
    combined_text = f"{complaint} {context}"
    consciousness = (intake.consciousness_level or "").lower()

    if intake.oxygen_saturation is not None and intake.oxygen_saturation < 92:
        triggered_rules.append(
            SafetyRuleResult(
                rule_id="oxygen_saturation_below_92",
                triggered=True,
                message="Oxygen saturation below 92% flagged for urgent clinician review.",
                is_placeholder=False,
            )
        )

    if any(term in consciousness for term in ("confused", "confusion", "unresponsive", "altered")):
        triggered_rules.append(
            SafetyRuleResult(
                rule_id="altered_consciousness",
                triggered=True,
                message="Altered consciousness wording flagged for urgent clinician review.",
                is_placeholder=False,
            )
        )

    has_chest_pain = "chest pain" in combined_text or "chest discomfort" in combined_text
    has_shortness_of_breath = any(
        term in combined_text
        for term in ("shortness of breath", "difficulty breathing", "breathless", " sob ")
    )
    if has_chest_pain and has_shortness_of_breath:
        triggered_rules.append(
            SafetyRuleResult(
                rule_id="cardiopulmonary_red_flag",
                triggered=True,
                message=(
                    "Chest pain with shortness of breath flagged for urgent clinician review."
                ),
                is_placeholder=False,
            )
        )

    has_bleeding = any(
        term in combined_text
        for term in ("severe bleeding", "heavy bleeding", "bleeding heavily", "hemorrhage")
    )
    if has_bleeding:
        triggered_rules.append(
            SafetyRuleResult(
                rule_id="bleeding_red_flag",
                triggered=True,
                message="Severe bleeding wording flagged for urgent clinician review.",
                is_placeholder=False,
            )
        )

    if intake.pregnancy is True and "bleeding" in combined_text:
        triggered_rules.append(
            SafetyRuleResult(
                rule_id="pregnancy_bleeding_red_flag",
                triggered=True,
                message="Pregnancy with bleeding wording flagged for urgent clinician review.",
                is_placeholder=False,
            )
        )

    return triggered_rules


def apply_safety_rules(
    predicted_esi: int | None,
    safety_rules: list[SafetyRuleResult],
) -> tuple[int | None, str]:
    if any(rule.triggered for rule in safety_rules):
        return 2, "safety_rule_override"
    return predicted_esi, "model"

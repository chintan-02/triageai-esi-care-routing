"""Contract-only safety rule placeholder service."""

from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import SafetyRuleResult


def evaluate_basic_safety_rules(
    intake: PatientIntakeRequest,
) -> list[SafetyRuleResult]:
    _ = intake
    return []

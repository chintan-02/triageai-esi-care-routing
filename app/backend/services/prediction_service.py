"""ESI prediction contract validation service."""

from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import ESIPredictionResponse
from app.backend.services.care_routing_service import build_placeholder_recommendation
from app.backend.services.clinician_summary_service import (
    build_placeholder_clinician_summary,
)
from app.backend.services.explanation_service import build_placeholder_explanation
from app.backend.services.safety_rules import evaluate_basic_safety_rules
from app.backend.utils.ids import new_id


DECISION_SUPPORT_DISCLAIMER = (
    "This contract-only response is for clinical decision support workflow "
    "testing only and is not a diagnosis or a substitute for clinician judgment."
)


def validate_prediction_contract(
    intake: PatientIntakeRequest,
) -> ESIPredictionResponse:
    return ESIPredictionResponse(
        request_id=new_id(),
        acuity_scale="ESI",
        model_loaded=False,
        predicted_esi=None,
        final_esi=None,
        confidence_score=None,
        probabilities={},
        safety_rules_triggered=evaluate_basic_safety_rules(intake),
        final_source="contract_placeholder",
        recommendation=build_placeholder_recommendation(),
        explanation=build_placeholder_explanation(),
        clinician_summary=build_placeholder_clinician_summary(),
        is_placeholder=True,
        disclaimer=DECISION_SUPPORT_DISCLAIMER,
    )

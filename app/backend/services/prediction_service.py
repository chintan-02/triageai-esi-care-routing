"""ESI prediction service with graceful model-artifact fallback."""

from typing import Any

import numpy as np

from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.schemas.prediction import ESIPredictionResponse
from app.backend.services.care_routing_service import (
    build_care_recommendation,
    build_placeholder_recommendation,
)
from app.backend.services.clinician_summary_service import (
    build_clinician_summary,
    build_placeholder_clinician_summary,
)
from app.backend.services.explanation_service import (
    build_placeholder_explanation,
    build_prediction_explanation,
)
from app.backend.services.feature_builder import build_model_input
from app.backend.services.model_loader import get_model_bundle
from app.backend.services.safety_rules import (
    apply_safety_rules,
    evaluate_basic_safety_rules,
)
from app.backend.utils.ids import new_id


DECISION_SUPPORT_DISCLAIMER = (
    "This response is for clinical decision support workflow testing only and "
    "is not a diagnosis or a substitute for clinician judgment."
)


def validate_prediction_contract(
    intake: PatientIntakeRequest,
) -> ESIPredictionResponse:
    _ = intake
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


def _label_to_esi(label: str) -> int | None:
    digits = "".join(character for character in str(label) if character.isdigit())
    if not digits:
        return None
    esi_value = int(digits)
    if 1 <= esi_value <= 5:
        return esi_value
    return None


def _probabilities_from_model_output(
    predict_proba_output: Any,
    class_labels: list[str],
) -> dict[str, float]:
    probabilities_array = np.asarray(predict_proba_output)
    if probabilities_array.ndim == 2:
        probabilities_array = probabilities_array[0]

    probabilities: dict[str, float] = {}
    for index, probability in enumerate(probabilities_array):
        if index >= len(class_labels):
            break
        probabilities[class_labels[index]] = float(probability)
    return probabilities


def _threshold_class_order(
    thresholds: dict[str, Any] | None,
    probabilities: dict[str, float],
) -> list[str]:
    if thresholds and isinstance(thresholds.get("class_order"), list):
        return [str(label) for label in thresholds["class_order"]]

    return sorted(probabilities, key=lambda label: _label_to_esi(label) or 99)


def _select_prediction(
    probabilities: dict[str, float],
    thresholds: dict[str, Any] | None,
) -> tuple[int | None, float | None]:
    if not probabilities:
        return None, None

    confidence = max(probabilities.values())

    if thresholds and thresholds.get("strategy") == "esi5_threshold_then_argmax":
        esi5_threshold = thresholds.get("esi5_threshold")
        esi5_probability = probabilities.get("ESI_5")
        if (
            esi5_threshold is not None
            and esi5_probability is not None
            and esi5_probability >= float(esi5_threshold)
        ):
            return 5, confidence

    threshold_values = thresholds.get("thresholds") if thresholds else None
    if isinstance(threshold_values, dict):
        for label in _threshold_class_order(thresholds, probabilities):
            threshold = threshold_values.get(label)
            if threshold is not None and probabilities.get(label, 0.0) >= float(threshold):
                return _label_to_esi(label), confidence

    best_label = max(probabilities.items(), key=lambda item: item[1])[0]
    return _label_to_esi(best_label), confidence


def _run_model_predict(model: Any, model_input: Any) -> Any:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(model_input)
    return model.predict(model_input)


def predict_esi_for_intake(intake: PatientIntakeRequest) -> ESIPredictionResponse:
    bundle = get_model_bundle()
    if not bundle.loaded:
        return validate_prediction_contract(intake)

    model_input = build_model_input(intake, bundle.feature_schema or {})
    raw_probabilities = _run_model_predict(bundle.model, model_input)
    probabilities = _probabilities_from_model_output(
        raw_probabilities,
        bundle.class_labels or ["ESI_3", "ESI_4", "ESI_5"],
    )
    predicted_esi, confidence_score = _select_prediction(
        probabilities,
        bundle.thresholds,
    )
    safety_rules = evaluate_basic_safety_rules(intake)
    final_esi, final_source = apply_safety_rules(predicted_esi, safety_rules)

    return ESIPredictionResponse(
        request_id=new_id(),
        acuity_scale="ESI",
        model_version=bundle.model_version,
        model_loaded=True,
        predicted_esi=predicted_esi,
        final_esi=final_esi,
        confidence_score=confidence_score,
        probabilities=probabilities,
        safety_rules_triggered=safety_rules,
        final_source=final_source,
        recommendation=build_care_recommendation(final_esi, model_loaded=True),
        explanation=build_prediction_explanation(
            predicted_esi=predicted_esi,
            final_esi=final_esi,
            probabilities=probabilities,
            safety_rules=safety_rules,
            model_loaded=True,
        ),
        clinician_summary=build_clinician_summary(
            intake=intake,
            predicted_esi=predicted_esi,
            final_esi=final_esi,
            safety_rules=safety_rules,
            probabilities=probabilities,
        ),
        is_placeholder=False,
        disclaimer=DECISION_SUPPORT_DISCLAIMER,
    )

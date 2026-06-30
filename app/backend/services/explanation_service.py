"""Prediction explanation placeholder service."""

from app.backend.schemas.prediction import SafetyRuleResult


def build_placeholder_explanation() -> str:
    return (
        "No clinical explanation is generated yet. This is a contract-only "
        "placeholder response."
    )


def build_prediction_explanation(
    predicted_esi: int | None,
    final_esi: int | None,
    probabilities: dict[str, float],
    safety_rules: list[SafetyRuleResult],
    model_loaded: bool,
) -> str:
    if not model_loaded:
        return build_placeholder_explanation()

    if probabilities:
        probability_summary = ", ".join(
            f"{label}: {probability:.2f}" for label, probability in probabilities.items()
        )
        confidence = max(probabilities.values())
    else:
        probability_summary = "No class probabilities were returned."
        confidence = None

    parts = [
        f"Model predicted ESI {predicted_esi} and final ESI is {final_esi}.",
        f"Class probabilities: {probability_summary}.",
    ]
    if confidence is not None:
        parts.append(f"Highest model probability was {confidence:.2f}.")

    triggered = [rule for rule in safety_rules if rule.triggered]
    if triggered and final_esi != predicted_esi:
        reasons = "; ".join(rule.message for rule in triggered)
        parts.append(f"Safety rules changed the final ESI to {final_esi}: {reasons}")
    else:
        parts.append("Final ESI is based on the model output without safety escalation.")

    parts.append(
        "This is decision-support output only and is not a diagnosis or a substitute "
        "for clinician judgment; clinician review is required."
    )
    return " ".join(parts)

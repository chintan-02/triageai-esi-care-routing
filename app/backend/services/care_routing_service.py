"""Care routing recommendation service."""


def build_placeholder_recommendation() -> str:
    return (
        "Model inference is not connected yet. This endpoint validates the "
        "request contract only."
    )


def build_care_recommendation(final_esi: int | None, model_loaded: bool) -> str:
    if not model_loaded or final_esi is None:
        return build_placeholder_recommendation()

    recommendations = {
        2: (
            "High-priority clinician review recommended due to safety flags. "
            "Decision-support only; clinician judgment is required."
        ),
        3: (
            "Urgent evaluation recommended; patient may require multiple resources. "
            "Decision-support only; clinician judgment is required."
        ),
        4: (
            "Lower-acuity evaluation pathway may be appropriate after clinician review. "
            "Decision-support only; clinician judgment is required."
        ),
        5: (
            "Non-urgent care pathway may be appropriate after clinician review. "
            "Decision-support only; clinician judgment is required."
        ),
    }
    return recommendations.get(
        final_esi,
        "Clinician review recommended before selecting a care pathway.",
    )

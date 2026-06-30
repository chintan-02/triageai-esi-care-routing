"""Run a sample ESI prediction from local artifacts when available."""

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.services.model_loader import reload_model_bundle
from app.backend.services.prediction_service import predict_esi_for_intake


SAMPLE_PATH = Path("data/sample/sample_intake_cases.json")


def _load_sample_payload() -> dict[str, object]:
    with SAMPLE_PATH.open(encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, list) and payload:
        return payload[0]
    if isinstance(payload, dict):
        return payload

    return {
        "patient_age": 45,
        "sex": "female",
        "chief_complaint": "Chest discomfort",
        "pain_score": 6,
        "oxygen_saturation": 98.0,
    }


def main() -> int:
    bundle = reload_model_bundle()
    if not bundle.loaded:
        print(f"Model artifacts unavailable: {bundle.error_message}")
        return 0

    intake = PatientIntakeRequest(**_load_sample_payload())
    response = predict_esi_for_intake(intake)
    print(f"predicted_esi: {response.predicted_esi}")
    print(f"probabilities: {response.probabilities}")
    print(f"final_esi: {response.final_esi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

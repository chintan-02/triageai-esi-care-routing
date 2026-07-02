from fastapi.testclient import TestClient

from app.backend.api.main import app
from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.services import prediction_service
from app.backend.services.model_loader import ModelBundle
from app.backend.services.safety_rules import (
    apply_safety_rules,
    evaluate_basic_safety_rules,
)


client = TestClient(app)


class FakeModel:
    def predict(self, model_input):
        return [[0.1, 0.2, 0.7]]


def base_intake_payload() -> dict[str, object]:
    return {
        "patient_age": 56,
        "sex": "male",
        "chief_complaint": "Chest discomfort",
        "symptom_duration": "1 hour",
        "pain_score": 5,
        "temperature_c": 36.8,
        "heart_rate": 115,
        "respiratory_rate": 22,
        "systolic_bp": 135,
        "diastolic_bp": 85,
        "oxygen_saturation": 96.0,
        "consciousness_level": "alert",
        "pregnancy": False,
        "arrival_mode": "Walk-in",
        "additional_context": "Reports shortness of breath.",
    }


def test_low_oxygen_saturation_rule_escalates_to_esi_2() -> None:
    intake = PatientIntakeRequest(
        **{
            **base_intake_payload(),
            "oxygen_saturation": 88.0,
            "additional_context": "No other red flags documented.",
        }
    )

    rules = evaluate_basic_safety_rules(intake)
    final_esi, final_source = apply_safety_rules(predicted_esi=5, safety_rules=rules)

    assert final_esi == 2
    assert final_source == "safety_rule_override"
    assert [rule.rule_id for rule in rules] == ["oxygen_saturation_below_92"]
    assert "urgent clinician review" in rules[0].message


def test_cardiopulmonary_red_flag_rule_escalates_to_esi_2() -> None:
    intake = PatientIntakeRequest(**base_intake_payload())

    rules = evaluate_basic_safety_rules(intake)
    final_esi, final_source = apply_safety_rules(predicted_esi=4, safety_rules=rules)

    assert final_esi == 2
    assert final_source == "safety_rule_override"
    assert [rule.rule_id for rule in rules] == ["cardiopulmonary_red_flag"]
    assert rules[0].triggered is True


def test_predict_endpoint_persists_safety_rule_escalation(monkeypatch) -> None:
    monkeypatch.setattr(
        prediction_service,
        "get_model_bundle",
        lambda: ModelBundle(
            model=FakeModel(),
            thresholds=None,
            feature_schema={},
            loaded=True,
            model_version="test-model",
            class_labels=["ESI_3", "ESI_4", "ESI_5"],
        ),
    )

    response = client.post(
        "/predict",
        json={
            **base_intake_payload(),
            "oxygen_saturation": 88.0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assessment_id"]
    assert body["predicted_esi"] in [3, 4, 5]
    assert body["final_esi"] == 2
    assert body["final_source"] == "safety_rule_override"
    assert body["probabilities"]
    assert set(body["probabilities"]) == {"ESI_3", "ESI_4", "ESI_5"}
    triggered_rule_ids = [
        rule["rule_id"] for rule in body["safety_rules_triggered"] if rule["triggered"]
    ]
    assert "oxygen_saturation_below_92" in triggered_rule_ids
    assert "cardiopulmonary_red_flag" in triggered_rule_ids

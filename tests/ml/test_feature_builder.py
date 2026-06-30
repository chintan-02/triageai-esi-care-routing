from app.backend.schemas.intake import PatientIntakeRequest
from app.backend.services.feature_builder import (
    align_features_to_schema,
    build_model_input,
    build_raw_features_from_intake,
)
import json
import pandas as pd
from pathlib import Path


def test_valid_intake_builds_feature_dictionary() -> None:
    intake = PatientIntakeRequest(
        patient_age=42,
        sex="female",
        chief_complaint="Chest pain and shortness of breath",
        pain_score=7,
        oxygen_saturation=97.0,
    )

    features = build_raw_features_from_intake(intake)

    assert features["patient_age"] == 42
    assert features["chief_complaint_clean"] == "chest pain and shortness of breath"
    assert features["complaint_length"] > 0


def test_chief_complaint_text_features_are_extracted() -> None:
    intake = PatientIntakeRequest(
        patient_age=30,
        chief_complaint="Severe headache with dizziness and vomiting",
    )

    features = build_raw_features_from_intake(intake)

    assert features["has_headache"] == 1
    assert features["has_dizziness"] == 1
    assert features["has_vomiting"] == 1
    assert features["has_severe_keyword"] == 1


def test_feature_alignment_handles_placeholder_schema() -> None:
    intake = PatientIntakeRequest(
        patient_age=30,
        chief_complaint="Mild ankle injury",
    )

    frame = build_model_input(intake, {"version": "0.1.0", "features": []})

    assert frame.shape[0] == 1
    assert "patient_age" in frame.columns
    assert "has_injury" in frame.columns


def test_feature_alignment_fills_missing_schema_columns() -> None:
    raw_features = {"patient_age": 30}

    frame = align_features_to_schema(
        raw_features,
        {"features": ["patient_age", "has_fever", "unknown_text"]},
    )

    assert list(frame.columns) == ["patient_age", "has_fever", "unknown_text"]
    assert frame.iloc[0]["has_fever"] == 0
    assert pd.isna(frame.iloc[0]["unknown_text"])


def test_generated_feature_schema_contains_expected_v2_features() -> None:
    with Path("model_artifacts/feature_schema.json").open() as file:
        feature_schema = json.load(file)

    assert feature_schema["feature_count"] == 272
    for feature in [
        "age",
        "triage_vital_hr",
        "triage_vital_sbp",
        "triage_vital_o2",
        "cc_chestpain",
        "cc_shortnessofbreath",
    ]:
        assert feature in feature_schema["features"]

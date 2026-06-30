import json
from pathlib import Path

from app.backend.core.config import settings
from app.backend.services.model_loader import load_model_bundle
from ml.inference.validate_artifacts import validate_artifacts


def test_model_artifact_placeholders_are_valid_json() -> None:
    artifact_dir = Path("model_artifacts")

    for filename in ["thresholds.json", "feature_schema.json", "model_metadata.json"]:
        with (artifact_dir / filename).open() as file:
            json.load(file)


def test_lightgbm_text_artifacts_do_not_require_joblib_files() -> None:
    bundle = load_model_bundle(settings)

    assert Path(settings.MODEL_PATH).name == "esi_345_lightgbm_v2_threshold.txt"
    assert not Path("model_artifacts/esi_345_lightgbm_v2_threshold.joblib").exists()
    assert not Path("model_artifacts/esi_345_preprocessor.joblib").exists()
    assert bundle.model_version == "esi_345_lightgbm_v2_threshold"
    assert bundle.class_labels == ["ESI_3", "ESI_4", "ESI_5"]
    assert bundle.error_message is None or "joblib" not in bundle.error_message.lower()
    assert bundle.error_message is None or "preprocessor" not in bundle.error_message.lower()


def test_validate_artifacts_accepts_lightgbm_text_contract() -> None:
    assert validate_artifacts() is True


def test_feature_schema_matches_v2_booster() -> None:
    with Path("model_artifacts/feature_schema.json").open() as file:
        feature_schema = json.load(file)

    assert feature_schema["feature_count"] == 272
    assert "age" in feature_schema["features"]
    assert "triage_vital_hr" in feature_schema["features"]
    assert "triage_vital_sbp" in feature_schema["features"]
    assert "triage_vital_o2" in feature_schema["features"]
    assert "cc_chestpain" in feature_schema["features"]
    assert "cc_shortnessofbreath" in feature_schema["features"]


def test_thresholds_match_v2_staging_config() -> None:
    with Path("model_artifacts/thresholds.json").open() as file:
        thresholds = json.load(file)

    assert thresholds["strategy"] == "esi5_threshold_then_argmax"
    assert thresholds["esi5_threshold"] == 0.60


def test_metadata_declares_lightgbm_booster_text() -> None:
    with Path("model_artifacts/model_metadata.json").open() as file:
        metadata = json.load(file)

    assert metadata["artifact_type"] == "lightgbm_booster_text"
    assert metadata["model_file"] == "esi_345_lightgbm_v2_threshold.txt"
    assert metadata["model_version"] == "esi_345_lightgbm_v2_threshold"


def test_model_bundle_falls_back_if_lightgbm_runtime_unavailable() -> None:
    bundle = load_model_bundle(settings)

    if bundle.loaded:
        assert bundle.error_message is None
    else:
        assert bundle.error_message
        assert "lightgbm" in bundle.error_message.lower()


def test_metadata_json_loads_model_version() -> None:
    with Path("model_artifacts/model_metadata.json").open() as file:
        metadata = json.load(file)

    assert metadata["model_version"] == "esi_345_lightgbm_v2_threshold"
    assert metadata["classes"] == ["ESI_3", "ESI_4", "ESI_5"]
    assert metadata["artifact_type"] == "lightgbm_booster_text"

import json
from pathlib import Path

from app.backend.core.config import settings
from app.backend.services.model_loader import load_model_bundle
from ml.inference.validate_artifacts import validate_artifacts

MODEL_REGISTRY_DIR = Path("model_registry/esi_345_lightgbm_v2")
FORBIDDEN_BACKUP_DIR = Path("model_registry/esi_345_lightgbm_v2_backup_before_final_verdict")


def test_model_registry_artifacts_are_valid_json() -> None:
    for filename in [
        "esi_345_lightgbm_v2_threshold_config.json",
        "esi_345_lightgbm_v2_feature_list.json",
        "esi_345_deployment_config.json",
        "esi_345_label_mapping.json",
    ]:
        with (MODEL_REGISTRY_DIR / filename).open() as file:
            json.load(file)


def test_runtime_uses_final_model_registry_not_backup_or_model_artifacts() -> None:
    configured_paths = [
        Path(settings.MODEL_REGISTRY_DIR),
        Path(settings.MODEL_DEPLOYMENT_CONFIG),
        Path(settings.MODEL_PATH),
        Path(settings.PREPROCESSOR_PATH),
        Path(settings.THRESHOLDS_PATH),
        Path(settings.FEATURE_SCHEMA_PATH),
        Path(settings.MODEL_METADATA_PATH),
        Path(settings.LABEL_MAPPING_PATH),
    ]

    for path in configured_paths:
        assert path.exists()
        assert MODEL_REGISTRY_DIR in [path, *path.parents]
        assert FORBIDDEN_BACKUP_DIR not in [path, *path.parents]
        assert Path("model_artifacts") not in [path, *path.parents]


def test_lightgbm_registry_bundle_loads_final_contract() -> None:
    bundle = load_model_bundle(settings)

    assert Path(settings.MODEL_PATH).name == "esi_345_lightgbm_v2_model.txt"
    assert Path(settings.PREPROCESSOR_PATH).name == (
        "esi_345_lightgbm_v2_preprocessing_artifacts.joblib"
    )
    assert bundle.model_version == "lightgbm_v2_weight_threshold_esi345"
    assert bundle.model_name == "LightGBM V2 Weight + Threshold"
    assert bundle.model_source == "final_registry"
    assert bundle.selected_calibration_method == "raw_lightgbm_probability"
    assert bundle.is_placeholder is False
    assert bundle.class_labels == ["ESI_3", "ESI_4", "ESI_5"]
    assert bundle.thresholds and bundle.thresholds["esi5_threshold"] == 0.60
    assert bundle.feature_schema and bundle.feature_schema["feature_count"] == 273
    assert bundle.feature_list and len(bundle.feature_list) == 273
    assert bundle.threshold_config is bundle.thresholds
    assert bundle.feature_schema["default_values"]["n_edvisits"] == 1.0
    assert bundle.feature_schema["default_values"]["cc_chestpain"] == 0
    assert bundle.error_message is None or "joblib" not in bundle.error_message.lower()
    assert bundle.error_message is None or "preprocessor" not in bundle.error_message.lower()


def test_validate_artifacts_accepts_lightgbm_text_contract() -> None:
    assert validate_artifacts() is True


def test_feature_schema_matches_v2_booster() -> None:
    with Path(settings.FEATURE_SCHEMA_PATH).open() as file:
        features = json.load(file)

    assert len(features) == 273
    assert "age" in features
    assert "triage_vital_hr" in features
    assert "triage_vital_sbp" in features
    assert "triage_vital_o2" in features
    assert "cc_chestpain" in features
    assert "cc_shortnessofbreath" in features


def test_thresholds_match_v2_staging_config() -> None:
    with Path(settings.THRESHOLDS_PATH).open() as file:
        thresholds = json.load(file)

    assert thresholds["model_version"] == "lightgbm_v2_weight_threshold_esi345"
    assert thresholds["deployment_threshold"] == 0.60
    assert thresholds["deploy_calibrated_probabilities"] is False


def test_metadata_declares_lightgbm_booster_text() -> None:
    with Path(settings.MODEL_METADATA_PATH).open() as file:
        metadata = json.load(file)

    assert metadata["model_file"] == "esi_345_lightgbm_v2_model.txt"
    assert metadata["model_version"] == "lightgbm_v2_weight_threshold_esi345"
    assert metadata["preprocessing_artifacts_file"] == (
        "esi_345_lightgbm_v2_preprocessing_artifacts.joblib"
    )


def test_model_bundle_falls_back_if_lightgbm_runtime_unavailable() -> None:
    bundle = load_model_bundle(settings)

    if bundle.loaded:
        assert bundle.error_message is None
    else:
        assert bundle.error_message
        assert "lightgbm" in bundle.error_message.lower()


def test_metadata_json_loads_model_version() -> None:
    with Path(settings.MODEL_METADATA_PATH).open() as file:
        metadata = json.load(file)
    with Path(settings.LABEL_MAPPING_PATH).open() as file:
        label_mapping = json.load(file)

    assert metadata["model_version"] == "lightgbm_v2_weight_threshold_esi345"
    assert label_mapping["class_names"] == ["ESI 3", "ESI 4", "ESI 5"]

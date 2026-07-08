"""Safe loading and caching for ESI LightGBM text artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.backend.core.config import settings

FORBIDDEN_MODEL_PATH_PARTS = {"esi_345_lightgbm_v2_backup_before_final_verdict"}


@dataclass
class ModelBundle:
    model: Any | None = None
    preprocessor: Any | None = None
    preprocessing_artifacts: Any | None = None
    thresholds: dict[str, Any] | None = None
    threshold_config: dict[str, Any] | None = None
    feature_schema: dict[str, Any] | None = None
    feature_list: list[str] | None = None
    metadata: dict[str, Any] | None = None
    label_mapping: dict[str, Any] | None = None
    loaded: bool = False
    is_placeholder: bool = True
    error_message: str | None = None
    model_version: str | None = None
    model_name: str | None = None
    model_source: str = "unavailable"
    selected_calibration_method: str | None = None
    class_labels: list[str] | None = None


_MODEL_BUNDLE_CACHE: ModelBundle | None = None


def load_json_file(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def _normalize_label(label: Any) -> str:
    label_text = str(label).strip().upper().replace(" ", "_")
    if label_text in {"3", "4", "5"}:
        return f"ESI_{label_text}"
    if label_text.startswith("ESI") and "_" not in label_text:
        digits = "".join(character for character in label_text if character.isdigit())
        if digits:
            return f"ESI_{digits}"
    return label_text


def _class_labels_from(
    metadata: dict[str, Any],
    model: Any | None,
    label_mapping: dict[str, Any] | None = None,
) -> list[str]:
    class_names = (label_mapping or {}).get("class_names")
    if isinstance(class_names, list) and class_names:
        return [_normalize_label(label) for label in class_names]

    reverse_label_map = (label_mapping or {}).get("reverse_label_map")
    if isinstance(reverse_label_map, dict) and reverse_label_map:
        return [
            _normalize_label(reverse_label_map[key])
            for key in sorted(reverse_label_map, key=lambda value: int(value))
        ]

    metadata_classes = metadata.get("classes")
    if isinstance(metadata_classes, list) and metadata_classes:
        return [_normalize_label(label) for label in metadata_classes]

    model_classes = getattr(model, "classes_", None) if model is not None else None
    if model_classes is not None:
        return [_normalize_label(label) for label in list(model_classes)]

    return ["ESI_3", "ESI_4", "ESI_5"]


def _contains_forbidden_path(path: Path) -> bool:
    return any(part in FORBIDDEN_MODEL_PATH_PARTS for part in path.parts)


def _registry_relative_path(
    registry_dir: Path,
    deployment_config: dict[str, Any],
    config_key: str,
    fallback_path: str | Path,
) -> Path:
    configured_name = deployment_config.get(config_key)
    if configured_name:
        candidate = Path(str(configured_name))
        if not candidate.is_absolute():
            return registry_dir / candidate
        return candidate
    return Path(fallback_path)


def _feature_schema_from_registry_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {
            "features": [str(feature) for feature in payload],
            "feature_count": len(payload),
            "source": "model_registry/esi_345_lightgbm_v2",
        }
    if isinstance(payload, dict):
        return payload
    raise ValueError("Feature list must be a JSON array or object.")


def _normalized_thresholds(threshold_config: dict[str, Any]) -> dict[str, Any]:
    deployment_threshold = threshold_config.get(
        "deployment_threshold",
        threshold_config.get("best_lgb_v2_threshold"),
    )
    normalized = dict(threshold_config)
    normalized.setdefault("strategy", "esi5_threshold_then_argmax")
    if deployment_threshold is not None:
        normalized.setdefault("esi5_threshold", float(deployment_threshold))
    normalized.setdefault("class_order", ["ESI_3", "ESI_4", "ESI_5"])
    return normalized


def _feature_schema_with_preprocessing_defaults(
    feature_schema: dict[str, Any],
    preprocessor: Any,
) -> dict[str, Any]:
    if not isinstance(preprocessor, dict):
        return feature_schema

    features = feature_schema.get("features")
    if not isinstance(features, list):
        return feature_schema

    numeric_medians = preprocessor.get("numeric_medians")
    if not isinstance(numeric_medians, dict):
        numeric_medians = {}

    default_values: dict[str, Any] = {}
    for feature in features:
        if feature in numeric_medians:
            default_values[feature] = numeric_medians[feature]
        elif feature.startswith(
            (
                "arrivalday_",
                "arrivalhour_bin_",
                "arrivalmode_",
                "arrivalmonth_",
                "cc_",
                "gender_",
                "triage_vital_o2_device_",
            )
        ):
            default_values[feature] = 0

    enriched_schema = dict(feature_schema)
    enriched_schema["default_values"] = default_values
    return enriched_schema


def _feature_list_from_schema(feature_schema: dict[str, Any]) -> list[str]:
    features = feature_schema.get("features")
    if not isinstance(features, list) or not all(isinstance(item, str) for item in features):
        raise ValueError("Feature list must resolve to a list of string feature names.")
    return features


def _validate_loaded_feature_contract(
    *,
    model: Any,
    feature_list: list[str],
    feature_schema: dict[str, Any],
) -> None:
    expected_count = feature_schema.get("feature_count")
    if expected_count is not None and int(expected_count) != len(feature_list):
        raise ValueError(
            f"Feature count mismatch: feature_count={expected_count}, "
            f"feature_list length={len(feature_list)}"
        )

    model_feature_count = None
    if hasattr(model, "num_feature"):
        model_feature_count = model.num_feature()
    if model_feature_count is not None and int(model_feature_count) != len(feature_list):
        raise ValueError(
            f"Feature count mismatch: model expects {model_feature_count}, "
            f"feature list has {len(feature_list)}"
        )


def load_model_bundle(app_settings: Any = settings) -> ModelBundle:
    registry_dir = Path(app_settings.MODEL_REGISTRY_DIR)
    deployment_config_path = Path(app_settings.MODEL_DEPLOYMENT_CONFIG)

    forbidden_paths = [
        path
        for path in [registry_dir, deployment_config_path]
        if _contains_forbidden_path(path)
    ]
    if forbidden_paths:
        return ModelBundle(
            loaded=False,
            error_message=(
                "Forbidden model registry path configured: "
                + ", ".join(str(path) for path in forbidden_paths)
            ),
        )

    if not deployment_config_path.exists():
        return ModelBundle(
            loaded=False,
            error_message=f"Missing model deployment config: {deployment_config_path}",
            model_source="unavailable",
        )

    try:
        metadata = load_json_file(deployment_config_path)
        required_paths = {
            "model": _registry_relative_path(
                registry_dir,
                metadata,
                "model_file",
                app_settings.MODEL_PATH,
            ),
            "preprocessor": _registry_relative_path(
                registry_dir,
                metadata,
                "preprocessing_artifacts_file",
                app_settings.PREPROCESSOR_PATH,
            ),
            "thresholds": _registry_relative_path(
                registry_dir,
                metadata,
                "threshold_config_file",
                app_settings.THRESHOLDS_PATH,
            ),
            "feature_schema": _registry_relative_path(
                registry_dir,
                metadata,
                "feature_list_file",
                app_settings.FEATURE_SCHEMA_PATH,
            ),
            "metadata": deployment_config_path,
            "label_mapping": _registry_relative_path(
                registry_dir,
                metadata,
                "label_mapping_file",
                app_settings.LABEL_MAPPING_PATH,
            ),
        }
    except Exception as exc:
        return ModelBundle(
            loaded=False,
            error_message=f"Unable to read model deployment config: {exc}",
            model_source="unavailable",
        )

    forbidden_paths = [path for path in required_paths.values() if _contains_forbidden_path(path)]
    if forbidden_paths:
        return ModelBundle(
            loaded=False,
            error_message=(
                "Forbidden model registry path configured: "
                + ", ".join(str(path) for path in forbidden_paths)
            ),
            metadata=metadata,
            model_version=metadata.get("model_version"),
            model_source="unavailable",
        )

    missing = [name for name, path in required_paths.items() if not path.exists()]
    if missing:
        missing_files = ", ".join(str(required_paths[name]) for name in missing)
        return ModelBundle(
            loaded=False,
            error_message=f"Missing required model artifact(s): {missing_files}",
            metadata=metadata,
            model_version=metadata.get("model_version"),
            model_name=metadata.get("model_display_name"),
            selected_calibration_method=metadata.get("selected_calibration_method"),
            model_source="unavailable",
        )

    try:
        thresholds = _normalized_thresholds(load_json_file(required_paths["thresholds"]))
        feature_schema = _feature_schema_from_registry_payload(
            json.loads(required_paths["feature_schema"].read_text(encoding="utf-8"))
        )
        label_mapping = load_json_file(required_paths["label_mapping"])
        class_labels = _class_labels_from(metadata, None, label_mapping)
        selected_calibration_method = (
            metadata.get("selected_calibration_method")
            or thresholds.get("selected_calibration_method")
        )
        model_version = metadata.get("model_version") or metadata.get("version")
        model_name = metadata.get("model_display_name")

        try:
            import joblib
        except ImportError:
            return ModelBundle(
                thresholds=thresholds,
                threshold_config=thresholds,
                feature_schema=feature_schema,
                feature_list=_feature_list_from_schema(feature_schema),
                metadata=metadata,
                label_mapping=label_mapping,
                loaded=False,
                error_message=(
                    "joblib package is not installed; preprocessing artifact is present "
                    "but runtime inference is unavailable."
                ),
                model_version=model_version,
                model_name=model_name,
                selected_calibration_method=selected_calibration_method,
                model_source="unavailable",
                class_labels=class_labels,
            )

        preprocessor = joblib.load(required_paths["preprocessor"])
        feature_schema = _feature_schema_with_preprocessing_defaults(
            feature_schema,
            preprocessor,
        )
        feature_list = _feature_list_from_schema(feature_schema)

        try:
            import lightgbm as lgb
        except ImportError:
            return ModelBundle(
                preprocessor=preprocessor,
                preprocessing_artifacts=preprocessor,
                thresholds=thresholds,
                threshold_config=thresholds,
                feature_schema=feature_schema,
                feature_list=feature_list,
                metadata=metadata,
                label_mapping=label_mapping,
                loaded=False,
                error_message=(
                    "LightGBM package is not installed; model text artifact is present "
                    "but runtime inference is unavailable."
                ),
                model_version=model_version,
                model_name=model_name,
                selected_calibration_method=selected_calibration_method,
                model_source="unavailable",
                class_labels=class_labels,
            )

        model = lgb.Booster(model_file=str(required_paths["model"]))
        _validate_loaded_feature_contract(
            model=model,
            feature_list=feature_list,
            feature_schema=feature_schema,
        )

        return ModelBundle(
            model=model,
            preprocessor=preprocessor,
            preprocessing_artifacts=preprocessor,
            thresholds=thresholds,
            threshold_config=thresholds,
            feature_schema=feature_schema,
            feature_list=feature_list,
            metadata=metadata,
            label_mapping=label_mapping,
            loaded=True,
            is_placeholder=False,
            error_message=None,
            model_version=model_version,
            model_name=model_name,
            model_source="final_registry",
            selected_calibration_method=selected_calibration_method,
            class_labels=class_labels,
        )
    except Exception as exc:
        return ModelBundle(
            loaded=False,
            error_message=f"Unable to load model artifacts: {exc}",
            metadata=metadata,
            model_version=metadata.get("model_version") if isinstance(metadata, dict) else None,
            model_name=metadata.get("model_display_name") if isinstance(metadata, dict) else None,
            selected_calibration_method=(
                metadata.get("selected_calibration_method")
                if isinstance(metadata, dict)
                else None
            ),
            model_source="unavailable",
        )


def get_model_bundle() -> ModelBundle:
    global _MODEL_BUNDLE_CACHE
    if _MODEL_BUNDLE_CACHE is None:
        _MODEL_BUNDLE_CACHE = load_model_bundle(settings)
    return _MODEL_BUNDLE_CACHE


def reload_model_bundle() -> ModelBundle:
    global _MODEL_BUNDLE_CACHE
    _MODEL_BUNDLE_CACHE = load_model_bundle(settings)
    return _MODEL_BUNDLE_CACHE

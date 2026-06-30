"""Safe loading and caching for ESI LightGBM text artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.backend.core.config import settings


@dataclass
class ModelBundle:
    model: Any | None = None
    preprocessor: Any | None = None
    thresholds: dict[str, Any] | None = None
    feature_schema: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    loaded: bool = False
    error_message: str | None = None
    model_version: str | None = None
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


def _class_labels_from(metadata: dict[str, Any], model: Any | None) -> list[str]:
    metadata_classes = metadata.get("classes")
    if isinstance(metadata_classes, list) and metadata_classes:
        return [_normalize_label(label) for label in metadata_classes]

    model_classes = getattr(model, "classes_", None) if model is not None else None
    if model_classes is not None:
        return [_normalize_label(label) for label in list(model_classes)]

    return ["ESI_3", "ESI_4", "ESI_5"]


def load_model_bundle(app_settings: Any = settings) -> ModelBundle:
    required_paths = {
        "model": Path(app_settings.MODEL_PATH),
        "thresholds": Path(app_settings.THRESHOLDS_PATH),
        "feature_schema": Path(app_settings.FEATURE_SCHEMA_PATH),
        "metadata": Path(app_settings.MODEL_METADATA_PATH),
    }

    missing = [name for name, path in required_paths.items() if not path.exists()]
    if missing:
        missing_files = ", ".join(str(required_paths[name]) for name in missing)
        return ModelBundle(
            loaded=False,
            error_message=f"Missing required model artifact(s): {missing_files}",
        )

    try:
        thresholds = load_json_file(required_paths["thresholds"])
        feature_schema = load_json_file(required_paths["feature_schema"])
        metadata = load_json_file(required_paths["metadata"])
        class_labels = _class_labels_from(metadata, None)
        model_version = metadata.get("model_version") or metadata.get("version")

        try:
            import lightgbm as lgb
        except ImportError:
            return ModelBundle(
                thresholds=thresholds,
                feature_schema=feature_schema,
                metadata=metadata,
                loaded=False,
                error_message=(
                    "LightGBM package is not installed; model text artifact is present "
                    "but runtime inference is unavailable."
                ),
                model_version=model_version,
                class_labels=class_labels,
            )

        model = lgb.Booster(model_file=str(required_paths["model"]))

        return ModelBundle(
            model=model,
            preprocessor=None,
            thresholds=thresholds,
            feature_schema=feature_schema,
            metadata=metadata,
            loaded=True,
            error_message=None,
            model_version=model_version,
            class_labels=class_labels,
        )
    except Exception as exc:
        return ModelBundle(
            loaded=False,
            error_message=f"Unable to load model artifacts: {exc}",
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

"""Smoke-check the final ESI 3/4/5 model registry package."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.backend.core.config import settings


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _registry_path(registry_dir: Path, deployment_config: dict[str, Any], key: str) -> Path:
    raw_value = deployment_config.get(key)
    if not raw_value:
        raise ValueError(f"Deployment config is missing {key}")
    candidate = Path(str(raw_value))
    if candidate.is_absolute():
        return candidate
    return registry_dir / candidate


def validate_model_registry() -> bool:
    registry_dir = Path(settings.MODEL_REGISTRY_DIR)
    deployment_config_path = Path(settings.MODEL_DEPLOYMENT_CONFIG)

    checks: list[tuple[str, Path]] = [
        ("registry_dir", registry_dir),
        ("deployment_config", deployment_config_path),
    ]

    if not deployment_config_path.exists():
        for label, path in checks:
            print(f"{'PASS' if path.exists() else 'FAIL'} {label}: {path}")
        return False

    deployment_config = _load_json(deployment_config_path)
    model_path = _registry_path(registry_dir, deployment_config, "model_file")
    preprocessing_path = _registry_path(
        registry_dir,
        deployment_config,
        "preprocessing_artifacts_file",
    )
    feature_list_path = _registry_path(registry_dir, deployment_config, "feature_list_file")
    threshold_config_path = _registry_path(
        registry_dir,
        deployment_config,
        "threshold_config_file",
    )
    label_mapping_path = _registry_path(registry_dir, deployment_config, "label_mapping_file")

    checks.extend(
        [
            ("model_file", model_path),
            ("preprocessing_artifacts", preprocessing_path),
            ("feature_list", feature_list_path),
            ("threshold_config", threshold_config_path),
            ("label_mapping", label_mapping_path),
        ]
    )

    all_present = True
    for label, path in checks:
        exists = path.exists()
        all_present = all_present and exists
        print(f"{'PASS' if exists else 'FAIL'} {label}: {path}")

    feature_list = _load_json(feature_list_path) if feature_list_path.exists() else []
    threshold_config = (
        _load_json(threshold_config_path)
        if threshold_config_path.exists()
        else {}
    )

    print(f"model_version: {deployment_config.get('model_version')}")
    print(f"model_name: {deployment_config.get('model_display_name')}")
    print(f"selected_calibration_method: {deployment_config.get('selected_calibration_method')}")
    print(f"deployment_threshold: {threshold_config.get('deployment_threshold')}")
    print(f"feature_count: {len(feature_list) if isinstance(feature_list, list) else 'unknown'}")

    return all_present


if __name__ == "__main__":
    raise SystemExit(0 if validate_model_registry() else 1)

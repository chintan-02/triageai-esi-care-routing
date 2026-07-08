"""Validate local ESI LightGBM V2 text artifacts without starting the API."""

from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.backend.core.config import settings
from app.backend.services.model_loader import load_json_file


MODEL_TXT_PATH = Path(settings.MODEL_PATH)
MODEL_REGISTRY_DIR = Path(settings.MODEL_REGISTRY_DIR)
VALIDATION_DIR = MODEL_REGISTRY_DIR / "reports"


def _check(condition: bool, label: str, detail: str) -> tuple[bool, str]:
    prefix = "PASS" if condition else "FAIL"
    return condition, f"{prefix} {label}: {detail}"


def _check_exists(label: str, path: Path) -> tuple[bool, str]:
    return _check(path.exists(), label, str(path) if path.exists() else f"missing {path}")


def _load_json(label: str, path: Path) -> tuple[bool, str, Any | None]:
    exists, message = _check_exists(label, path)
    if not exists:
        return exists, message, None
    try:
        payload = load_json_file(path)
        return True, f"PASS {label}: JSON load succeeded", payload
    except Exception as exc:
        return False, f"FAIL {label}: JSON load failed: {exc}", None


def _read_model_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_feature_names(model_text: str) -> list[str]:
    for line in model_text.splitlines():
        if line.startswith("feature_names="):
            return line.split("=", 1)[1].split()
    return []


def _parse_max_feature_idx(model_text: str) -> int | None:
    for line in model_text.splitlines():
        if line.startswith("max_feature_idx="):
            return int(line.split("=", 1)[1])
    return None


def validate_artifacts() -> bool:
    checks: list[tuple[bool, str]] = []

    model_exists, model_message = _check_exists("model_text", MODEL_TXT_PATH)
    checks.append((model_exists, model_message))

    model_text = _read_model_text(MODEL_TXT_PATH) if model_exists else ""
    feature_names = _parse_feature_names(model_text)
    max_feature_idx = _parse_max_feature_idx(model_text) if model_text else None

    if model_exists:
        checks.append(
            _check(
                "objective=multiclass" in model_text or "num_class=3" in model_text,
                "model_text",
                "contains multiclass objective or num_class=3",
            )
        )
        checks.append(
            _check(
                bool(feature_names),
                "model_text",
                f"parsed {len(feature_names)} feature names",
            )
        )

    thresholds_ok, thresholds_message, thresholds = _load_json(
        "threshold_config",
        Path(settings.THRESHOLDS_PATH),
    )
    feature_list_ok, feature_list_message, feature_list = _load_json(
        "feature_list",
        Path(settings.FEATURE_SCHEMA_PATH),
    )
    metadata_ok, metadata_message, metadata = _load_json(
        "deployment_config",
        Path(settings.MODEL_METADATA_PATH),
    )
    label_mapping_ok, label_mapping_message, label_mapping = _load_json(
        "label_mapping",
        Path(settings.LABEL_MAPPING_PATH),
    )
    checks.extend(
        [
            (thresholds_ok, thresholds_message),
            (feature_list_ok, feature_list_message),
            (metadata_ok, metadata_message),
            (label_mapping_ok, label_mapping_message),
            _check_exists("preprocessing_artifacts", Path(settings.PREPROCESSOR_PATH)),
        ]
    )

    required_validation_files = [
        VALIDATION_DIR / "lightgbm_v2_validation_summary.csv",
        VALIDATION_DIR / "lightgbm_v2_test_metrics.json",
        VALIDATION_DIR / "calibration_deployment_decision.csv",
        VALIDATION_DIR / "fairness_subgroup_evaluation.csv",
    ]
    for path in required_validation_files:
        checks.append(_check_exists(path.name, path))

    if feature_list_ok and isinstance(feature_list, list):
        schema_count = len(feature_list)
        checks.append(
            _check(
                schema_count == len(feature_names),
                "feature_list",
                f"feature_count {schema_count} matches parsed count {len(feature_names)}",
            )
        )
        if max_feature_idx is not None:
            checks.append(
                _check(
                    schema_count == max_feature_idx + 1,
                    "feature_list",
                    f"feature_count {schema_count} matches max_feature_idx {max_feature_idx}",
                )
            )
    elif feature_list_ok:
        checks.append(
            _check(False, "feature_list", "expected registry feature list JSON array")
        )

    if metadata_ok and metadata is not None:
        checks.append(
            _check(
                metadata.get("model_version") == "lightgbm_v2_weight_threshold_esi345",
                "deployment_config",
                "model_version is lightgbm_v2_weight_threshold_esi345",
            )
        )
        checks.append(
            _check(
                metadata.get("model_file") == MODEL_TXT_PATH.name,
                "deployment_config",
                f"model_file is {MODEL_TXT_PATH.name}",
            )
        )

    if thresholds_ok and thresholds is not None:
        checks.append(
            _check(
                thresholds.get("deployment_threshold") == 0.60,
                "threshold_config",
                "deployment_threshold is 0.60",
            )
        )
        checks.append(
            _check(
                thresholds.get("deploy_calibrated_probabilities") is False,
                "threshold_config",
                "raw LightGBM probabilities are deployed",
            )
        )

    if label_mapping_ok and label_mapping is not None:
        checks.append(
            _check(
                label_mapping.get("class_names") == ["ESI 3", "ESI 4", "ESI 5"],
                "label_mapping",
                "class_names are ESI 3, ESI 4, ESI 5",
            )
        )

    for _, message in checks:
        print(message)

    return all(ok for ok, _ in checks)


if __name__ == "__main__":
    raise SystemExit(0 if validate_artifacts() else 1)

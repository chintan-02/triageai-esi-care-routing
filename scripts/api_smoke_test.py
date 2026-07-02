"""Lightweight local API smoke checks for TriageAI / SympDirect."""

from __future__ import annotations

import argparse
import sys
from typing import Any

import requests


DEFAULT_BASE_URL = "http://127.0.0.1:8001"
TIMEOUT_SECONDS = 15


def sample_prediction_payload() -> dict[str, object]:
    return {
        "patient_age": 42,
        "sex": "female",
        "chief_complaint": "Chest discomfort",
        "symptom_duration": "45 minutes",
        "pain_score": 6,
        "temperature_c": 37.0,
        "heart_rate": 104,
        "respiratory_rate": 20,
        "systolic_bp": 132,
        "diastolic_bp": 82,
        "oxygen_saturation": 97.0,
        "consciousness_level": "alert",
        "pregnancy": False,
        "arrival_mode": "Walk-in",
        "additional_context": "Structured intake data for local smoke testing.",
    }


def _url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _get_json(base_url: str, path: str) -> tuple[int, dict[str, Any]]:
    response = requests.get(_url(base_url, path), timeout=TIMEOUT_SECONDS)
    return response.status_code, response.json()


def _post_json(
    base_url: str,
    path: str,
    payload: dict[str, object],
) -> tuple[int, dict[str, Any]]:
    response = requests.post(_url(base_url, path), json=payload, timeout=TIMEOUT_SECONDS)
    return response.status_code, response.json()


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_smoke_checks(base_url: str) -> None:
    health_status, health = _get_json(base_url, "/health")
    _check(health_status == 200, f"/health returned HTTP {health_status}")
    _check(health.get("status") == "ok", "/health status was not ok")
    print("PASS /health")

    ready_status, ready = _get_json(base_url, "/ready")
    _check(ready_status == 200, f"/ready returned HTTP {ready_status}")
    _check(ready.get("status") == "ready", "/ready status was not ready")
    _check(ready.get("database") == "connected", "/ready database was not connected")
    _check(ready.get("model_loaded") is True, "/ready model was not loaded")
    _check(ready.get("model_version"), "/ready did not include model_version")
    print("PASS /ready")

    predict_status, prediction = _post_json(
        base_url,
        "/predict",
        sample_prediction_payload(),
    )
    _check(predict_status == 200, f"/predict returned HTTP {predict_status}")
    _check(prediction.get("assessment_id"), "/predict did not return assessment_id")
    _check(prediction.get("acuity_scale") == "ESI", "/predict acuity_scale was not ESI")
    _check(
        prediction.get("predicted_esi") in {3, 4, 5},
        "/predict predicted_esi was not one of ESI 3, 4, or 5",
    )
    _check(
        prediction.get("final_esi") in {1, 2, 3, 4, 5},
        "/predict final_esi was not a valid ESI value",
    )
    _check(
        set(prediction.get("probabilities") or {}) == {"ESI_3", "ESI_4", "ESI_5"},
        "/predict probabilities did not include ESI_3, ESI_4, and ESI_5",
    )
    _check(
        "substitute for clinician judgment" in prediction.get("disclaimer", ""),
        "/predict disclaimer missing clinician judgment wording",
    )
    print("PASS /predict")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local API smoke checks.")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"FastAPI base URL. Defaults to {DEFAULT_BASE_URL}.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        run_smoke_checks(args.base_url)
    except (AssertionError, requests.RequestException, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print("All API smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

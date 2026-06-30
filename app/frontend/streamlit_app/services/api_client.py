"""HTTP client helpers for the FastAPI backend."""

from __future__ import annotations

import os
from typing import Any

import requests


BACKEND_URL = os.getenv("TRIAGEAI_BACKEND_URL", "http://127.0.0.1:8001")
REQUEST_TIMEOUT_SECONDS = 15
START_BACKEND_COMMAND = (
    "python -m uvicorn app.backend.api.main:app --reload --port 8001"
)


def _backend_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _response_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {"detail": response.text or "Backend returned a non-JSON response."}
    return payload if isinstance(payload, dict) else {"detail": payload}


def _request_error(message: str, error_type: str) -> dict[str, Any]:
    return {
        "ok": False,
        "backend_connected": False,
        "status_code": None,
        "data": None,
        "error_type": error_type,
        "message": message,
        "start_command": START_BACKEND_COMMAND,
    }


def get_ready_status(base_url: str = BACKEND_URL) -> dict[str, Any]:
    """Return normalized backend readiness status for Streamlit display."""
    try:
        response = requests.get(
            _backend_url(base_url, "/ready"),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.Timeout:
        return _request_error(
            f"Backend readiness check timed out after {REQUEST_TIMEOUT_SECONDS} seconds.",
            "timeout",
        )
    except requests.RequestException:
        return _request_error(
            f"Backend is not running on {base_url}",
            "connection",
        )

    payload = _response_json(response)
    if response.status_code >= 400:
        return {
            "ok": False,
            "backend_connected": True,
            "status_code": response.status_code,
            "data": payload,
            "error_type": "backend_error",
            "message": payload.get("detail", "Backend readiness check failed."),
            "start_command": START_BACKEND_COMMAND,
        }

    return {
        "ok": True,
        "backend_connected": True,
        "status_code": response.status_code,
        "data": payload,
        "error_type": None,
        "message": None,
        "start_command": START_BACKEND_COMMAND,
    }


def submit_prediction(
    payload: dict[str, Any],
    base_url: str = BACKEND_URL,
) -> dict[str, Any]:
    """Submit an intake payload to /predict and normalize errors."""
    try:
        response = requests.post(
            _backend_url(base_url, "/predict"),
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.Timeout:
        return _request_error(
            f"Prediction request timed out after {REQUEST_TIMEOUT_SECONDS} seconds.",
            "timeout",
        )
    except requests.RequestException:
        return _request_error(
            f"Backend is not running on {base_url}",
            "connection",
        )

    body = _response_json(response)
    if response.status_code == 422:
        return {
            "ok": False,
            "backend_connected": True,
            "status_code": response.status_code,
            "data": body,
            "error_type": "validation_error",
            "message": "Please review the highlighted intake fields and try again.",
            "start_command": START_BACKEND_COMMAND,
        }

    if response.status_code >= 400:
        return {
            "ok": False,
            "backend_connected": True,
            "status_code": response.status_code,
            "data": body,
            "error_type": "backend_error",
            "message": body.get("detail", "Prediction request failed."),
            "start_command": START_BACKEND_COMMAND,
        }

    warning = None
    if body.get("model_loaded") is False or body.get("is_placeholder") is True:
        warning = (
            "Model inference is currently unavailable; displaying fallback "
            "contract response."
        )

    return {
        "ok": True,
        "backend_connected": True,
        "status_code": response.status_code,
        "data": body,
        "error_type": None,
        "message": warning,
        "start_command": START_BACKEND_COMMAND,
    }

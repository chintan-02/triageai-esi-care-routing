"""Helpers for audit log payloads."""

from typing import Any


def build_audit_details(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": action,
        "payload": payload,
    }

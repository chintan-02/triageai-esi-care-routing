from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.backend.db.session import engine
from app.backend.services.model_loader import get_model_bundle

router = APIRouter(tags=["health"])


def _decision_threshold(bundle: Any) -> float | None:
    threshold_config = bundle.threshold_config or bundle.thresholds or {}
    for key in ("deployment_threshold", "esi5_threshold", "best_lgb_v2_threshold"):
        value = threshold_config.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _model_metrics(bundle: Any) -> dict[str, float] | None:
    metrics = bundle.metrics
    if not isinstance(metrics, dict):
        return None

    field_map = {
        "accuracy": "accuracy",
        "macro_f1": "macro_f1",
        "weighted_f1": "weighted_f1",
        "esi5_f1": "esi5_f1",
        "unsafe_esi3_to_esi5_downgrade_rate": "esi3_to_esi5_rate",
    }
    snapshot = {
        response_key: float(metrics[source_key])
        for response_key, source_key in field_map.items()
        if isinstance(metrics.get(source_key), (int, float))
    }
    return snapshot or None


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "TriageAI API"}


@router.get("/ready")
def readiness_check(response: Response) -> dict[str, Any]:
    bundle = get_model_bundle()
    database_connected = True
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database_connected = False

    is_ready = database_connected and bundle.loaded
    if not is_ready:
        response.status_code = 503

    return {
        "status": "ready" if is_ready else "not_ready",
        "database_connected": database_connected,
        "database": "connected" if database_connected else "not_connected",
        "model_loaded": bundle.loaded,
        "model_version": bundle.model_version,
        "model_name": bundle.model_name,
        "model_source": bundle.model_source,
        "selected_calibration_method": bundle.selected_calibration_method,
        "threshold_config_loaded": bundle.threshold_config is not None,
        "decision_threshold": _decision_threshold(bundle),
        "model_metrics": _model_metrics(bundle),
        "feature_count": (
            len(bundle.feature_list)
            if bundle.feature_list is not None
            else None
        ),
        "class_order": bundle.class_labels,
        "model_error": bundle.error_message,
        "is_placeholder": bundle.is_placeholder,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

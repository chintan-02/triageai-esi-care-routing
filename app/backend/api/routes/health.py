from datetime import datetime, timezone

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.backend.db.session import engine
from app.backend.services.model_loader import get_model_bundle

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "TriageAI API"}


@router.get("/ready")
def readiness_check(response: Response) -> dict[str, bool | str | None]:
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
        "model_error": bundle.error_message,
        "is_placeholder": not bundle.loaded,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

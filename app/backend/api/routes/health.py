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
    database_status = "connected"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database_status = "not_connected"

    is_ready = database_status == "connected" and bundle.loaded
    if not is_ready:
        response.status_code = 503

    return {
        "status": "ready" if is_ready else "not_ready",
        "model_loaded": bundle.loaded,
        "model_version": bundle.model_version,
        "model_error": bundle.error_message,
        "database": database_status,
    }

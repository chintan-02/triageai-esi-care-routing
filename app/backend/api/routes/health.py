from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "TriageAI API"}


@router.get("/ready")
def readiness_check() -> dict[str, bool | str]:
    return {
        "status": "ready",
        "model_loaded": False,
        "database": "not_connected",
    }

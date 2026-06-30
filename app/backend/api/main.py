from fastapi import FastAPI

from app.backend.api.routes.health import router as health_router
from app.backend.core.config import settings


app = FastAPI(
    title="TriageAI SympDirect API",
    version="0.1.0",
    debug=settings.DEBUG,
)

app.include_router(health_router)

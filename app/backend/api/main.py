from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.backend.api.routes.auth import router as auth_router
from app.backend.api.routes.nlp import router as nlp_router
from app.backend.api.routes.assessments import router as assessments_router
from app.backend.api.routes.clinician_review import router as clinician_review_router
from app.backend.api.routes.dashboard import router as dashboard_router
from app.backend.api.routes.health import router as health_router
from app.backend.api.routes.predict import router as predict_router
from app.backend.api.routes.reports import router as reports_router
from app.backend.api.routes.speech import router as speech_router
from app.backend.core.config import settings
from app.backend.db.base import init_db, assert_schema_current


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.AUTO_CREATE_TABLES:
        if settings.APP_ENV not in {"development", "test"}:
            raise RuntimeError("Automatic table creation is restricted to development/test")
        init_db()
    if settings.APP_ENV.lower() in {"production", "staging"}:
        assert_schema_current()
    yield


app = FastAPI(
    title="TriageAI SympDirect API",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)
app.include_router(nlp_router)
app.include_router(health_router)
app.include_router(speech_router)
app.include_router(predict_router)
app.include_router(assessments_router)
app.include_router(clinician_review_router)
app.include_router(dashboard_router)
app.include_router(reports_router)


@app.middleware("http")
async def private_response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.api.routes.nlp import router as nlp_router
from app.backend.api.routes.assessments import router as assessments_router
from app.backend.api.routes.clinician_review import router as clinician_review_router
from app.backend.api.routes.dashboard import router as dashboard_router
from app.backend.api.routes.health import router as health_router
from app.backend.api.routes.predict import router as predict_router
from app.backend.api.routes.reports import router as reports_router
from app.backend.api.routes.speech import router as speech_router
from app.backend.core.config import settings
from app.backend.db.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="TriageAI SympDirect API",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nlp_router)
app.include_router(health_router)
app.include_router(speech_router)
app.include_router(predict_router)
app.include_router(assessments_router)
app.include_router(clinician_review_router)
app.include_router(dashboard_router)
app.include_router(reports_router)

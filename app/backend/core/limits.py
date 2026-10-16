"""Shared fixed-window limits and atomic workspace reservations (PostgreSQL/SQLite)."""
import hashlib
import hmac
import time

from fastapi import Depends, HTTPException, Request
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.backend.core.config import settings
from app.backend.db.models import RateBucket, User
from app.backend.db.session import get_db


def consume(db: Session, scope: str, subject: str, limit: int, seconds: int = 60,
            *, now: int | None = None) -> None:
    """One atomic upsert, committed independently of the later business request.

    Fixed windows allow a boundary burst of up to twice the configured limit.
    No raw IP, account email or bearer credential is persisted in these keys.
    """
    now = int(time.time()) if now is None else now
    start = now // seconds * seconds
    key = hmac.new(settings.RATE_LIMIT_SECRET.encode(),
                   f"{scope}:{subject}:{start}".encode(), hashlib.sha256).hexdigest()
    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise RuntimeError("Unsupported shared limiter database")
    statement = insert(RateBucket).values(key=key, count=1, expires_at=start + seconds)
    statement = statement.on_conflict_do_update(
        index_elements=[RateBucket.key], set_={"count": RateBucket.count + 1},
        where=RateBucket.count < limit,
    ).returning(RateBucket.count)
    try:
        accepted = db.scalar(statement)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Request controls are temporarily unavailable") from None
    if accepted is None:
        raise HTTPException(429, "Request limit reached. Please retry later.",
                            headers={"Retry-After": str(start + seconds - now)})


def peer_identity(request: Request) -> str:
    # Only ASGI's resolved client address is trusted, never caller-supplied XFF.
    return request.client.host if request.client else "unknown-peer"


def public_auth_limit(request: Request, db: Session = Depends(get_db)) -> None:
    consume(db, "auth-global", "all", settings.AUTH_GLOBAL_PER_MINUTE)
    consume(db, "auth-peer", peer_identity(request), settings.AUTH_PER_MINUTE)
    if request.url.path.endswith(("/demo", "/register")):
        consume(db, "issuance-global", "all", settings.SESSION_ISSUANCE_GLOBAL_PER_HOUR, 3600)
        consume(db, "issuance-peer", peer_identity(request), settings.SESSION_ISSUANCE_PER_HOUR, 3600)


def authenticated_limits(request: Request, db: Session, user_id: str) -> None:
    consume(db, "api-global", "all", settings.API_GLOBAL_PER_MINUTE)
    consume(db, "api", user_id, settings.API_PER_MINUTE)
    path = request.url.path
    operation = None
    if request.method == "POST" and path in {"/predict", "/assessments"}:
        operation = ("inference-intake", settings.PREDICTIONS_PER_MINUTE)
    elif path == "/reports/generate" or path.endswith("/report/pdf"):
        operation = ("pdf", settings.REPORTS_PER_MINUTE)
    elif path.startswith("/reports/") and path.endswith("/download"):
        operation = ("pdf-download", settings.REPORT_DOWNLOADS_PER_MINUTE)
    elif path == "/nlp/extract-intake":
        operation = ("nlp", settings.NLP_PER_MINUTE)
    elif path == "/speech/transcribe":
        operation = ("speech", settings.SPEECH_PER_MINUTE)
    if operation:
        consume(db, "expensive-global", "all", settings.EXPENSIVE_GLOBAL_PER_HOUR, 3600)
        consume(db, operation[0], user_id, operation[1])


def reserve_workspace(db: Session, kind: str) -> None:
    """Charge work before resource creation; concurrent requests cannot overbook.

    Reservation and insert commit together in the repository transaction. Failed
    generation after a committed report creation still consumes a report slot.
    Trusted offline seed scripts have no request owner and are not public APIs.
    """
    owner = db.info.get("owner_id")
    if owner is None:
        return
    column, maximum = {
        "assessment": (User.assessment_count, settings.MAX_WORKSPACE_ASSESSMENTS),
        "report": (User.report_count, settings.MAX_WORKSPACE_REPORTS),
        "review": (User.review_count, settings.MAX_WORKSPACE_REVIEWS),
    }[kind]
    try:
        result = db.scalar(update(User).where(
            User.id == owner, User.cleanup_pending.is_(False), column < maximum,
        ).values({column: column + 1}).returning(User.id))
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Workspace controls are temporarily unavailable") from None
    if result is None:
        db.rollback()
        raise HTTPException(409, f"Workspace {kind} quota reached. Use existing records or wait for demo retention cleanup.")

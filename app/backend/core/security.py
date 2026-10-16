"""Opaque, revocable bearer sessions. Raw tokens and passwords are never stored."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.backend.core.config import settings
from app.backend.core.limits import authenticated_limits
from app.backend.db.models import AuthSession, User
from app.backend.db.session import get_db

bearer = HTTPBearer(auto_error=False)
PASSWORD_ITERATIONS = 600_000


def password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        # Keep unknown-user checks on the same expensive path as password checks.
        encoded = f"pbkdf2_sha256${PASSWORD_ITERATIONS}$invalid${'0' * 64}"
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user: User) -> tuple[str, datetime]:
    if db.scalar(update(User).where(User.id == user.id, User.cleanup_pending.is_(False))
                 .values(updated_at=datetime.now(timezone.utc)).returning(User.id)) is None:
        db.rollback()
        raise HTTPException(401, "Workspace is no longer available")
    token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.SESSION_TTL_MINUTES)
    db.add(AuthSession(token_hash=token_hash(token), user_id=user.id, expires_at=expiry))
    db.commit()
    return token, expiry


def get_authenticated_db(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Session:
    unauthorized = HTTPException(401, "Session missing or expired", headers={"WWW-Authenticate": "Bearer"})
    if not credentials or len(credentials.credentials) > 256:
        raise unauthorized
    session = db.get(AuthSession, token_hash(credentials.credentials))
    if not session:
        raise unauthorized
    expiry = session.expires_at
    if expiry.tzinfo is None:  # SQLite does not retain the timezone annotation.
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry <= datetime.now(timezone.utc):
        raise unauthorized
    user = db.get(User, session.user_id)
    if not user or user.cleanup_pending:
        raise unauthorized
    user_id = user.id
    authenticated_limits(request, db, user_id)
    if db.scalar(update(User).where(User.id == user_id, User.cleanup_pending.is_(False))
                 .values(updated_at=datetime.now(timezone.utc)).returning(User.id)) is None:
        db.rollback()
        raise unauthorized
    db.commit()
    db.info.update(owner_id=user_id, user=user, session=session)
    return db

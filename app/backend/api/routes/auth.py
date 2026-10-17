from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.backend.core.config import settings
from app.backend.core.limits import public_auth_limit, consume
from app.backend.core.security import create_session, get_authenticated_db, password_hash, verify_password
from app.backend.db.models import User
from app.backend.db.session import get_db
from app.backend.schemas.auth import AuthUserResponse, LoginRequest, RegisterRequest, SessionResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def user_response(user: User) -> AuthUserResponse:
    name = user.full_name or "Demo visitor"
    return AuthUserResponse(id=user.id, name=name, role=user.role,
                            initials="".join(part[0] for part in name.split()[:2]).upper(), email=user.email)


def session_response(db: Session, user: User, response: Response) -> SessionResponse:
    token, expires_at = create_session(db, user)
    response.headers["Cache-Control"] = "no-store"
    return SessionResponse(access_token=token, expires_at=expires_at, user=user_response(user))


def require_public_demo() -> None:
    if not settings.PUBLIC_DEMO_ENABLED:
        raise HTTPException(403, "Public demo access is disabled")


@router.post("/demo", response_model=SessionResponse, dependencies=[Depends(public_auth_limit), Depends(require_public_demo)])
def demo(response: Response, db: Session = Depends(get_db)) -> SessionResponse:
    user = User(full_name="Demo visitor", role="Doctor", is_demo=True)
    db.add(user)
    db.flush()
    return session_response(db, user, response)


@router.post("/register", response_model=SessionResponse, dependencies=[Depends(public_auth_limit), Depends(require_public_demo)])
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> SessionResponse:
    # This is an educational demo account, not a verified clinician or administrator.
    user = User(email=payload.email, full_name=payload.name, role="Doctor", is_demo=True,
                password_hash=password_hash(payload.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account cannot be created") from None
    return session_response(db, user, response)


@router.post("/login", response_model=SessionResponse, dependencies=[Depends(public_auth_limit)])
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> SessionResponse:
    identifier = payload.identifier.strip().lower()
    consume(db, "login-account", identifier, settings.LOGIN_ACCOUNT_PER_HOUR, 3600)
    user = db.scalar(select(User).where(User.email == identifier))
    if not verify_password(payload.password, user.password_hash if user else None):
        raise HTTPException(401, "Invalid credentials")
    return session_response(db, user, response)


@router.get("/me", response_model=AuthUserResponse)
def me(response: Response, db: Session = Depends(get_authenticated_db)) -> AuthUserResponse:
    response.headers["Cache-Control"] = "no-store"
    return user_response(db.info["user"])


@router.post("/logout", status_code=204)
def logout(db: Session = Depends(get_authenticated_db)) -> None:
    db.delete(db.info["session"])
    db.commit()

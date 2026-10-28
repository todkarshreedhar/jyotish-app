"""Sessions, CSRF protection and the current-user dependency (US-07, US-08)."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from jyotish_api.crypto import new_token, token_hash
from jyotish_api.db import get_db
from jyotish_api.models import Consent, SessionRow, User
from jyotish_api.settings import settings

COOKIE = "jy_session"
CONSENT_PURPOSE = "chart_calculation"
CONSENT_VERSION = "2026-10"
UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}

DB = Annotated[Session, Depends(get_db)]


def now() -> datetime:
    return datetime.now(UTC)


def issue_token(db: Session, user: User) -> str:
    """Create a session and return its token. The web app keeps it in a
    cookie; the mobile app keeps it in the phone's secure storage and sends
    it as `Authorization: Bearer <token>`."""
    token = new_token()
    db.add(SessionRow(token_hash=token_hash(token), user_id=user.id, expires_at=now() + timedelta(days=settings.session_days)))
    user.last_login_at = now()
    db.commit()
    return token


def create_session(db: Session, user: User, response: Response) -> None:
    token = issue_token(db, user)
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def bearer_token(request: Request) -> str | None:
    h = request.headers.get("authorization", "")
    if h[:7].lower() == "bearer ":
        return h[7:].strip() or None
    return None


def session_token(request: Request) -> str | None:
    return bearer_token(request) or request.cookies.get(COOKIE)


def end_session(db: Session, request: Request, response: Response) -> None:
    token = session_token(request)
    if token:
        db.execute(delete(SessionRow).where(SessionRow.token_hash == token_hash(token)))
        db.commit()
    response.delete_cookie(COOKIE, path="/")


def csrf_ok(request: Request) -> bool:
    """State-changing requests must carry the X-CSRF header. Browsers cannot
    add custom headers to cross-site requests without a CORS preflight, which
    our CORS policy refuses for other origins."""
    if request.method not in UNSAFE:
        return True
    # A bearer token is never sent by the browser on its own, so a request
    # that carries one (and no cookie) cannot be a cross-site forgery.
    if bearer_token(request) and COOKIE not in request.cookies:
        return True
    return request.headers.get("x-csrf") == "1"


def optional_user(request: Request, db: DB) -> User | None:
    token = session_token(request)
    if not token:
        return None
    row = db.scalar(select(SessionRow).where(SessionRow.token_hash == token_hash(token)))
    if row is None or row.expires_at < now():
        return None
    return db.get(User, row.user_id)


def current_user(request: Request, user: Annotated[User | None, Depends(optional_user)]) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not signed in")
    if not csrf_ok(request):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "missing CSRF header")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def has_consent(db: Session, user: User) -> bool:
    return (
        db.scalar(
            select(Consent.id).where(
                Consent.user_id == user.id, Consent.purpose == CONSENT_PURPOSE, Consent.version == CONSENT_VERSION
            )
        )
        is not None
    )


def consented_user(user: CurrentUser, db: DB) -> User:
    if not has_consent(db, user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "consent_required")
    return user


ConsentedUser = Annotated[User, Depends(consented_user)]


def admin_user(user: CurrentUser) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin only")
    return user


AdminUser = Annotated[User, Depends(admin_user)]

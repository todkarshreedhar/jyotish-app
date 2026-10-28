"""Sign-in with Google (OpenID Connect) or an emailed one-time link (US-07)."""

from datetime import timedelta
from typing import Annotated
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update

from jyotish_api import cache, emailer
from jyotish_api.crypto import new_token, token_hash
from jyotish_api.models import AuditLog, LoginToken, User
from jyotish_api.security import DB, create_session, csrf_ok, end_session, has_consent, now
from jyotish_api.settings import settings

router = APIRouter(prefix="/v1/auth", tags=["auth"])

GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
STATE_COOKIE = "jy_oauth"

LINK_TEXT = {
    "en": ("Your sign-in link", "Open this link to sign in to Jyotish. It works once and expires in {m} minutes.\n\n{url}\n\nIf you did not ask for this, ignore this email."),
    "hi": ("आपका साइन-इन लिंक", "ज्योतिष में साइन इन करने के लिए यह लिंक खोलें। यह एक बार काम करता है और {m} मिनट में समाप्त हो जाता है।\n\n{url}\n\nयदि आपने इसका अनुरोध नहीं किया, तो इस ईमेल को अनदेखा करें।"),
    "mr": ("तुमची साइन-इन लिंक", "ज्योतिषमध्ये साइन इन करण्यासाठी ही लिंक उघडा. ती एकदाच चालते आणि {m} मिनिटांत संपते.\n\n{url}\n\nतुम्ही ही विनंती केली नसल्यास, हा ईमेल दुर्लक्षित करा."),
}


def _require_csrf(request: Request) -> None:
    if not csrf_ok(request):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "missing CSRF header")


def _safe_next(nxt: str | None) -> str:
    # Only same-site relative paths, to avoid open redirects.
    if nxt and nxt.startswith("/") and not nxt.startswith("//"):
        return nxt
    return "/dashboard"


def _user_for_email(db: DB, email: str, locale: str = "en") -> User:
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, locale=locale if locale in LINK_TEXT else "en", default_settings={})
        db.add(user)
        db.flush()
        db.add(AuditLog(actor_id=user.id, action="user.created", target_user_id=user.id, meta={"method": "email"}))
    return user


class EmailStart(BaseModel):
    email: EmailStr
    next: str | None = None
    locale: str = "en"


@router.post("/email/start", status_code=202, dependencies=[Depends(_require_csrf)])
def email_start(body: EmailStart, request: Request, db: DB) -> dict[str, str]:
    email = body.email.strip().lower()
    ip = request.client.host if request.client else "?"
    if cache.incr_window(f"jy:rl:login:{email}", 3600) > 5 or cache.incr_window(f"jy:rl:loginip:{ip}", 3600) > 30:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too many sign-in requests; try again later")
    token = new_token()
    db.add(LoginToken(email=email, token_hash=token_hash(token), expires_at=now() + timedelta(minutes=settings.login_link_minutes)))
    db.commit()
    url = f"{settings.web_url}/auth/verify?" + urlencode({"token": token, "next": _safe_next(body.next)})
    subject, text = LINK_TEXT.get(body.locale, LINK_TEXT["en"])
    emailer.send(email, subject, text.format(url=url, m=settings.login_link_minutes))
    return {"status": "sent"}


class EmailVerify(BaseModel):
    token: str


@router.post("/email/verify", dependencies=[Depends(_require_csrf)])
def email_verify(body: EmailVerify, response: Response, db: DB) -> dict[str, object]:
    h = token_hash(body.token)
    row = db.scalar(select(LoginToken).where(LoginToken.token_hash == h))
    if row is None or row.used_at is not None or row.expires_at < now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "this sign-in link is invalid or has expired")
    # Mark used atomically so the link works only once.
    res = db.execute(update(LoginToken).where(LoginToken.id == row.id, LoginToken.used_at.is_(None)).values(used_at=now()))
    if res.rowcount != 1:  # type: ignore[attr-defined]
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "this sign-in link was already used")
    user = _user_for_email(db, row.email)
    db.add(AuditLog(actor_id=user.id, action="auth.login", target_user_id=user.id, meta={"method": "email"}))
    create_session(db, user, response)
    return {"ok": True, "needs_consent": not has_consent(db, user)}


@router.get("/google/login")
def google_login(next: Annotated[str | None, Query()] = None) -> RedirectResponse:
    if not settings.google_client_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Google sign-in is not configured")
    state, nonce = new_token(16), new_token(16)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.web_url}/api/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "prompt": "select_account",
    }
    resp = RedirectResponse(GOOGLE_AUTH + "?" + urlencode(params), status_code=302)
    resp.set_cookie(STATE_COOKIE, f"{state}.{nonce}.{_safe_next(next)}", max_age=600, httponly=True,
                    secure=settings.cookie_secure, samesite="lax", path="/")
    return resp


_jwks: jwt.PyJWKClient | None = None


def _verify_google_id_token(id_token: str, nonce: str) -> dict[str, object]:
    global _jwks
    if _jwks is None:
        _jwks = jwt.PyJWKClient(GOOGLE_JWKS)
    key = _jwks.get_signing_key_from_jwt(id_token)
    claims = jwt.decode(id_token, key.key, algorithms=["RS256"], audience=settings.google_client_id)
    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise ValueError("bad issuer")
    if claims.get("nonce") != nonce:
        raise ValueError("bad nonce")
    if not claims.get("email_verified"):
        raise ValueError("email not verified")
    return claims


@router.get("/google/callback")
def google_callback(request: Request, db: DB, code: str = "", state: str = "") -> RedirectResponse:
    cookie = request.cookies.get(STATE_COOKIE, "")
    parts = cookie.split(".", 2)
    fail = RedirectResponse(f"{settings.web_url}/login?error=google", status_code=302)
    if len(parts) != 3 or not code or parts[0] != state:
        return fail
    _, nonce, nxt = parts
    try:
        r = httpx.post(GOOGLE_TOKEN, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": f"{settings.web_url}/api/v1/auth/google/callback",
            "grant_type": "authorization_code",
        }, timeout=10)
        r.raise_for_status()
        claims = _verify_google_id_token(r.json()["id_token"], nonce)
    except Exception:
        return fail
    sub, email = str(claims["sub"]), str(claims["email"]).lower()
    user = db.scalar(select(User).where(User.google_sub == sub)) or _user_for_email(db, email)
    user.google_sub = sub
    if not user.display_name and claims.get("name"):
        user.display_name = str(claims["name"])[:200]
    db.add(AuditLog(actor_id=user.id, action="auth.login", target_user_id=user.id, meta={"method": "google"}))
    target = "/welcome" if not has_consent(db, user) else nxt
    resp = RedirectResponse(f"{settings.web_url}{target}", status_code=302)
    create_session(db, user, resp)
    resp.delete_cookie(STATE_COOKIE, path="/")
    return resp


@router.post("/logout", dependencies=[Depends(_require_csrf)])
def logout(request: Request, response: Response, db: DB) -> dict[str, bool]:
    end_session(db, request, response)
    return {"ok": True}

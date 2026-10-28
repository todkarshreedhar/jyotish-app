"""The signed-in user's account: settings, consent, export and deletion
(US-09, US-10, US-11)."""

import json
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import delete, select, update

from jyotish_api.crypto import decrypt_json
from jyotish_api.models import AlertPrefs, ApiKey, AuditLog, Consent, LoginToken, Profile, Report, SessionRow, User
from jyotish_api.schemas import SettingsIn
from jyotish_api.security import CONSENT_PURPOSE, CONSENT_VERSION, DB, CurrentUser, end_session, has_consent
from jyotish_api.settings import settings

router = APIRouter(prefix="/v1", tags=["account"])


def user_out(db: DB, u: User) -> dict[str, Any]:
    return {
        "id": str(u.id),
        "email": u.email,
        "display_name": u.display_name,
        "role": u.role,
        "locale": u.locale,
        "default_settings": SettingsIn(**(u.default_settings or {})).model_dump(mode="json"),
        "consent": {"given": has_consent(db, u), "version": CONSENT_VERSION},
        "brand_name": u.brand_name,
        "has_brand_logo": u.brand_logo is not None,
        "max_profiles": settings.max_profiles_astrologer if u.role in ("astrologer", "admin") else settings.max_profiles_user,
    }


@router.get("/config")
def config() -> dict[str, Any]:
    return {
        "google_enabled": bool(settings.google_client_id),
        "consent_version": CONSENT_VERSION,
        "languages": ["en", "hi", "mr"],
        "environment": settings.environment,
        "version": settings.app_version,
    }


@router.get("/me")
def me(user: CurrentUser, db: DB) -> dict[str, Any]:
    return user_out(db, user)


class MeUpdate(BaseModel):
    display_name: str | None = None
    locale: Literal["en", "hi", "mr"] | None = None
    default_settings: SettingsIn | None = None
    brand_name: str | None = None


@router.patch("/me")
def update_me(body: MeUpdate, user: CurrentUser, db: DB) -> dict[str, Any]:
    if body.display_name is not None:
        user.display_name = body.display_name[:200] or None
    if body.locale is not None:
        user.locale = body.locale
    if body.default_settings is not None:
        user.default_settings = body.default_settings.model_dump(mode="json")
    if body.brand_name is not None:
        if user.role not in ("astrologer", "admin"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "branding is for astrologer accounts")
        user.brand_name = body.brand_name[:200] or None
    db.commit()
    return user_out(db, user)


class ConsentIn(BaseModel):
    accept: bool
    version: str = CONSENT_VERSION


@router.post("/me/consent")
def give_consent(body: ConsentIn, user: CurrentUser, db: DB) -> dict[str, Any]:
    if not body.accept:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "consent is required to use the app")
    if body.version != CONSENT_VERSION:
        raise HTTPException(status.HTTP_409_CONFLICT, "consent text has changed; please reload")
    if not has_consent(db, user):
        db.add(Consent(user_id=user.id, purpose=CONSENT_PURPOSE, version=CONSENT_VERSION))
        db.add(
            AuditLog(
                actor_id=user.id,
                action="consent.given",
                target_user_id=user.id,
                meta={"purpose": CONSENT_PURPOSE, "version": CONSENT_VERSION},
            )
        )
        db.commit()
    return user_out(db, user)


@router.get("/me/export")
def export(user: CurrentUser, db: DB) -> Response:

    profiles = []
    for p in db.scalars(select(Profile).where(Profile.user_id == user.id)):
        profiles.append(
            {
                "id": str(p.id),
                **decrypt_json(p.birth_enc),
                "folder": p.folder,
                "settings": p.settings,
                "is_main": p.is_main,
                "created_at": p.created_at.isoformat(),
            }
        )
    consents = [
        {"purpose": c.purpose, "version": c.version, "accepted_at": c.accepted_at.isoformat()}
        for c in db.scalars(select(Consent).where(Consent.user_id == user.id))
    ]
    data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "account": {k: v for k, v in user_out(db, user).items() if k != "has_brand_logo"},
        "profiles": profiles,
        "consents": consents,
        "reports": [
            {"id": str(r.id), "kind": r.kind, "status": r.status, "created_at": r.created_at.isoformat()}
            for r in db.scalars(select(Report).where(Report.user_id == user.id))
        ],
    }
    db.add(AuditLog(actor_id=user.id, action="account.export", target_user_id=user.id))
    db.commit()
    body = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(
        body, media_type="application/json", headers={"Content-Disposition": 'attachment; filename="jyotish-my-data.json"'}
    )


class DeleteIn(BaseModel):
    confirm_email: str


@router.delete("/me")
def delete_me(body: DeleteIn, user: CurrentUser, request: Request, response: Response, db: DB) -> dict[str, bool]:
    if body.confirm_email.strip().lower() != user.email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "type your email address to confirm")
    uid = user.id
    end_session(db, request, response)
    # Child rows go first; most also cascade, this keeps it explicit.
    for model in (Report, Profile, SessionRow, Consent, AlertPrefs, ApiKey):
        db.execute(delete(model).where(model.user_id == uid))
    db.execute(delete(LoginToken).where(LoginToken.email == user.email))
    # Audit rows are kept for accountability but no longer point at an identity.
    db.add(AuditLog(actor_id=None, action="account.deleted", target_user_id=None, meta={}))
    db.execute(update(AuditLog).where(AuditLog.actor_id == uid).values(actor_id=None))
    db.execute(update(AuditLog).where(AuditLog.target_user_id == uid).values(target_user_id=None))
    db.delete(user)
    db.commit()
    return {"ok": True}


@router.post("/me/logo")
async def upload_logo(file: UploadFile, user: CurrentUser, db: DB) -> dict[str, Any]:
    """Logo for client PDFs (US-74). PNG or JPEG, up to 300 KB."""
    if user.role not in ("astrologer", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "branding is for astrologer accounts")
    data = await file.read(300_001)
    if len(data) > 300_000:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "logo must be 300 KB or smaller")
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        kind = "image/png"
    elif data[:3] == b"\xff\xd8\xff":
        kind = "image/jpeg"
    else:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "logo must be PNG or JPEG")
    user.brand_logo, user.brand_logo_type = data, kind
    db.commit()
    return user_out(db, user)

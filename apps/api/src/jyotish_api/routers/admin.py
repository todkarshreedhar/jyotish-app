"""Support tools with an audit trail (US-12)."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from jyotish_api.models import AuditLog, Profile, User
from jyotish_api.routers.profiles import profile_out
from jyotish_api.security import DB, AdminUser

router = APIRouter(prefix="/v1/admin", tags=["admin"])


def _user(db: DB, user_id: str) -> User:
    try:
        u = db.get(User, uuid.UUID(user_id))
    except ValueError:
        u = None
    if u is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not found")
    return u


@router.get("/users")
def find_users(admin: AdminUser, db: DB, email: str = Query(min_length=3)) -> dict[str, Any]:
    rows = db.scalars(select(User).where(User.email.ilike(f"%{email.strip()}%")).limit(20))
    db.add(AuditLog(actor_id=admin.id, action="admin.search_users", meta={"query": email}))
    db.commit()
    return {"items": [{"id": str(u.id), "email": u.email, "role": u.role, "created_at": u.created_at.isoformat()} for u in rows]}


@router.get("/users/{user_id}")
def open_user(user_id: str, admin: AdminUser, db: DB) -> dict[str, Any]:
    u = _user(db, user_id)
    n = db.scalar(select(func.count()).select_from(Profile).where(Profile.user_id == u.id))
    db.add(AuditLog(actor_id=admin.id, action="admin.open_user", target_user_id=u.id))
    db.commit()
    # No birth details here: those need a reason (see below).
    return {
        "id": str(u.id),
        "email": u.email,
        "role": u.role,
        "locale": u.locale,
        "profiles": n,
        "created_at": u.created_at.isoformat(),
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
    }


class Reason(BaseModel):
    reason: str = Field(min_length=10, max_length=500)


@router.post("/users/{user_id}/birth-details")
def view_birth_details(user_id: str, body: Reason, admin: AdminUser, db: DB) -> dict[str, Any]:
    u = _user(db, user_id)
    db.add(AuditLog(actor_id=admin.id, action="admin.view_birth_details", target_user_id=u.id, reason=body.reason))
    db.commit()
    return {"items": [profile_out(p) for p in db.scalars(select(Profile).where(Profile.user_id == u.id))]}


class RoleIn(BaseModel):
    role: str = Field(pattern="^(user|astrologer|admin)$")
    reason: str = Field(min_length=10, max_length=500)


@router.post("/users/{user_id}/role")
def set_role(user_id: str, body: RoleIn, admin: AdminUser, db: DB) -> dict[str, Any]:
    u = _user(db, user_id)
    old = u.role
    u.role = body.role
    db.add(
        AuditLog(
            actor_id=admin.id,
            action="admin.set_role",
            target_user_id=u.id,
            reason=body.reason,
            meta={"from": old, "to": body.role},
        )
    )
    db.commit()
    return {"id": str(u.id), "role": u.role}


@router.get("/audit")
def audit(admin: AdminUser, db: DB, user_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    q = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500))
    if user_id:
        q = q.where((AuditLog.target_user_id == uuid.UUID(user_id)) | (AuditLog.actor_id == uuid.UUID(user_id)))
    return {
        "items": [
            {
                "who": str(a.actor_id) if a.actor_id else None,
                "what": a.action,
                "target": str(a.target_user_id) if a.target_user_id else None,
                "reason": a.reason,
                "meta": a.meta,
                "when": a.created_at.isoformat(),
            }
            for a in db.scalars(q)
        ]
    }

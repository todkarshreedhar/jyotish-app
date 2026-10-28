"""Partner API: self-service keys, limits, usage and the public endpoints
(US-77 to US-80). Public routes live under /public/v1 and use X-API-Key."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from jyotish_engine.matching import ashtakoota
from jyotish_engine.panchang import panchang
from jyotish_engine.settings import ChartSettings
from jyotish_engine.timeutil import InputError
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from jyotish_api import cache
from jyotish_api.crypto import new_token, token_hash
from jyotish_api.models import ApiKey, ApiUsage, AuditLog
from jyotish_api.schemas import BirthIn, ChartRequest
from jyotish_api.security import DB, AdminUser, ConsentedUser
from jyotish_api.services import charts

router = APIRouter(prefix="/v1/developer", tags=["developer"])
public = APIRouter(prefix="/public/v1", tags=["public API"])


class KeyIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def _key_out(k: ApiKey, usage_today: int = 0) -> dict[str, Any]:
    return {
        "id": str(k.id),
        "name": k.name,
        "prefix": k.prefix,
        "daily_limit": k.daily_limit,
        "per_minute_limit": k.per_minute_limit,
        "created_at": k.created_at.isoformat() if k.created_at else None,
        "revoked_at": k.revoked_at.isoformat() if k.revoked_at else None,
        "used_today": usage_today,
    }


def _usage_today(db: DB, key_id: Any) -> int:
    u = db.get(ApiUsage, {"key_id": key_id, "day": datetime.now(UTC).date()})
    return u.count if u else 0


@router.get("/keys")
def list_keys(user: ConsentedUser, db: DB) -> dict[str, Any]:
    keys = db.scalars(select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc()))
    return {"items": [_key_out(k, _usage_today(db, k.id)) for k in keys]}


@router.post("/keys", status_code=201)
def create_key(body: KeyIn, user: ConsentedUser, db: DB) -> dict[str, Any]:
    active = db.scalars(select(ApiKey).where(ApiKey.user_id == user.id, ApiKey.revoked_at.is_(None))).all()
    if len(active) >= 5:
        raise HTTPException(status.HTTP_409_CONFLICT, "at most 5 active keys")
    secret = "jy_" + new_token(24)
    k = ApiKey(user_id=user.id, name=body.name, prefix=secret[:10], key_hash=token_hash(secret))
    db.add(k)
    db.add(AuditLog(actor_id=user.id, action="apikey.created", target_user_id=user.id, meta={"prefix": k.prefix}))
    db.commit()
    db.refresh(k)
    # The full key is shown once only.
    return {**_key_out(k), "key": secret}


@router.delete("/keys/{key_id}")
def revoke_key(key_id: str, user: ConsentedUser, db: DB) -> dict[str, Any]:
    k = db.scalar(select(ApiKey).where(ApiKey.user_id == user.id, ApiKey.id == _uuid(key_id)))
    if k is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "key not found")
    k.revoked_at = datetime.now(UTC)
    db.add(AuditLog(actor_id=user.id, action="apikey.revoked", target_user_id=user.id, meta={"prefix": k.prefix}))
    db.commit()
    return _key_out(k)


def _uuid(s: str) -> Any:
    import uuid

    try:
        return uuid.UUID(s)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "key not found") from None


@router.get("/usage")
def admin_usage(admin: AdminUser, db: DB) -> dict[str, Any]:
    rows = db.execute(
        select(ApiKey.prefix, ApiKey.name, ApiUsage.day, ApiUsage.count)
        .join(ApiUsage, ApiUsage.key_id == ApiKey.id)
        .order_by(ApiUsage.day.desc())
        .limit(500)
    )
    return {"items": [{"prefix": p, "name": n, "day": d.isoformat(), "count": c} for p, n, d, c in rows]}


def api_key(db: DB, request: Request, x_api_key: Annotated[str | None, Header()] = None) -> ApiKey:
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "X-API-Key header is required")
    k = db.scalar(select(ApiKey).where(ApiKey.key_hash == token_hash(x_api_key)))
    if k is None or k.revoked_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid API key")
    minute = cache.incr_window(f"jy:rl:key:{k.id}:m", 60)
    today = datetime.now(UTC).date()
    stmt = (
        insert(ApiUsage)
        .values(key_id=k.id, day=today, count=1)
        .on_conflict_do_update(index_elements=["key_id", "day"], set_={"count": ApiUsage.count + 1})
        .returning(ApiUsage.count)
    )
    day_count = int(db.execute(stmt).scalar_one())
    db.commit()
    # Added to the response by the middleware in main.py
    request.state.extra_headers = {
        "X-RateLimit-Limit-Day": str(k.daily_limit),
        "X-RateLimit-Remaining-Day": str(max(0, k.daily_limit - day_count)),
    }
    if minute > k.per_minute_limit or day_count > k.daily_limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "rate limit exceeded", headers={"Retry-After": "60"})
    return k


Key = Annotated[ApiKey, Depends(api_key)]


@public.post("/chart")
def public_chart(body: ChartRequest, key: Key) -> Response:
    """Full chart for birth details. Nothing is stored."""
    try:
        birth = charts.birth_from(body.birth.model_dump(mode="json"))
        cs = ChartSettings.from_dict(body.settings.model_dump(mode="json"))
        return Response(charts.chart(birth, cs, tuple(body.vargas), body.bhava_chalit), media_type="application/json")
    except (InputError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@public.get("/panchang")
def public_panchang(key: Key, on: str, lat: float, lon: float, tz: str | None = None) -> dict[str, Any]:
    from datetime import date

    tz_name = tz or charts.timezone_at(lat, lon)
    try:
        return panchang(date.fromisoformat(on), tz_name or "UTC", lat, lon)
    except (InputError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


class PublicMatchIn(BaseModel):
    boy: BirthIn
    girl: BirthIn


@public.post("/match")
def public_match(body: PublicMatchIn, key: Key) -> dict[str, Any]:
    moons = []
    for b in (body.boy, body.girl):
        c = charts.chart_dict(charts.birth_from(b.model_dump(mode="json")), ChartSettings(), ("D1",))
        moons.append(next(p["longitude"] for p in c["planets"] if p["id"] == "moon"))
    return ashtakoota(moons[0], moons[1])

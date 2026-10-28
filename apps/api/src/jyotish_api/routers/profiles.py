"""Birth profiles (US-13 to US-18, US-32) and everything computed from them."""

import uuid
from dataclasses import asdict
from datetime import UTC, date, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from jyotish_engine.names import names
from jyotish_engine.settings import ChartSettings
from jyotish_engine.timeutil import InputError
from sqlalchemy import func, select

from jyotish_api.crypto import decrypt_json, encrypt_json
from jyotish_api.models import Profile
from jyotish_api.schemas import VARGA_CODES, Lang, ProfileIn, SettingsIn
from jyotish_api.security import DB, ConsentedUser
from jyotish_api.services import charts, svg
from jyotish_api.services.report_text import ASC
from jyotish_api.settings import settings

router = APIRouter(prefix="/v1/profiles", tags=["profiles"])


def _limit(user: Any) -> int:
    return settings.max_profiles_astrologer if user.role in ("astrologer", "admin") else settings.max_profiles_user


def _birth_payload(body: ProfileIn) -> dict[str, Any]:
    d = body.model_dump(mode="json", exclude={"settings", "folder", "is_main"})
    if not d.get("tz_name") and d.get("utc_offset_minutes") is None:
        d["tz_name"] = charts.timezone_at(body.latitude, body.longitude)
    return d


def profile_out(p: Profile) -> dict[str, Any]:
    b = decrypt_json(p.birth_enc)
    return {
        "id": str(p.id),
        **b,
        "folder": p.folder,
        "settings": SettingsIn(**(p.settings or {})).model_dump(mode="json"),
        "is_main": p.is_main,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def get_owned(db: DB, user: Any, profile_id: str) -> Profile:
    try:
        pid = uuid.UUID(profile_id)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "profile not found") from None
    p = db.get(Profile, pid)
    # Someone else's profile looks exactly like a missing one (US-08).
    if p is None or p.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "profile not found")
    return p


def _validate(payload: dict[str, Any]) -> None:
    try:
        charts.birth_from(payload).moment()
    except InputError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


def _set_main(db: DB, user: Any, p: Profile) -> None:
    for other in db.scalars(select(Profile).where(Profile.user_id == user.id, Profile.id != p.id, Profile.is_main.is_(True))):
        other.is_main = False


@router.get("")
def list_profiles(user: ConsentedUser, db: DB, folder: str | None = None, q: str | None = None) -> dict[str, Any]:
    rows = list(
        db.scalars(select(Profile).where(Profile.user_id == user.id).order_by(Profile.is_main.desc(), Profile.created_at))
    )
    items = [profile_out(p) for p in rows]
    if folder is not None:
        items = [i for i in items if (i["folder"] or "") == folder]
    if q:
        items = [i for i in items if q.lower() in i["name"].lower()]  # names are encrypted, so filter here
    folders = sorted({p.folder for p in rows if p.folder})
    return {"items": items, "count": len(rows), "limit": _limit(user), "folders": folders}


@router.post("", status_code=201)
def create_profile(body: ProfileIn, user: ConsentedUser, db: DB) -> dict[str, Any]:
    count = db.scalar(select(func.count()).select_from(Profile).where(Profile.user_id == user.id)) or 0
    if count >= _limit(user):
        raise HTTPException(status.HTTP_409_CONFLICT, f"profile limit reached ({_limit(user)})")
    payload = _birth_payload(body)
    _validate(payload)
    p = Profile(
        user_id=user.id,
        birth_enc=encrypt_json(payload),
        folder=body.folder,
        settings=body.settings.model_dump(mode="json"),
        is_main=body.is_main or count == 0,
    )
    db.add(p)
    db.flush()
    if p.is_main:
        _set_main(db, user, p)
    db.commit()
    db.refresh(p)
    return profile_out(p)


@router.get("/{profile_id}")
def get_profile(profile_id: str, user: ConsentedUser, db: DB) -> dict[str, Any]:
    return profile_out(get_owned(db, user, profile_id))


@router.put("/{profile_id}")
def update_profile(profile_id: str, body: ProfileIn, user: ConsentedUser, db: DB) -> dict[str, Any]:
    p = get_owned(db, user, profile_id)
    payload = _birth_payload(body)
    _validate(payload)
    p.birth_enc = encrypt_json(payload)
    p.folder = body.folder
    p.settings = body.settings.model_dump(mode="json")
    p.is_main = body.is_main or p.is_main
    p.updated_at = datetime.now(UTC)
    if p.is_main:
        _set_main(db, user, p)
    db.commit()
    db.refresh(p)
    return profile_out(p)


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: str, user: ConsentedUser, db: DB) -> Response:
    p = get_owned(db, user, profile_id)
    db.delete(p)
    db.commit()
    return Response(status_code=204)


def _inputs(p: Profile, overrides: dict[str, Any] | None = None) -> tuple[Any, ChartSettings]:
    b = decrypt_json(p.birth_enc)
    s = dict(p.settings or {})
    s.update({k: v for k, v in (overrides or {}).items() if v is not None})
    return charts.birth_from(b), ChartSettings.from_dict(s)


Vargas = Annotated[str, Query(description="Comma-separated, e.g. D1,D9")]


@router.get("/{profile_id}/chart")
def profile_chart(
    profile_id: str,
    user: ConsentedUser,
    db: DB,
    vargas: Vargas = "D1,D9",
    bhava_chalit: bool = False,
    ayanamsa: str | None = None,
    node_type: str | None = None,
) -> Response:
    p = get_owned(db, user, profile_id)
    codes = tuple(v.strip().upper() for v in vargas.split(",") if v.strip())
    bad = [c for c in codes if c not in VARGA_CODES]
    if bad:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"unknown divisional charts: {bad}")
    try:
        birth, cs = _inputs(p, {"ayanamsa": ayanamsa, "node_type": node_type})
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return Response(charts.chart(birth, cs, codes, bhava_chalit), media_type="application/json")


@router.get("/{profile_id}/chart-layout")
def profile_chart_layout(
    profile_id: str,
    user: ConsentedUser,
    db: DB,
    varga: str = "D1",
    style: Literal["north", "south"] | None = None,
    lang: Lang = "en",
) -> dict[str, Any]:
    """Chart drawing as lines plus positioned labels, for the mobile app
    (US-83). It is the same layout the PDF reports and the web app use."""
    p = get_owned(db, user, profile_id)
    code = varga.strip().upper()
    if code not in VARGA_CODES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"unknown divisional chart: {varga}")
    birth, cs = _inputs(p)
    style = style or (p.settings or {}).get("chart_style", "north")
    c = charts.chart_dict(birth, cs, (code,))
    lines, labels = svg.layout(c, code, style or "north", names(lang), ASC[lang], "" if code == "D1" else code)
    return {
        "size": svg.SIZE,
        "varga": code,
        "style": style,
        "svg": f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg.SIZE} {svg.SIZE}">{lines}</svg>',
        "labels": [asdict(lb) for lb in labels],
    }


@router.get("/{profile_id}/readings")
def profile_readings(profile_id: str, user: ConsentedUser, db: DB, lang: Lang = "en") -> dict[str, Any]:
    p = get_owned(db, user, profile_id)
    birth, cs = _inputs(p)
    c = charts.chart_dict(birth, cs)
    return {"ruleset_version": c["interpretations"]["ruleset_version"], "lang": lang, "readings": charts.readings(c, lang)}


@router.get("/{profile_id}/transits")
def profile_transits(profile_id: str, user: ConsentedUser, db: DB, on: date | None = None) -> dict[str, Any]:
    p = get_owned(db, user, profile_id)
    birth, cs = _inputs(p)
    when = datetime.combine(on, datetime.min.time(), UTC).replace(hour=6) if on else datetime.now(UTC)
    return charts.transits(birth, cs, when)


@router.get("/{profile_id}/strength")
def profile_strength(profile_id: str, user: ConsentedUser, db: DB) -> dict[str, Any]:
    p = get_owned(db, user, profile_id)
    birth, cs = _inputs(p)
    return charts.strength(birth, cs)


@router.get("/{profile_id}/export.csv")
def profile_csv(profile_id: str, user: ConsentedUser, db: DB) -> Response:
    """Degree table for spreadsheets (US-73)."""
    import csv
    import io

    p = get_owned(db, user, profile_id)
    birth, cs = _inputs(p)
    c = charts.chart_dict(birth, cs, ("D1", "D9"))
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(
        [
            "body",
            "sign",
            "degree_in_sign",
            "dms",
            "longitude",
            "nakshatra",
            "pada",
            "house",
            "retrograde",
            "combust",
            "dignity",
            "navamsa_sign",
        ]
    )
    w.writerow(
        [
            "lagna",
            c["lagna"]["sign"],
            c["lagna"]["degree_in_sign"],
            c["lagna"]["dms"],
            c["lagna"]["longitude"],
            c["lagna"]["nakshatra"],
            c["lagna"]["pada"],
            1,
            "",
            "",
            "",
            c["vargas"]["D9"]["lagna_sign"],
        ]
    )
    for pl in c["planets"]:
        w.writerow(
            [
                pl["id"],
                pl["sign"],
                pl["degree_in_sign"],
                pl["dms"],
                pl["longitude"],
                pl["nakshatra"],
                pl["pada"],
                pl["house"],
                pl["retrograde"],
                pl["combust"],
                pl["dignity"],
                c["vargas"]["D9"]["planets"][pl["id"]]["sign"],
            ]
        )
    name = "".join(ch for ch in decrypt_json(p.birth_enc)["name"] if ch.isalnum() or ch in " -_")[:40] or "chart"
    return Response(
        "﻿" + buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}.csv"'},
    )

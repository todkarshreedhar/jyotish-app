"""Endpoints that need no saved profile: chart preview, places, Panchang,
matching (US-14, US-25, US-64, US-65 to US-67)."""

import json
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from jyotish_engine.matching import ashtakoota, manglik
from jyotish_engine.panchang import panchang
from jyotish_engine.settings import Ayanamsa, ChartSettings
from jyotish_engine.timeutil import InputError

from jyotish_api import cache
from jyotish_api.routers.profiles import _inputs, get_owned
from jyotish_api.schemas import ChartRequest, MatchRequest
from jyotish_api.security import DB, ConsentedUser
from jyotish_api.services import charts, places

router = APIRouter(prefix="/v1", tags=["tools"])


def _rate_limit(request: Request, bucket: str, per_minute: int) -> None:
    ip = request.client.host if request.client else "?"
    if cache.incr_window(f"jy:rl:{bucket}:{ip}", 60) > per_minute:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too many requests; slow down")


@router.post("/charts")
def chart_preview(body: ChartRequest, request: Request) -> Response:
    """Compute a chart without saving anything (used by the 'try it' form)."""
    _rate_limit(request, "chart", 60)
    try:
        birth = charts.birth_from(body.birth.model_dump(mode="json"))
        cs = ChartSettings.from_dict(body.settings.model_dump(mode="json"))
        return Response(charts.chart(birth, cs, tuple(body.vargas), body.bhava_chalit), media_type="application/json")
    except (InputError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get("/places/search")
def place_search(db: DB, request: Request, q: Annotated[str, Query(min_length=2, max_length=100)], limit: int = 10) -> dict[str, Any]:
    _rate_limit(request, "places", 120)
    return {"items": places.search(db, q, min(max(limit, 1), 20))}


@router.get("/places/timezone")
def place_timezone(lat: Annotated[float, Query(ge=-90, le=90)], lon: Annotated[float, Query(ge=-180, le=180)]) -> dict[str, Any]:
    """Time zone for manually entered coordinates."""
    return {"tz_name": charts.timezone_at(lat, lon)}


@router.get("/panchang")
def get_panchang(request: Request, on: date, lat: Annotated[float, Query(ge=-66, le=66)],
                 lon: Annotated[float, Query(ge=-180, le=180)], tz: str | None = None,
                 ayanamsa: Ayanamsa = Ayanamsa.LAHIRI) -> dict[str, Any]:
    _rate_limit(request, "panchang", 60)
    tz_name = tz or charts.timezone_at(lat, lon)
    if not tz_name:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown time zone for these coordinates")
    key = cache.make_key("panchang", {"d": on.isoformat(), "lat": round(lat, 4), "lon": round(lon, 4), "tz": tz_name, "a": str(ayanamsa)})
    hit = cache.get(key)
    if hit:
        return json.loads(hit)
    try:
        out = panchang(on, tz_name, lat, lon, ayanamsa)
    except (InputError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    cache.put(key, json.dumps(out))
    return out


def match_data(db: DB, user: Any, boy_id: str, girl_id: str, lang: str) -> dict[str, Any]:
    from jyotish_api.routers.profiles import profile_out

    out: dict[str, Any] = {}
    moons = {}
    for role, pid in (("boy", boy_id), ("girl", girl_id)):
        p = get_owned(db, user, pid)
        birth, cs = _inputs(p)
        c = charts.chart_dict(birth, cs, ("D1", "D9"))
        by = {pl["id"]: pl for pl in c["planets"]}
        moons[role] = by["moon"]["longitude"]
        po = profile_out(p)
        out[role] = {
            "profile": {"id": po["id"], "name": po["name"], "birth_date": po["birth_date"]},
            "chart": c,
            "manglik": manglik(by["mars"]["sign_index"], c["lagna"]["sign_index"], by["moon"]["sign_index"], by["venus"]["sign_index"]),
        }
    out["ashtakoota"] = ashtakoota(moons["boy"], moons["girl"])
    out["lang"] = lang
    return out


@router.post("/match")
def match(body: MatchRequest, user: ConsentedUser, db: DB) -> dict[str, Any]:
    return match_data(db, user, body.boy_profile_id, body.girl_profile_id, body.lang)

"""Turns stored profiles into engine inputs and caches chart snapshots."""

import json
from datetime import UTC, date, datetime, time
from typing import Any

from jyotish_engine.ashtakavarga import ashtakavarga
from jyotish_engine.chart import BirthData, compute_chart
from jyotish_engine.constants import SEVEN_GRAHAS, Graha
from jyotish_engine.rules import RULESET_VERSION as RULES_VERSION
from jyotish_engine.rules import load_rules, run_rules, texts
from jyotish_engine.settings import ChartSettings
from jyotish_engine.shadbala import shadbala
from jyotish_engine.timeutil import InputError, julian_day_ut
from jyotish_engine.transits import sade_sati, transit_positions
from jyotish_engine.version import ENGINE_VERSION
from timezonefinder import TimezoneFinder

from jyotish_api import cache

_tf: TimezoneFinder | None = None
RULES = load_rules()


def timezone_at(lat: float, lon: float) -> str | None:
    global _tf
    if _tf is None:
        _tf = TimezoneFinder(in_memory=True)
    return _tf.timezone_at(lat=lat, lng=lon)


def birth_from(b: dict[str, Any]) -> BirthData:
    tz = b.get("tz_name")
    off = b.get("utc_offset_minutes")
    if not tz and off is None:
        tz = timezone_at(float(b["latitude"]), float(b["longitude"]))
        if tz is None:
            raise InputError("could not find a time zone for these coordinates; please give a UTC offset")
    bd = b["birth_date"]
    bt = b["birth_time"]
    return BirthData(
        birth_date=bd if isinstance(bd, date) else date.fromisoformat(bd),
        birth_time=bt if isinstance(bt, time) else time.fromisoformat(bt),
        latitude=float(b["latitude"]),
        longitude=float(b["longitude"]),
        tz_name=tz,
        utc_offset_minutes=off,
        time_accuracy=b.get("time_accuracy", "exact"),
    )


def _key_payload(birth: BirthData, settings: ChartSettings, extra: dict[str, Any]) -> dict[str, Any]:
    return {
        "engine": ENGINE_VERSION,
        "rules": RULES_VERSION,
        "birth": [
            birth.birth_date.isoformat(),
            birth.birth_time.isoformat(),
            birth.latitude,
            birth.longitude,
            birth.tz_name,
            birth.utc_offset_minutes,
            birth.time_accuracy,
        ],
        "settings": settings.to_dict(),
        **extra,
    }


def chart(birth: BirthData, settings: ChartSettings, vargas: tuple[str, ...] = ("D1", "D9"), bhava_chalit: bool = False) -> str:
    """Return the chart as a JSON string (byte-identical for equal inputs)."""
    key = cache.make_key("chart", _key_payload(birth, settings, {"vargas": list(vargas), "bc": bhava_chalit}))
    hit = cache.get(key)
    if hit is not None:
        return hit
    data = compute_chart(birth, settings, vargas=vargas, bhava_chalit=bhava_chalit)
    data["interpretations"] = run_rules(data, RULES)
    out = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    cache.put(key, out)
    return out


def chart_dict(
    birth: BirthData, settings: ChartSettings, vargas: tuple[str, ...] = ("D1", "D9"), bhava_chalit: bool = False
) -> dict[str, Any]:
    return json.loads(chart(birth, settings, vargas, bhava_chalit))


def readings(chart_data: dict[str, Any], lang: str) -> list[dict[str, Any]]:
    t = texts(lang)
    out = []
    for r in chart_data["interpretations"]["results"]:
        txt = t.get(r["text_key"]) or texts("en")[r["text_key"]]
        out.append({**r, "title": txt["title"], "text": txt["text"]})
    return out


def transits(birth: BirthData, settings: ChartSettings, when: datetime) -> dict[str, Any]:
    c = chart_dict(birth, settings, ("D1",))
    moon_sign = next(p["sign_index"] for p in c["planets"] if p["id"] == "moon")
    jd = julian_day_ut(when.astimezone(UTC))
    key = cache.make_key("sadesati", _key_payload(birth, settings, {"moon": moon_sign}))
    ss_json = cache.get(key)
    if ss_json is None:
        ss = sade_sati(moon_sign, c["input"]["julian_day_ut"], settings, years=100)
        cache.put(key, json.dumps(ss))
    else:
        ss = json.loads(ss_json)
    current = None
    for cyc in ss["cycles"]:
        if cyc["start_jd"] <= jd < cyc["end_jd"]:
            phase = None
            for ph in cyc["phases"]:
                if ph["start"] <= when.astimezone(UTC).isoformat() < ph["end"]:
                    phase = ph["phase"]
            current = {"phase": phase, "cycle": cyc}
    return {
        "date": when.isoformat(),
        "julian_day_ut": round(jd, 6),
        "natal_lagna": c["lagna"]["sign"],
        "natal_moon_sign": c["planets"][1]["sign"],
        "planets": transit_positions(jd, c["lagna"]["sign_index"], moon_sign, settings),
        "sade_sati": {"cycles": ss["cycles"], "current": current},
    }


def strength(birth: BirthData, settings: ChartSettings) -> dict[str, Any]:
    c = chart_dict(birth, settings, ("D1",))
    signs = {Graha(p["id"]): p["sign_index"] for p in c["planets"] if Graha(p["id"]) in SEVEN_GRAHAS}
    return {
        "ashtakavarga": ashtakavarga(signs, c["lagna"]["sign_index"]),
        "shadbala": shadbala(
            c["input"]["julian_day_ut"],
            birth.latitude,
            birth.longitude,
            {p["id"]: p for p in c["planets"]},
            c["lagna"]["longitude"],
            settings.ayanamsa,
        ),
    }

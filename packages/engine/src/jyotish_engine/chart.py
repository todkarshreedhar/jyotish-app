"""Natal chart: the one function the API calls (pipeline steps 1-8).

The output is plain JSON-ready data. The same inputs and settings always give
byte-identical output (floats are rounded, keys are ordered), which lets the
API cache chart snapshots and lets users trace every number.
"""

from dataclasses import dataclass
from datetime import date, time
from typing import Any

from jyotish_engine import ephemeris
from jyotish_engine.constants import GRAHAS, SIGN_LORDS, Graha
from jyotish_engine.core import (
    combustion_orb,
    deg_in_sign,
    dignity,
    dms,
    house_from,
    is_combust,
    nakshatra_of,
    sign_key,
    sign_of,
)
from jyotish_engine.dasha import vimshottari
from jyotish_engine.settings import ChartSettings
from jyotish_engine.timeutil import BirthMoment, to_moment, validate_location
from jyotish_engine.vargas import VARGAS, varga_sign
from jyotish_engine.version import ENGINE_VERSION

ROUND = 7  # decimal places for degrees (~0.0004 arcsec)


@dataclass(frozen=True, slots=True)
class BirthData:
    birth_date: date
    birth_time: time
    latitude: float
    longitude: float
    tz_name: str | None = None
    utc_offset_minutes: int | None = None
    time_accuracy: str = "exact"  # exact | approximate | unknown

    def moment(self) -> BirthMoment:
        validate_location(self.latitude, self.longitude)
        return to_moment(self.birth_date, self.birth_time, self.tz_name, self.utc_offset_minutes)


def _r(x: float) -> float:
    return round(x, ROUND)


# Results that change if the birth time is wrong by a few minutes to hours.
TIME_SENSITIVE = ["lagna", "houses", "bhava_chalit", "dasha_dates", "navamsa_lagna", "moon_nakshatra_pada"]


def planet_positions(jd_ut: float, settings: ChartSettings) -> dict[Graha, ephemeris.BodyPosition]:
    return {g: ephemeris.body(jd_ut, g, settings.ayanamsa, settings.node_type) for g in GRAHAS}


def compute_chart(
    birth: BirthData,
    settings: ChartSettings | None = None,
    *,
    vargas: tuple[str, ...] = ("D1", "D9"),
    bhava_chalit: bool = False,
    dasha_levels: int = 3,
) -> dict[str, Any]:
    settings = settings or ChartSettings()
    m = birth.moment()
    jd = m.jd_ut

    pos = planet_positions(jd, settings)
    hd = ephemeris.houses(jd, birth.latitude, birth.longitude, settings.ayanamsa)
    asc = hd.ascendant
    lagna_sign = sign_of(asc)
    sign_positions = {g: sign_of(p.longitude) for g, p in pos.items()}
    sun_lon = pos[Graha.SUN].longitude
    sources = sorted({p.source for p in pos.values()})

    planets: list[dict[str, Any]] = []
    for g in GRAHAS:
        p = pos[g]
        s = sign_of(p.longitude)
        nk = nakshatra_of(p.longitude)
        combust = is_combust(g, p.longitude, sun_lon, p.retrograde)
        planets.append(
            {
                "id": str(g),
                "longitude": _r(p.longitude),
                "latitude": _r(p.latitude),
                "speed": _r(p.speed),
                "retrograde": p.retrograde,
                "sign": sign_key(s),
                "sign_index": s,
                "degree_in_sign": _r(deg_in_sign(p.longitude)),
                "dms": dms(deg_in_sign(p.longitude)),
                "house": house_from(s, lagna_sign),
                "nakshatra": nk.key,
                "nakshatra_index": nk.index,
                "pada": nk.pada,
                "nakshatra_lord": str(nk.lord),
                "sign_lord": str(SIGN_LORDS[s]),
                "dignity": dignity(g, p.longitude, sign_positions),
                "combust": combust,
                "combustion_orb": combustion_orb(g, p.retrograde),
            }
        )

    asc_nk = nakshatra_of(asc)
    houses = [
        {
            "house": h,
            "sign": sign_key((lagna_sign + h - 1) % 12),
            "sign_index": (lagna_sign + h - 1) % 12,
            "lord": str(SIGN_LORDS[(lagna_sign + h - 1) % 12]),
            "occupants": [str(g) for g in GRAHAS if house_from(sign_positions[g], lagna_sign) == h],
        }
        for h in range(1, 13)
    ]

    divisional: dict[str, Any] = {}
    for code in vargas:
        if code not in VARGAS:
            raise ValueError(f"unknown divisional chart {code}")
        v_lagna = varga_sign(code, asc)
        divisional[code] = {
            "name": VARGAS[code][1],
            "lagna_sign_index": v_lagna,
            "lagna_sign": sign_key(v_lagna),
            "planets": {
                str(g): {
                    "sign_index": (vs := varga_sign(code, pos[g].longitude)),
                    "sign": sign_key(vs),
                    "house": house_from(vs, v_lagna),
                }
                for g in GRAHAS
            },
        }

    dasha = vimshottari(pos[Graha.MOON].longitude, jd, settings.dasha_year_days, dasha_levels)

    result: dict[str, Any] = {
        "meta": {
            "engine_version": ENGINE_VERSION,
            "ephemeris": "swiss_ephemeris",
            "ephemeris_version": ephemeris.swe_version(),
            "ephemeris_source": sources,
            "ayanamsa": str(settings.ayanamsa),
            "ayanamsa_value": _r(ephemeris.ayanamsa(jd, settings.ayanamsa)),
            "settings": settings.to_dict(),
            "zodiac": "sidereal",
        },
        "input": {
            "local_datetime": m.local.isoformat(),
            "utc_datetime": m.utc.isoformat(),
            "tz_name": m.tz_name,
            "utc_offset_minutes": m.utc_offset_minutes,
            "julian_day_ut": round(jd, 8),
            "latitude": birth.latitude,
            "longitude": birth.longitude,
            "time_accuracy": birth.time_accuracy,
        },
        "lagna": {
            "longitude": _r(asc),
            "sign": sign_key(lagna_sign),
            "sign_index": lagna_sign,
            "degree_in_sign": _r(deg_in_sign(asc)),
            "dms": dms(deg_in_sign(asc)),
            "nakshatra": asc_nk.key,
            "pada": asc_nk.pada,
            "lord": str(SIGN_LORDS[lagna_sign]),
        },
        "planets": planets,
        "houses": houses,
        "vargas": divisional,
        "dasha": dasha.to_dict(dasha_levels),
        "time_sensitive": TIME_SENSITIVE if birth.time_accuracy != "exact" else [],
    }
    if bhava_chalit:
        result["bhava_chalit"] = compute_bhava_chalit(jd, birth.latitude, birth.longitude, settings, pos)
    return result


def compute_bhava_chalit(
    jd: float, lat: float, lon: float, settings: ChartSettings, pos: dict[Graha, ephemeris.BodyPosition]
) -> dict[str, Any]:
    """Sripati Bhava Chalit: cusps are the midpoints between Porphyry house
    middles (Swiss Ephemeris system 'S'). A planet belongs to the bhava whose
    start cusp it has passed."""
    hd = ephemeris.houses(jd, lat, lon, settings.ayanamsa, b"S")
    cusps = hd.cusps

    def bhava_of(x: float) -> int:
        for i in range(12):
            a, b = cusps[i], cusps[(i + 1) % 12]
            span = (b - a) % 360.0
            if (x - a) % 360.0 < span:
                return i + 1
        return 12

    return {
        "system": "sripati",
        "cusps": [_r(c) for c in cusps],
        "planets": {str(g): bhava_of(p.longitude) for g, p in pos.items()},
    }

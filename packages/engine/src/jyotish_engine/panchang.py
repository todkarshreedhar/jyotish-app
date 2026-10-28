"""Panchang (five limbs of the day): vara, tithi, nakshatra, yoga, karana.

The Hindu day runs from sunrise to sunrise, so the weekday and the "ruling"
limbs are taken at local sunrise. End times are found by bisection to about
one minute.
"""

from collections.abc import Callable
from datetime import date, time
from typing import Any

from jyotish_engine import ephemeris
from jyotish_engine.constants import NAKSHATRA_SPAN, NAKSHATRAS, Graha
from jyotish_engine.core import norm
from jyotish_engine.settings import Ayanamsa
from jyotish_engine.timeutil import jd_to_utc, to_moment

TITHIS = (
    "pratipada", "dwitiya", "tritiya", "chaturthi", "panchami", "shashthi", "saptami",
    "ashtami", "navami", "dashami", "ekadashi", "dwadashi", "trayodashi", "chaturdashi",
)  # fmt: skip
YOGAS = (
    "vishkambha", "priti", "ayushman", "saubhagya", "shobhana", "atiganda", "sukarma",
    "dhriti", "shula", "ganda", "vriddhi", "dhruva", "vyaghata", "harshana", "vajra",
    "siddhi", "vyatipata", "variyana", "parigha", "shiva", "siddha", "sadhya", "shubha",
    "shukla", "brahma", "indra", "vaidhriti",
)  # fmt: skip
MOVABLE_KARANAS = ("bava", "balava", "kaulava", "taitila", "gara", "vanija", "vishti")
VARAS = ("sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday")


def _sun_moon(jd: float) -> tuple[float, float]:
    # Tithi and karana use the elongation, which does not depend on ayanamsa.
    s = ephemeris.body(jd, Graha.SUN, Ayanamsa.LAHIRI).longitude
    m = ephemeris.body(jd, Graha.MOON, Ayanamsa.LAHIRI).longitude
    return s, m


def elongation(jd: float) -> float:
    s, m = _sun_moon(jd)
    return norm(m - s)


def tithi_index(jd: float) -> int:  # 0..29
    return int(elongation(jd) // 12.0) % 30


def karana_index(jd: float) -> int:  # 0..59
    return int(elongation(jd) // 6.0) % 60


def nakshatra_index(jd: float, ayanamsa: Ayanamsa = Ayanamsa.LAHIRI) -> int:
    m = ephemeris.body(jd, Graha.MOON, ayanamsa).longitude
    return int(m // NAKSHATRA_SPAN) % 27


def yoga_index(jd: float, ayanamsa: Ayanamsa = Ayanamsa.LAHIRI) -> int:
    s = ephemeris.body(jd, Graha.SUN, ayanamsa).longitude
    m = ephemeris.body(jd, Graha.MOON, ayanamsa).longitude
    return int(norm(s + m) // NAKSHATRA_SPAN) % 27


def tithi_name(i: int) -> dict[str, str]:
    paksha = "shukla" if i < 15 else "krishna"
    k = i % 15
    if k == 14:
        name = "purnima" if paksha == "shukla" else "amavasya"
    else:
        name = TITHIS[k]
    return {"paksha": paksha, "name": name}


def karana_name(i: int) -> str:
    if i == 0:
        return "kimstughna"
    if i >= 57:
        return ("shakuni", "chatushpada", "naga")[i - 57]
    return MOVABLE_KARANAS[(i - 1) % 7]


def find_change(fn: Callable[[float], int], start: float, max_days: float = 2.0, step: float = 1 / 24) -> float | None:
    """First moment after `start` when fn's value changes."""
    v0 = fn(start)
    t = start
    while t < start + max_days:
        t2 = t + step
        if fn(t2) != v0:
            lo, hi = t, t2
            while hi - lo > 1 / 2880:  # 30 seconds
                mid = (lo + hi) / 2
                if fn(mid) == v0:
                    lo = mid
                else:
                    hi = mid
            return hi
        t = t2
    return None


def _iso(jd: float | None) -> str | None:
    return jd_to_utc(jd).isoformat() if jd is not None else None


def _spans(fn: Callable[[float], int], namer: Callable[[int], Any], start: float, end: float) -> list[dict[str, Any]]:
    """All values of a limb between sunrise and next sunrise, with end times."""
    out = []
    t = start
    while t < end:
        i = fn(t)
        nxt = find_change(fn, t)
        out.append({"index": i, "name": namer(i), "ends": _iso(nxt)})
        if nxt is None or nxt >= end:
            break
        t = nxt + 1e-6
    return out


def panchang(day: date, tz_name: str, lat: float, lon: float, ayanamsa: Ayanamsa = Ayanamsa.LAHIRI) -> dict[str, Any]:
    """Panchang for a civil date at a place."""
    jd_local_midnight_ut = to_moment(day, time(0, 0), tz_name).jd_ut
    sunrise = ephemeris.rise_set(jd_local_midnight_ut, Graha.SUN, lat, lon, rise=True)
    if sunrise is None:
        raise ValueError("the Sun does not rise on this date at this latitude")
    sunset = ephemeris.rise_set(sunrise, Graha.SUN, lat, lon, rise=False)
    next_sunrise = ephemeris.rise_set(sunrise + 0.5, Graha.SUN, lat, lon, rise=True) or sunrise + 1
    moonrise = ephemeris.rise_set(jd_local_midnight_ut, Graha.MOON, lat, lon, rise=True)
    moonset = ephemeris.rise_set(jd_local_midnight_ut, Graha.MOON, lat, lon, rise=False)

    # The vara is the weekday of the sunrise, i.e. of the civil date asked for.
    vara = (day.weekday() + 1) % 7  # 0 = Sunday

    return {
        "sunrise": _iso(sunrise),
        "sunset": _iso(sunset),
        "next_sunrise": _iso(next_sunrise),
        "moonrise": _iso(moonrise),
        "moonset": _iso(moonset),
        "vara": {"index": vara, "name": VARAS[vara]},
        "tithi": _spans(tithi_index, tithi_name, sunrise, next_sunrise),
        "nakshatra": _spans(lambda t: nakshatra_index(t, ayanamsa), lambda i: NAKSHATRAS[i], sunrise, next_sunrise),
        "yoga": _spans(lambda t: yoga_index(t, ayanamsa), lambda i: YOGAS[i], sunrise, next_sunrise),
        "karana": _spans(karana_index, karana_name, sunrise, next_sunrise),
        "date": day.isoformat(),
        "tz_name": tz_name,
        "ayanamsa": str(ayanamsa),
    }

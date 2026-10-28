"""Transits (gochara) over a natal chart, and Sade Sati (US-37, US-38)."""

from dataclasses import dataclass
from typing import Any

from jyotish_engine import ephemeris
from jyotish_engine.constants import GRAHAS, Graha
from jyotish_engine.core import deg_in_sign, dms, house_from, nakshatra_of, sign_key, sign_of
from jyotish_engine.settings import ChartSettings
from jyotish_engine.timeutil import jd_to_utc


def transit_positions(jd: float, natal_lagna_sign: int, natal_moon_sign: int, settings: ChartSettings) -> list[dict[str, Any]]:
    out = []
    for g in GRAHAS:
        p = ephemeris.body(jd, g, settings.ayanamsa, settings.node_type)
        s = sign_of(p.longitude)
        nk = nakshatra_of(p.longitude)
        out.append(
            {
                "id": str(g),
                "longitude": round(p.longitude, 7),
                "sign": sign_key(s),
                "sign_index": s,
                "dms": dms(deg_in_sign(p.longitude)),
                "retrograde": p.retrograde,
                "nakshatra": nk.key,
                "pada": nk.pada,
                "house_from_lagna": house_from(s, natal_lagna_sign),
                "house_from_moon": house_from(s, natal_moon_sign),
            }
        )
    return out


@dataclass(frozen=True)
class Ingress:
    jd: float
    from_sign: int
    to_sign: int


def _sign_at(jd: float, g: Graha, settings: ChartSettings) -> int:
    return sign_of(ephemeris.body(jd, g, settings.ayanamsa, settings.node_type).longitude)


def sign_ingresses(g: Graha, start_jd: float, end_jd: float, settings: ChartSettings, step: float | None = None) -> list[Ingress]:
    """All moments the graha changes sidereal sign in [start, end), found by
    stepping and then bisecting to about one minute."""
    if step is None:
        step = {Graha.MOON: 0.5, Graha.SUN: 2.0, Graha.MERCURY: 1.0, Graha.VENUS: 1.0, Graha.MARS: 2.0}.get(g, 4.0)
    out: list[Ingress] = []
    t = start_jd
    s = _sign_at(t, g, settings)
    while t < end_jd:
        t2 = min(t + step, end_jd)
        s2 = _sign_at(t2, g, settings)
        if s2 != s:
            lo, hi = t, t2
            while hi - lo > 1 / 1440:
                mid = (lo + hi) / 2
                if _sign_at(mid, g, settings) == s:
                    lo = mid
                else:
                    hi = mid
            out.append(Ingress(hi, s, s2))
            s = s2
        t = t2
    return out


PHASES = {-1: "rising", 0: "peak", 1: "setting"}
MERGE_GAP_DAYS = 400


def sade_sati(natal_moon_sign: int, birth_jd: float, settings: ChartSettings, years: int = 100, now_jd: float | None = None) -> dict[str, Any]:
    """Sade Sati: transit Saturn in the 12th, 1st or 2nd sign from the natal
    Moon. Retrograde back-and-forth is folded into one cycle; each phase runs
    from the first entry to the last exit of its sign within the cycle."""
    end_jd = birth_jd + years * 365.25
    ing = sign_ingresses(Graha.SATURN, birth_jd, end_jd, settings)
    targets = {(natal_moon_sign - 1) % 12: -1, natal_moon_sign: 0, (natal_moon_sign + 1) % 12: 1}

    # Build contiguous sign intervals.
    intervals: list[tuple[int, float, float]] = []
    t0 = birth_jd
    cur = _sign_at(birth_jd, Graha.SATURN, settings)
    for i in ing:
        intervals.append((cur, t0, i.jd))
        cur, t0 = i.to_sign, i.jd
    intervals.append((cur, t0, end_jd))

    # Group target-sign intervals into cycles. A retrograde exit and re-entry
    # within MERGE_GAP days belongs to the same cycle.
    blocks: list[list[tuple[int, float, float]]] = []
    for sgn, a, b in intervals:
        if sgn not in targets:
            continue
        if blocks and a - blocks[-1][-1][2] < MERGE_GAP_DAYS:
            blocks[-1].append((sgn, a, b))
        else:
            blocks.append([(sgn, a, b)])
    cycles = [_cycle(b, targets, birth_jd, end_jd) for b in blocks]

    current = None
    if now_jd is not None:
        for c in cycles:
            if c["start_jd"] <= now_jd < c["end_jd"]:
                s_now = _sign_at(now_jd, Graha.SATURN, settings)
                current = {"active": s_now in targets, "phase": PHASES.get(targets.get(s_now, 99)), "cycle": c}
                break
    return {"natal_moon_sign": sign_key(natal_moon_sign), "cycles": cycles, "current": current}


def _cycle(block: list[tuple[int, float, float]], targets: dict[int, int], birth_jd: float, end_jd: float) -> dict[str, Any]:
    start, end = block[0][1], block[-1][2]
    phases = []
    for off in (-1, 0, 1):
        spans = [(a, b) for s, a, b in block if targets[s] == off]
        if spans:
            phases.append(
                {
                    "phase": PHASES[off],
                    "start": jd_to_utc(spans[0][0]).isoformat(),
                    "end": jd_to_utc(spans[-1][1]).isoformat(),
                }
            )
    return {
        "start": jd_to_utc(start).isoformat(),
        "end": jd_to_utc(end).isoformat(),
        "start_jd": round(start, 5),
        "end_jd": round(end, 5),
        "starts_before_birth": start <= birth_jd,
        "ends_after_range": end >= end_jd,
        "phases": phases,
    }

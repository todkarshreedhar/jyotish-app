"""Shadbala, the six-fold planetary strength (BPHS ch. 27), in virupas.

60 virupas = 1 rupa. Components:
  1 Sthana (positional): uchcha, saptavargaja, ojayugma, kendradi, drekkana
  2 Dig (directional)
  3 Kala (temporal): natonnata, paksha, tribhaga, abda, masa, vara, hora, ayana
  4 Chesta (motional)
  5 Naisargika (natural)
  6 Drik (aspectual)

Method notes for the domain expert (gate for US-62):
  * Chesta uses the eight motion classes of BPHS from the planet's speed
    relative to its mean speed, not the cheshta-kendra formula.
  * Drik uses the virupa drishti curve with B. V. Raman's additions for the
    special aspects of Mars, Jupiter and Saturn.
  * Yuddha (planetary war) is not applied yet.
  * Abda and masa lords are counted from the Kali Yuga epoch (Ahargana).
"""

import math
from typing import Any

from jyotish_engine import ephemeris
from jyotish_engine.constants import EXALTATION, MOOLATRIKONA, OWN_SIGNS, SEVEN_GRAHAS, SIGN_LORDS, WEEKDAY_LORDS, Graha
from jyotish_engine.core import angular_distance, compound_relation, deg_in_sign, house_from, norm, sign_of
from jyotish_engine.vargas import varga_sign

S, MO, MA, ME, J, V, SA = SEVEN_GRAHAS

NAISARGIKA = {S: 60.0, MO: 51.43, V: 42.86, J: 34.29, ME: 25.71, MA: 17.14, SA: 8.57}
REQUIRED_RUPAS = {S: 6.5, MO: 6.0, MA: 5.0, ME: 7.0, J: 6.5, V: 5.5, SA: 5.0}
# Geocentric mean daily motion; Mercury and Venus keep pace with the Sun on average.
MEAN_SPEED = {MA: 0.524, ME: 0.9856, J: 0.0831, V: 0.9856, SA: 0.0335}
KALI_EPOCH_JD = 588465.5
CHALDEAN = (S, V, ME, MO, SA, J, MA)  # hora order

_VARGA_POINTS = {
    "moolatrikona": 45.0,
    "own": 30.0,
    "great_friend": 22.5,
    "friend": 15.0,
    "neutral": 7.5,
    "enemy": 3.75,
    "great_enemy": 1.875,
}


def _uchcha(g: Graha, lon: float) -> float:
    ex_sign, ex_deg = EXALTATION[g]
    deb_point = norm(ex_sign * 30 + ex_deg + 180)
    return angular_distance(lon, deb_point) / 3.0


def _varga_relation(g: Graha, vsign: int, rasi_signs: dict[Graha, int]) -> str:
    if vsign in OWN_SIGNS[g]:
        return "own"
    lord = SIGN_LORDS[vsign]
    return compound_relation(g, lord, rasi_signs[g], rasi_signs[lord])


def _saptavargaja(g: Graha, lon: float, rasi_signs: dict[Graha, int]) -> float:
    total = 0.0
    for code in ("D1", "D2", "D3", "D7", "D9", "D12", "D30"):
        vs = varga_sign(code, lon)
        if code == "D1":
            mt = MOOLATRIKONA[g]
            if vs == mt[0] and mt[1] <= deg_in_sign(lon) < mt[2]:
                total += _VARGA_POINTS["moolatrikona"]
                continue
        total += _VARGA_POINTS[_varga_relation(g, vs, rasi_signs)]
    return total


def _ojayugma(g: Graha, lon: float) -> float:
    female = g in (MO, V)
    pts = 0.0
    for s in (sign_of(lon), varga_sign("D9", lon)):
        even = s % 2 == 1
        if even == female:
            pts += 15.0
    return pts


def _kendradi(house: int) -> float:
    if house in (1, 4, 7, 10):
        return 60.0
    if house in (2, 5, 8, 11):
        return 30.0
    return 15.0


def _drekkana(g: Graha, lon: float) -> float:
    part = int(deg_in_sign(lon) // 10)
    want = {S: 0, MA: 0, J: 0, ME: 1, SA: 1, MO: 2, V: 2}[g]
    return 15.0 if part == want else 0.0


def _dig(g: Graha, lon: float, asc: float, mc: float) -> float:
    strong = {J: asc, ME: asc, S: mc, MA: mc, SA: norm(asc + 180), MO: norm(mc + 180), V: norm(mc + 180)}[g]
    weak = norm(strong + 180)
    return angular_distance(lon, weak) / 3.0


def _drishti(d: float) -> float:
    """Aspect strength (virupas) for an angular distance d = aspected - aspecting."""
    if 30 <= d < 60:
        return (d - 30) / 2
    if 60 <= d < 90:
        return d - 60 + 15
    if 90 <= d < 120:
        return (120 - d) / 2 + 30
    if 120 <= d < 150:
        return 150 - d
    if 150 <= d < 180:
        return (d - 150) * 2
    if 180 <= d < 300:
        return (300 - d) / 2
    return 0.0


def _special(g: Graha, d: float) -> float:
    if g is MA and (90 <= d < 120 or 210 <= d < 240):
        return 15.0
    if g is J and (120 <= d < 150 or 240 <= d < 270):
        return 30.0
    if g is SA and (60 <= d < 90 or 270 <= d < 300):
        return 45.0
    return 0.0


def _motion_class(g: Graha, speed: float) -> tuple[str, float]:
    r = speed / MEAN_SPEED[g]
    if r < 0:
        return "vakra", 60.0
    if r < 0.1:
        return "vikala", 15.0
    if r < 0.5:
        return "mandatara", 15.0
    if r < 0.9:
        return "manda", 30.0
    if r < 1.1:
        return "sama", 7.5
    if r < 1.5:
        return "chara", 45.0
    return "atichara", 30.0


def shadbala(jd: float, lat: float, lon_geo: float, planets: dict[str, dict[str, Any]], lagna_lon: float, ayanamsa: Any) -> dict[str, Any]:
    """planets: chart["planets"] keyed by id (sidereal longitudes, speeds)."""
    lon = {g: float(planets[str(g)]["longitude"]) for g in SEVEN_GRAHAS}
    speed = {g: float(planets[str(g)]["speed"]) for g in SEVEN_GRAHAS}
    rasi_signs = {g: sign_of(lon[g]) for g in SEVEN_GRAHAS}
    hd = ephemeris.houses(jd, lat, lon_geo, ayanamsa)
    asc, mc = lagna_lon, hd.mc
    lagna_sign = sign_of(asc)

    # Time of day: Sun's hour angle, sunrise/sunset of the birth day.
    sunrise = ephemeris.rise_set(jd - 1.0, S, lat, lon_geo, rise=True)
    while sunrise is not None and sunrise + 1.0 <= jd:
        nxt = ephemeris.rise_set(sunrise + 0.1, S, lat, lon_geo, rise=True)
        if nxt is None or nxt > jd:
            break
        sunrise = nxt
    sunset = ephemeris.rise_set(sunrise, S, lat, lon_geo, rise=False) if sunrise else None
    next_rise = ephemeris.rise_set(sunrise + 0.1, S, lat, lon_geo, rise=True) if sunrise else None
    is_day = bool(sunrise and sunset and sunrise <= jd < sunset)

    sun_trop = ephemeris.tropical_longitude(jd, S)
    # Local apparent time from the Sun's hour angle (ARMC - RA of Sun).
    eps = math.radians(23.4393)
    ra_sun = math.degrees(math.atan2(math.cos(eps) * math.sin(math.radians(sun_trop)), math.cos(math.radians(sun_trop)))) % 360
    ha = (hd.armc - ra_sun + 540) % 360 - 180  # -180..180, 0 at noon
    unnata = 180 - abs(ha)  # 180 at noon, 0 at midnight

    elong = norm(lon[MO] - lon[S])
    e = elong if elong <= 180 else 360 - elong
    waxing = elong < 180
    benefics = {J, V, ME} | ({MO} if waxing else set())

    # Weekday (Hindu day from sunrise) and lords
    weekday = int(math.floor((sunrise if sunrise else jd) + 0.5 + 1)) % 7  # 0 = Sunday
    if sunrise and jd < sunrise:
        weekday = (weekday - 1) % 7
    vara_lord = WEEKDAY_LORDS[weekday]
    hours_since_rise = ((jd - sunrise) * 24) if sunrise else 0.0
    hora_lord = CHALDEAN[(CHALDEAN.index(vara_lord) + int(hours_since_rise)) % 7]
    ahargana = int(jd - KALI_EPOCH_JD)
    abda_lord = WEEKDAY_LORDS[(5 + 3 * (ahargana // 360)) % 7]
    masa_lord = WEEKDAY_LORDS[(5 + 2 * (ahargana // 30)) % 7]

    # Tribhaga
    if sunrise and sunset and next_rise:
        if is_day:
            third = int(3 * (jd - sunrise) / (sunset - sunrise))
            tribhaga_lord = (ME, S, SA)[min(third, 2)]
        else:
            start = sunset if jd >= sunset else (sunset - 1.0)
            third = int(3 * (jd - start) / max(next_rise - sunset, 1e-6))
            tribhaga_lord = (MO, V, MA)[min(max(third, 0), 2)]
    else:
        tribhaga_lord = None

    out: dict[str, Any] = {}
    for g in SEVEN_GRAHAS:
        sthana = {
            "uchcha": _uchcha(g, lon[g]),
            "saptavargaja": _saptavargaja(g, lon[g], rasi_signs),
            "ojayugma": _ojayugma(g, lon[g]),
            "kendradi": _kendradi(house_from(rasi_signs[g], lagna_sign)),
            "drekkana": _drekkana(g, lon[g]),
        }
        dig = _dig(g, lon[g], asc, mc)

        if g is ME:
            natonnata = 60.0
        elif g in (S, J, V):
            natonnata = unnata / 3
        else:
            natonnata = 60 - unnata / 3
        paksha = e / 3 if g in benefics else 60 - e / 3
        if g is MO:
            paksha *= 2
        dec = ephemeris.declination(jd, g)
        if g is ME:
            ayana = (24 + abs(dec)) / 48 * 60
        elif g in (MO, SA):
            ayana = (24 - dec) / 48 * 60
        else:
            ayana = (24 + dec) / 48 * 60
        if g is S:
            ayana *= 2
        kala = {
            "natonnata": natonnata,
            "paksha": paksha,
            "tribhaga": 60.0 if (g is J or g == tribhaga_lord) else 0.0,
            "abda": 15.0 if g == abda_lord else 0.0,
            "masa": 30.0 if g == masa_lord else 0.0,
            "vara": 45.0 if g == vara_lord else 0.0,
            "hora": 60.0 if g == hora_lord else 0.0,
            "ayana": ayana,
        }
        if g is S:
            chesta, motion = kala["ayana"], "ayana"
        elif g is MO:
            chesta, motion = kala["paksha"], "paksha"
        else:
            motion, chesta = _motion_class(g, speed[g])

        drik = 0.0
        for a in SEVEN_GRAHAS:
            if a == g:
                continue
            d = norm(lon[g] - lon[a])
            val = _drishti(d) + _special(a, d)
            drik += val if a in benefics else -val
        drik /= 4.0

        total = sum(sthana.values()) + dig + sum(kala.values()) + chesta + NAISARGIKA[g] + drik
        out[str(g)] = {
            "sthana": {k: round(v, 2) for k, v in sthana.items()},
            "sthana_total": round(sum(sthana.values()), 2),
            "dig": round(dig, 2),
            "kala": {k: round(v, 2) for k, v in kala.items()},
            "kala_total": round(sum(kala.values()), 2),
            "chesta": round(chesta, 2),
            "motion": motion,
            "naisargika": NAISARGIKA[g],
            "drik": round(drik, 2),
            "total_virupas": round(total, 2),
            "total_rupas": round(total / 60, 2),
            "required_rupas": REQUIRED_RUPAS[g],
            "ratio": round(total / 60 / REQUIRED_RUPAS[g], 2),
        }
    ranking = sorted(out, key=lambda k: -out[k]["ratio"])
    return {"planets": out, "ranking": ranking, "method_notes": __doc__.split("Method notes for the domain expert (gate for US-62):")[1].strip()}  # type: ignore[union-attr]

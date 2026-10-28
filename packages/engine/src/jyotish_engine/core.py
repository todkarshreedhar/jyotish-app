"""Small pure helpers: sign, Nakshatra, pada, dignity, combustion, DMS."""

from dataclasses import dataclass

from jyotish_engine.constants import (
    COMBUSTION_ORBS,
    COMBUSTION_ORBS_RETRO,
    EXALTATION,
    MOOLATRIKONA,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN,
    NAKSHATRAS,
    NATURAL_FRIENDS,
    NATURAL_NEUTRALS,
    OWN_SIGNS,
    PADA_SPAN,
    SIGN_LORDS,
    SIGNS,
    Graha,
)

EPS = 1e-9


def norm(deg: float) -> float:
    d = deg % 360.0
    return 0.0 if abs(d - 360.0) < EPS else d


def sign_of(lon: float) -> int:
    return int(norm(lon) // 30.0) % 12


def deg_in_sign(lon: float) -> float:
    return norm(lon) - 30.0 * sign_of(lon)


def angular_distance(a: float, b: float) -> float:
    d = abs(norm(a) - norm(b)) % 360.0
    return 360.0 - d if d > 180.0 else d


def house_from(sign: int, reference_sign: int) -> int:
    """1-based house of `sign` counted from `reference_sign` (whole sign)."""
    return (sign - reference_sign) % 12 + 1


@dataclass(frozen=True, slots=True)
class NakshatraInfo:
    index: int  # 0..26
    key: str
    pada: int  # 1..4
    lord: Graha
    fraction_elapsed: float  # 0..1 within the Nakshatra


def nakshatra_of(lon: float) -> NakshatraInfo:
    lon = norm(lon)
    idx = int(lon // NAKSHATRA_SPAN) % 27
    within = lon - idx * NAKSHATRA_SPAN
    # guard against floating noise at exact boundaries such as 13°20'
    if NAKSHATRA_SPAN - within < 1e-10:
        idx = (idx + 1) % 27
        within = 0.0
    pada = min(4, int(within // PADA_SPAN) + 1)
    return NakshatraInfo(idx, NAKSHATRAS[idx], pada, NAKSHATRA_LORDS[idx], within / NAKSHATRA_SPAN)


def dms(deg: float) -> str:
    """Format degrees as D°MM'SS" (rounded to the second)."""
    total = round(abs(deg) * 3600)
    d, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    sign = "-" if deg < 0 else ""
    return f"{sign}{d}°{m:02d}'{s:02d}\""


def natural_relation(of: Graha, to: Graha) -> str:
    if of in (Graha.RAHU, Graha.KETU) or to in (Graha.RAHU, Graha.KETU):
        return "neutral"
    if to in NATURAL_FRIENDS[of]:
        return "friend"
    if to in NATURAL_NEUTRALS[of]:
        return "neutral"
    return "enemy"


def temporary_relation(of_sign: int, to_sign: int) -> str:
    """Tatkalika: planets in 2,3,4,10,11,12 from a planet are its friends."""
    h = house_from(to_sign, of_sign)
    return "friend" if h in (2, 3, 4, 10, 11, 12) else "enemy"


_COMPOUND = {
    ("friend", "friend"): "great_friend",
    ("friend", "enemy"): "neutral",
    ("neutral", "friend"): "friend",
    ("neutral", "enemy"): "enemy",
    ("enemy", "friend"): "neutral",
    ("enemy", "enemy"): "great_enemy",
}


def compound_relation(of: Graha, to: Graha, of_sign: int, to_sign: int) -> str:
    """Panchadha maitri (BPHS ch. 3): natural + temporary relationship."""
    nat = natural_relation(of, to)
    if of in (Graha.RAHU, Graha.KETU) or to in (Graha.RAHU, Graha.KETU):
        return nat
    return _COMPOUND[(nat, temporary_relation(of_sign, to_sign))]


def dignity(graha: Graha, lon: float, sign_positions: dict[Graha, int] | None = None) -> str:
    """Dignity of a graha: exalted, moolatrikona, own, debilitated, or the
    compound relationship with the sign lord (great_friend .. great_enemy).
    """
    s = sign_of(lon)
    d = deg_in_sign(lon)
    ex_sign, ex_deg = EXALTATION[graha]
    deb_sign = (ex_sign + 6) % 12
    mt = MOOLATRIKONA.get(graha)

    if s == ex_sign:
        # Moon and Mercury share their exaltation sign with Moolatrikona.
        if graha is Graha.MOON and d >= ex_deg:
            return "moolatrikona"
        if graha is Graha.MERCURY and d >= ex_deg:
            return "moolatrikona" if d < 20.0 else "own"
        return "exalted"
    if s == deb_sign:
        return "debilitated"
    if mt and s == mt[0] and mt[1] <= d < mt[2]:
        return "moolatrikona"
    if s in OWN_SIGNS[graha]:
        return "own"
    lord = SIGN_LORDS[s]
    if lord == graha:
        return "own"
    if sign_positions and graha in sign_positions and lord in sign_positions:
        return compound_relation(graha, lord, sign_positions[graha], sign_positions[lord])
    return natural_relation(graha, lord)


def combustion_orb(graha: Graha, retrograde: bool) -> float | None:
    if graha in (Graha.SUN, Graha.RAHU, Graha.KETU):
        return None
    if retrograde and graha in COMBUSTION_ORBS_RETRO:
        return COMBUSTION_ORBS_RETRO[graha]
    return COMBUSTION_ORBS[graha]


def is_combust(graha: Graha, lon: float, sun_lon: float, retrograde: bool) -> bool:
    orb = combustion_orb(graha, retrograde)
    return orb is not None and angular_distance(lon, sun_lon) < orb


def sign_key(index: int) -> str:
    return SIGNS[index % 12]

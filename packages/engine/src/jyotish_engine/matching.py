"""Ashtakoota marriage matching (Guna Milan, 36 points) and Manglik check.

Tables follow the common North Indian tradition. A few kootas have regional
variants (Vashya and Gana scoring in particular); the tables are kept in one
place so the domain expert can review and adjust them.
"""

from typing import Any

from jyotish_engine.constants import SIGN_LORDS, Graha
from jyotish_engine.core import house_from, natural_relation

# 0 Brahmin, 1 Kshatriya, 2 Vaishya, 3 Shudra (by Moon sign)
VARNA_OF_SIGN = (1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0)
VARNAS = ("brahmin", "kshatriya", "vaishya", "shudra")

# 0 chatushpada (quadruped), 1 manava (human), 2 jalachara (water),
# 3 vanachara (wild), 4 keeta (insect)
VASHYAS = ("chatushpada", "manava", "jalachara", "vanachara", "keeta")
VASHYA_POINTS = (
    (2.0, 1.0, 1.0, 0.5, 1.0),
    (1.0, 2.0, 0.5, 0.0, 1.0),
    (1.0, 0.5, 2.0, 1.0, 1.0),
    (0.5, 0.0, 1.0, 2.0, 0.0),
    (1.0, 1.0, 1.0, 0.0, 2.0),
)


def vashya_of(moon_lon: float) -> int:
    s = int(moon_lon // 30) % 12
    d = moon_lon % 30
    if s in (0, 1):
        return 0
    if s == 8:
        return 1 if d < 15 else 0
    if s == 9:
        return 0 if d < 15 else 2
    if s in (2, 5, 6, 10):
        return 1
    if s in (3, 11):
        return 2
    if s == 4:
        return 3
    return 4  # Scorpio


YONIS = ("horse", "elephant", "sheep", "serpent", "dog", "cat", "rat", "cow",
         "buffalo", "tiger", "deer", "monkey", "mongoose", "lion")  # fmt: skip
YONI_OF_NAKSHATRA = (0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10, 4, 11, 12, 11, 13, 0, 13, 7, 1)
YONI_POINTS = (
    (4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1),
    (2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0),
    (2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1),
    (3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2),
    (2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1),
    (2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1),
    (2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2),
    (1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1),
    (0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1),
    (1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1),
    (3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1),
    (3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2),
    (2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2),
    (1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4),
)

GANAS = ("deva", "manushya", "rakshasa")
GANA_OF_NAKSHATRA = (0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1, 0, 2, 2, 1, 1, 0)
# GANA_POINTS[girl][boy]
GANA_POINTS = ((6, 5, 1), (6, 6, 0), (0, 0, 6))

NADIS = ("adi", "madhya", "antya")
NADI_OF_NAKSHATRA = tuple((0, 1, 2, 2, 1, 0)[i % 6] for i in range(27))

_MAITRI = {
    ("friend", "friend"): 5.0,
    ("friend", "neutral"): 4.0,
    ("neutral", "friend"): 4.0,
    ("neutral", "neutral"): 3.0,
    ("friend", "enemy"): 1.0,
    ("enemy", "friend"): 1.0,
    ("neutral", "enemy"): 0.5,
    ("enemy", "neutral"): 0.5,
    ("enemy", "enemy"): 0.0,
}


def _tara_ok(from_nak: int, to_nak: int) -> bool:
    count = (to_nak - from_nak) % 27 + 1
    return count % 9 not in (3, 5, 7)


def ashtakoota(boy_moon: float, girl_moon: float) -> dict[str, Any]:
    """Score two charts from their sidereal Moon longitudes."""
    bs, gs = int(boy_moon // 30) % 12, int(girl_moon // 30) % 12
    bn, gn = int(boy_moon // (360 / 27)) % 27, int(girl_moon // (360 / 27)) % 27

    kootas: list[dict[str, Any]] = []

    bv, gv = VARNA_OF_SIGN[bs], VARNA_OF_SIGN[gs]
    # Lower index = higher varna. Full point if the boy's varna is equal or higher.
    kootas.append({"koota": "varna", "max": 1, "points": 1.0 if bv <= gv else 0.0, "boy": VARNAS[bv], "girl": VARNAS[gv]})

    bva, gva = vashya_of(boy_moon), vashya_of(girl_moon)
    kootas.append({"koota": "vashya", "max": 2, "points": VASHYA_POINTS[bva][gva], "boy": VASHYAS[bva], "girl": VASHYAS[gva]})

    tara = 1.5 * _tara_ok(gn, bn) + 1.5 * _tara_ok(bn, gn)
    kootas.append({"koota": "tara", "max": 3, "points": tara})

    by, gy = YONI_OF_NAKSHATRA[bn], YONI_OF_NAKSHATRA[gn]
    kootas.append({"koota": "yoni", "max": 4, "points": float(YONI_POINTS[by][gy]), "boy": YONIS[by], "girl": YONIS[gy]})

    bl, gl = SIGN_LORDS[bs], SIGN_LORDS[gs]
    maitri = 5.0 if bl == gl else _MAITRI[(natural_relation(bl, gl), natural_relation(gl, bl))]
    kootas.append({"koota": "graha_maitri", "max": 5, "points": maitri, "boy": str(bl), "girl": str(gl)})

    bg, gg = GANA_OF_NAKSHATRA[bn], GANA_OF_NAKSHATRA[gn]
    kootas.append({"koota": "gana", "max": 6, "points": float(GANA_POINTS[gg][bg]), "boy": GANAS[bg], "girl": GANAS[gg]})

    dist = house_from(gs, bs)  # girl's sign counted from boy's
    back = house_from(bs, gs)
    bad = {dist, back} in ({2, 12}, {5, 9}, {6, 8})
    kootas.append({"koota": "bhakoot", "max": 7, "points": 0.0 if bad else 7.0, "distance": [dist, back]})

    bnad, gnad = NADI_OF_NAKSHATRA[bn], NADI_OF_NAKSHATRA[gn]
    kootas.append({"koota": "nadi", "max": 8, "points": 0.0 if bnad == gnad else 8.0, "boy": NADIS[bnad], "girl": NADIS[gnad]})

    total = sum(k["points"] for k in kootas)
    return {
        "kootas": kootas,
        "total": total,
        "max": 36,
        "verdict": "excellent" if total >= 28 else "good" if total >= 18 else "not_recommended",
        "doshas": {
            "nadi": bnad == gnad,
            "bhakoot": bad,
        },
    }


MANGLIK_HOUSES = (1, 2, 4, 7, 8, 12)


def manglik(mars_sign: int, lagna_sign: int, moon_sign: int, venus_sign: int) -> dict[str, Any]:
    """Mangal dosha: Mars in houses 1, 2, 4, 7, 8 or 12 counted from Lagna,
    Moon or Venus (the common rule; exceptions are listed for the reader but
    not applied automatically)."""
    from_lagna = house_from(mars_sign, lagna_sign)
    from_moon = house_from(mars_sign, moon_sign)
    from_venus = house_from(mars_sign, venus_sign)
    flags = {
        "lagna": from_lagna in MANGLIK_HOUSES,
        "moon": from_moon in MANGLIK_HOUSES,
        "venus": from_venus in MANGLIK_HOUSES,
    }
    own_or_exalted = mars_sign in (0, 7, 9)
    return {
        "is_manglik": flags["lagna"] or flags["moon"],
        "from": {"lagna": from_lagna, "moon": from_moon, "venus": from_venus},
        "flags": flags,
        "rule": "Mars in 1, 2, 4, 7, 8 or 12 from Lagna or Moon",
        "mitigations": ["mars_own_or_exalted"] if own_or_exalted else [],
    }


__all__ = ["ashtakoota", "manglik", "Graha"]

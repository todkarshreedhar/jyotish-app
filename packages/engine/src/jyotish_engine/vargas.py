"""Divisional charts (Shodashvarga) following BPHS ch. 6 (Parashari method).

Each function maps a sidereal longitude to a sign index 0..11.
"""

from collections.abc import Callable

from jyotish_engine.core import deg_in_sign, norm, sign_of

VargaFn = Callable[[float], int]


def _odd(s: int) -> bool:  # Aries, Gemini, ... are odd signs (index 0, 2, ...)
    return s % 2 == 0


def _modality(s: int) -> int:  # 0 movable, 1 fixed, 2 dual
    return s % 3


def _part(lon: float, n: int) -> tuple[int, int]:
    s = sign_of(lon)
    d = deg_in_sign(lon)
    k = min(n - 1, int(d * n / 30.0 + 1e-12))
    return s, k


def d1(lon: float) -> int:
    return sign_of(lon)


def d2(lon: float) -> int:
    s, k = _part(lon, 2)
    sun, moon = 4, 3  # Leo, Cancer
    if _odd(s):
        return sun if k == 0 else moon
    return moon if k == 0 else sun


def d3(lon: float) -> int:
    s, k = _part(lon, 3)
    return (s + 4 * k) % 12


def d4(lon: float) -> int:
    s, k = _part(lon, 4)
    return (s + 3 * k) % 12


def d7(lon: float) -> int:
    s, k = _part(lon, 7)
    start = s if _odd(s) else s + 6
    return (start + k) % 12


def d9(lon: float) -> int:
    return int(norm(lon) * 9 / 30.0 + 1e-12) % 12


def d10(lon: float) -> int:
    s, k = _part(lon, 10)
    start = s if _odd(s) else s + 8
    return (start + k) % 12


def d12(lon: float) -> int:
    s, k = _part(lon, 12)
    return (s + k) % 12


def d16(lon: float) -> int:
    s, k = _part(lon, 16)
    start = (0, 4, 8)[_modality(s)]  # Aries, Leo, Sagittarius
    return (start + k) % 12


def d20(lon: float) -> int:
    s, k = _part(lon, 20)
    start = (0, 8, 4)[_modality(s)]  # Aries, Sagittarius, Leo
    return (start + k) % 12


def d24(lon: float) -> int:
    s, k = _part(lon, 24)
    start = 4 if _odd(s) else 3  # Leo for odd, Cancer for even
    return (start + k) % 12


def d27(lon: float) -> int:
    return int(norm(lon) * 27 / 30.0 + 1e-12) % 12


def d30(lon: float) -> int:
    s = sign_of(lon)
    d = deg_in_sign(lon)
    if _odd(s):
        # Mars 5, Saturn 5, Jupiter 8, Mercury 7, Venus 5
        bounds = ((5, 0), (10, 10), (18, 8), (25, 2), (30, 6))
    else:
        # Venus 5, Mercury 7, Jupiter 8, Saturn 5, Mars 5
        bounds = ((5, 1), (12, 5), (20, 11), (25, 9), (30, 7))
    for end, sign in bounds:
        if d < end:
            return sign
    return bounds[-1][1]


def d40(lon: float) -> int:
    s, k = _part(lon, 40)
    start = 0 if _odd(s) else 6
    return (start + k) % 12


def d45(lon: float) -> int:
    s, k = _part(lon, 45)
    start = (0, 4, 8)[_modality(s)]
    return (start + k) % 12


def d60(lon: float) -> int:
    s, k = _part(lon, 60)
    return (s + k) % 12


VARGAS: dict[str, tuple[VargaFn, str]] = {
    "D1": (d1, "rasi"),
    "D2": (d2, "hora"),
    "D3": (d3, "drekkana"),
    "D4": (d4, "chaturthamsa"),
    "D7": (d7, "saptamsa"),
    "D9": (d9, "navamsa"),
    "D10": (d10, "dasamsa"),
    "D12": (d12, "dwadasamsa"),
    "D16": (d16, "shodasamsa"),
    "D20": (d20, "vimsamsa"),
    "D24": (d24, "chaturvimsamsa"),
    "D27": (d27, "bhamsa"),
    "D30": (d30, "trimsamsa"),
    "D40": (d40, "khavedamsa"),
    "D45": (d45, "akshavedamsa"),
    "D60": (d60, "shashtiamsa"),
}


def varga_sign(code: str, lon: float) -> int:
    try:
        return VARGAS[code][0](lon)
    except KeyError as exc:
        raise ValueError(f"unknown divisional chart {code}") from exc

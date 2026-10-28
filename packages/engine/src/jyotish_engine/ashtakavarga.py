"""Ashtakavarga (BPHS ch. 66-67): Bhinna (BAV) and Sarva (SAV) tables.

BENEFIC_PLACES[planet][contributor] lists the houses, counted from the
contributor's sign, where `planet` receives a benefic point (bindu).
Totals per planet: Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56,
Venus 52, Saturn 39; Sarva total 337.
"""

from typing import Any

from jyotish_engine.constants import SEVEN_GRAHAS, Graha
from jyotish_engine.core import sign_key

S, MO, MA, ME, J, V, SA = SEVEN_GRAHAS
L = "lagna"

BENEFIC_PLACES: dict[Graha, dict[Graha | str, tuple[int, ...]]] = {
    S: {S: (1, 2, 4, 7, 8, 9, 10, 11), MO: (3, 6, 10, 11), MA: (1, 2, 4, 7, 8, 9, 10, 11),
        ME: (3, 5, 6, 9, 10, 11, 12), J: (5, 6, 9, 11), V: (6, 7, 12),
        SA: (1, 2, 4, 7, 8, 9, 10, 11), L: (3, 4, 6, 10, 11, 12)},
    MO: {S: (3, 6, 7, 8, 10, 11), MO: (1, 3, 6, 7, 10, 11), MA: (2, 3, 5, 6, 9, 10, 11),
         ME: (1, 3, 4, 5, 7, 8, 10, 11), J: (1, 4, 7, 8, 10, 11, 12), V: (3, 4, 5, 7, 9, 10, 11),
         SA: (3, 5, 6, 11), L: (3, 6, 10, 11)},
    MA: {S: (3, 5, 6, 10, 11), MO: (3, 6, 11), MA: (1, 2, 4, 7, 8, 10, 11), ME: (3, 5, 6, 11),
         J: (6, 10, 11, 12), V: (6, 8, 11, 12), SA: (1, 4, 7, 8, 9, 10, 11), L: (1, 3, 6, 10, 11)},
    ME: {S: (5, 6, 9, 11, 12), MO: (2, 4, 6, 8, 10, 11), MA: (1, 2, 4, 7, 8, 9, 10, 11),
         ME: (1, 3, 5, 6, 9, 10, 11, 12), J: (6, 8, 11, 12), V: (1, 2, 3, 4, 5, 8, 9, 11),
         SA: (1, 2, 4, 7, 8, 9, 10, 11), L: (1, 2, 4, 6, 8, 10, 11)},
    J: {S: (1, 2, 3, 4, 7, 8, 9, 10, 11), MO: (2, 5, 7, 9, 11), MA: (1, 2, 4, 7, 8, 10, 11),
        ME: (1, 2, 4, 5, 6, 9, 10, 11), J: (1, 2, 3, 4, 7, 8, 10, 11), V: (2, 5, 6, 9, 10, 11),
        SA: (3, 5, 6, 12), L: (1, 2, 4, 5, 6, 7, 9, 10, 11)},
    V: {S: (8, 11, 12), MO: (1, 2, 3, 4, 5, 8, 9, 11, 12), MA: (3, 5, 6, 9, 11, 12),
        ME: (3, 5, 6, 9, 11), J: (5, 8, 9, 10, 11), V: (1, 2, 3, 4, 5, 8, 9, 10, 11),
        SA: (3, 4, 5, 8, 9, 10, 11), L: (1, 2, 3, 4, 5, 8, 9, 11)},
    SA: {S: (1, 2, 4, 7, 8, 10, 11), MO: (3, 6, 11), MA: (3, 5, 6, 10, 11, 12),
         ME: (6, 8, 9, 10, 11, 12), J: (5, 6, 11, 12), V: (6, 11, 12), SA: (3, 5, 6, 11),
         L: (1, 3, 4, 6, 10, 11)},
}  # fmt: skip

EXPECTED_TOTALS = {S: 48, MO: 49, MA: 39, ME: 54, J: 56, V: 52, SA: 39}


def ashtakavarga(signs: dict[Graha, int], lagna_sign: int) -> dict[str, Any]:
    """signs: sidereal sign index (0..11) of each of the seven grahas."""
    bav: dict[str, list[int]] = {}
    for planet, table in BENEFIC_PLACES.items():
        row = [0] * 12
        for contributor, places in table.items():
            ref = lagna_sign if contributor == L else signs[contributor]  # type: ignore[index]
            for h in places:
                row[(ref + h - 1) % 12] += 1
        bav[str(planet)] = row
    sav = [sum(bav[str(p)][i] for p in BENEFIC_PLACES) for i in range(12)]
    return {
        "signs": [sign_key(i) for i in range(12)],
        "bhinna": bav,
        "sarva": sav,
        "sarva_total": sum(sav),
        "sarva_by_house": [sav[(lagna_sign + h) % 12] for h in range(12)],
    }

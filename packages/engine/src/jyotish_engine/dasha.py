"""Vimshottari Dasha (BPHS ch. 46): Maha, Antar and Pratyantar periods."""

from dataclasses import dataclass, field

from jyotish_engine.constants import VIMSHOTTARI_ORDER, VIMSHOTTARI_YEARS, Graha
from jyotish_engine.core import nakshatra_of
from jyotish_engine.timeutil import jd_to_utc

TOTAL_YEARS = 120


@dataclass
class Period:
    lord: Graha
    level: int  # 1 maha, 2 antar, 3 pratyantar
    start_jd: float
    end_jd: float
    children: list["Period"] = field(default_factory=list)

    def to_dict(self, depth: int) -> dict[str, object]:
        d: dict[str, object] = {
            "lord": str(self.lord),
            "start": jd_to_utc(self.start_jd).isoformat(),
            "end": jd_to_utc(self.end_jd).isoformat(),
            "start_jd": round(self.start_jd, 6),
            "end_jd": round(self.end_jd, 6),
        }
        if depth > self.level and self.children:
            d["periods"] = [c.to_dict(depth) for c in self.children]
        return d


def _sequence_from(lord: Graha) -> list[Graha]:
    i = VIMSHOTTARI_ORDER.index(lord)
    return [VIMSHOTTARI_ORDER[(i + k) % 9] for k in range(9)]


def _subdivide(parent: Period, max_level: int) -> None:
    if parent.level >= max_level:
        return
    span = parent.end_jd - parent.start_jd
    t = parent.start_jd
    for lord in _sequence_from(parent.lord):
        length = span * VIMSHOTTARI_YEARS[lord] / TOTAL_YEARS
        child = Period(lord, parent.level + 1, t, t + length)
        _subdivide(child, max_level)
        parent.children.append(child)
        t += length
    parent.children[-1].end_jd = parent.end_jd  # remove float drift


@dataclass(frozen=True)
class DashaResult:
    moon_nakshatra: str
    first_lord: Graha
    balance_years: float  # remaining years of the first Mahadasha at birth
    year_days: float
    mahadashas: list[Period]

    def current(self, jd: float) -> list[Period]:
        """The chain [maha, antar, pratyantar] running at jd (empty if none)."""
        chain: list[Period] = []
        level = self.mahadashas
        while level:
            hit = next((p for p in level if p.start_jd <= jd < p.end_jd), None)
            if hit is None:
                break
            chain.append(hit)
            level = hit.children
        return chain

    def to_dict(self, depth: int = 3) -> dict[str, object]:
        return {
            "system": "vimshottari",
            "moon_nakshatra": self.moon_nakshatra,
            "first_lord": str(self.first_lord),
            "balance_years": round(self.balance_years, 6),
            "year_days": self.year_days,
            "mahadashas": [m.to_dict(depth) for m in self.mahadashas],
        }


def vimshottari(moon_lon: float, birth_jd: float, year_days: float = 365.25, levels: int = 3) -> DashaResult:
    nak = nakshatra_of(moon_lon)
    first = nak.lord
    first_years = VIMSHOTTARI_YEARS[first]
    elapsed_years = nak.fraction_elapsed * first_years
    balance = first_years - elapsed_years
    # The first Mahadasha conceptually started before birth.
    t = birth_jd - elapsed_years * year_days
    mahas: list[Period] = []
    for lord in _sequence_from(first):
        length = VIMSHOTTARI_YEARS[lord] * year_days
        p = Period(lord, 1, t, t + length)
        _subdivide(p, levels)
        mahas.append(p)
        t += length
    return DashaResult(nak.key, first, balance, year_days, mahas)

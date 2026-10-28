"""Thin, thread-safe wrapper around Swiss Ephemeris.

Swiss Ephemeris keeps global state (ephemeris path, sidereal mode), so every
call goes through one lock. The ephemeris files shipped in `ephe/` cover
1800-2400 CE; outside that range Swiss Ephemeris falls back to the Moshier
model (about 1 arcsecond), and the result's meta block says so.
"""

import threading
from dataclasses import dataclass
from pathlib import Path

import swisseph as swe

from jyotish_engine.constants import SWE_IDS, Graha
from jyotish_engine.settings import AYANAMSA_SWE, Ayanamsa, NodeType

EPHE_PATH = Path(__file__).parent / "ephe"
_lock = threading.RLock()
_initialised = False

BASE_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


def _init() -> None:
    global _initialised
    if not _initialised:
        swe.set_ephe_path(str(EPHE_PATH))
        _initialised = True


@dataclass(frozen=True, slots=True)
class BodyPosition:
    longitude: float  # degrees 0..360 (sidereal unless stated)
    latitude: float
    distance_au: float
    speed: float  # degrees per day in longitude
    retrograde: bool
    source: str  # "swiss_ephemeris" or "moshier"


def _flags_source(retflags: int) -> str:
    return "swiss_ephemeris" if retflags & swe.FLG_SWIEPH else "moshier"


def ayanamsa(jd_ut: float, which: Ayanamsa) -> float:
    """Ayanamsa in degrees (true, i.e. including nutation) at a UT moment."""
    with _lock:
        _init()
        swe.set_sid_mode(AYANAMSA_SWE[which], 0, 0)
        _, value = swe.get_ayanamsa_ex_ut(jd_ut, swe.FLG_SWIEPH)
        return float(value)


def body(jd_ut: float, graha: Graha, which: Ayanamsa, node: NodeType = NodeType.MEAN, *, sidereal: bool = True) -> BodyPosition:
    with _lock:
        _init()
        flags = BASE_FLAGS
        if sidereal:
            swe.set_sid_mode(AYANAMSA_SWE[which], 0, 0)
            flags |= swe.FLG_SIDEREAL
        if graha in (Graha.RAHU, Graha.KETU):
            pid = swe.MEAN_NODE if node is NodeType.MEAN else swe.TRUE_NODE
        else:
            pid = SWE_IDS[graha]
        xx, ret = swe.calc_ut(jd_ut, pid, flags)
    lon, lat, dist, speed = float(xx[0]), float(xx[1]), float(xx[2]), float(xx[3])
    if graha is Graha.KETU:
        lon = (lon + 180.0) % 360.0
        lat = -lat
    return BodyPosition(
        longitude=lon % 360.0,
        latitude=lat,
        distance_au=dist,
        speed=speed,
        retrograde=speed < 0,
        source=_flags_source(ret),
    )


def tropical_longitude(jd_ut: float, graha: Graha) -> float:
    return body(jd_ut, graha, Ayanamsa.LAHIRI, sidereal=False).longitude


@dataclass(frozen=True, slots=True)
class HouseData:
    ascendant: float  # sidereal
    mc: float  # sidereal
    cusps: tuple[float, ...]  # 12 sidereal cusps for the requested system
    armc: float


def houses(jd_ut: float, lat: float, lon: float, which: Ayanamsa, system: bytes = b"W") -> HouseData:
    with _lock:
        _init()
        swe.set_sid_mode(AYANAMSA_SWE[which], 0, 0)
        cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, system, swe.FLG_SIDEREAL)
    return HouseData(
        ascendant=float(ascmc[0]) % 360.0,
        mc=float(ascmc[1]) % 360.0,
        cusps=tuple(float(c) % 360.0 for c in cusps[:12]),
        armc=float(ascmc[2]),
    )


def sidereal_longitude_of(jd_ut: float, graha: Graha, which: Ayanamsa, node: NodeType = NodeType.MEAN) -> float:
    return body(jd_ut, graha, which, node).longitude


def rise_set(jd_ut_start: float, graha: Graha, lat: float, lon: float, alt: float = 0.0, *, rise: bool = True) -> float | None:
    """Next rise (or set) after jd_ut_start, Hindu definition: disc centre,
    no refraction is the classical rule but most panchangs use the upper limb
    with refraction. We use the upper limb with refraction (matches published
    Indian panchangs such as Rashtriya Panchang within a minute)."""
    with _lock:
        _init()
        rsmi = swe.CALC_RISE if rise else swe.CALC_SET
        try:
            res, tret = swe.rise_trans(jd_ut_start, SWE_IDS[graha], rsmi, (lon, lat, alt), 1013.25, 15.0, swe.FLG_SWIEPH)
        except swe.Error:
            return None
    if res != 0:
        return None
    return float(tret[0])


def swe_version() -> str:
    return str(swe.version)


def declination(jd_ut: float, graha: Graha) -> float:
    """Apparent declination in degrees (equatorial, of date)."""
    with _lock:
        _init()
        xx, _ = swe.calc_ut(jd_ut, SWE_IDS[graha], swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)
    return float(xx[1])

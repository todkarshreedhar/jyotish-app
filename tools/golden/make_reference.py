"""Build the golden reference values from an INDEPENDENT source.

Planet positions come from NASA JPL's DE421 ephemeris through Skyfield (not
from Swiss Ephemeris). The ascendant comes from Skyfield's sidereal time and
the classical formula. The mean lunar node comes from Meeus' polynomial.
Nakshatra, pada and Dasha dates are recomputed here with plain arithmetic.

Two conventions are shared with the engine on purpose, because they are
definitions, not measurements:
  * the Lahiri ayanamsa value (checked separately against its official
    definition, 23°15'00.658" on 21 March 1956), and
  * Delta T (TT - UT), so both sides look at the same physical instant.

Run:  uv run python tools/golden/make_reference.py
The output is packages/engine/tests/golden/golden_charts.json. A domain
expert should also check each chart in Jagannatha Hora and fill in
`expert_check` before gate M1 is signed off.
"""

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import swisseph as swe
from skyfield.api import Loader, load_file
from skyfield.framelib import ecliptic_frame
from skyfield_data import get_skyfield_data_path

HERE = Path(__file__).parent
OUT = HERE.parent.parent / "packages/engine/tests/golden/golden_charts.json"
EPHE = HERE.parent.parent / "packages/engine/src/jyotish_engine/ephe"

load = Loader(get_skyfield_data_path(), verbose=False)
ts = load.timescale(builtin=True)
eph = load_file(str(Path(get_skyfield_data_path()) / "de421.bsp"))
earth = eph["earth"]
BODIES = {
    "sun": eph["sun"],
    "moon": eph["moon"],
    "mars": eph["mars barycenter"],
    "mercury": eph["mercury barycenter"],
    "jupiter": eph["jupiter barycenter"],
    "venus": eph["venus barycenter"],
    "saturn": eph["saturn barycenter"],
}
NAK = 360 / 27
LORDS = ["ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"]
YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]
SIGNS = [
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
]

swe.set_ephe_path(str(EPHE))


def tropical(name: str, jd_ut: float) -> tuple[float, float]:
    t = ts.tt_jd(jd_ut + swe.deltat(jd_ut))
    lat, lon, _ = earth.at(t).observe(BODIES[name]).apparent().frame_latlon(ecliptic_frame)
    # speed by central difference over +-30 minutes
    dt = 1 / 48
    t1, t2 = ts.tt_jd(t.tt - dt), ts.tt_jd(t.tt + dt)
    l1 = earth.at(t1).observe(BODIES[name]).apparent().frame_latlon(ecliptic_frame)[1].degrees
    l2 = earth.at(t2).observe(BODIES[name]).apparent().frame_latlon(ecliptic_frame)[1].degrees
    speed = ((l2 - l1 + 540) % 360 - 180) / (2 * dt)
    return float(lon.degrees % 360), float(speed)


def mean_node_tropical(jd_ut: float) -> float:
    jd_tt = jd_ut + swe.deltat(jd_ut)
    T = (jd_tt - 2451545.0) / 36525
    omega = 125.0445479 - 1934.1362891 * T + 0.0020754 * T**2 + T**3 / 467441 - T**4 / 60616000
    # apparent: add nutation in longitude (IAU 1980 main terms are enough at 0.5")
    t = ts.tt_jd(jd_tt)
    from skyfield.nutationlib import iau2000b_radians

    dpsi, _ = iau2000b_radians(t)
    return float((omega + math.degrees(dpsi)) % 360)


def ascendant_tropical(jd_ut: float, lat: float, lon: float) -> float:
    # Sidereal time depends on the Earth's rotation angle, i.e. on UT1 itself.
    t = ts.ut1_jd(jd_ut)
    from skyfield.earthlib import sidereal_time  # noqa: F401 (documented dependency)
    from skyfield.nutationlib import iau2000b_radians

    gast_h = t.gast
    dpsi, deps = iau2000b_radians(t)
    eps = t._mean_obliquity_radians + deps
    ramc = math.radians((gast_h * 15 + lon) % 360)
    phi = math.radians(lat)
    asc = math.atan2(math.cos(ramc), -(math.sin(ramc) * math.cos(eps) + math.tan(phi) * math.sin(eps)))
    return float(math.degrees(asc) % 360)


def lahiri(jd_ut: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    return swe.get_ayanamsa_ex_ut(jd_ut, swe.FLG_SWIEPH)[1]


def nak_info(lon: float) -> dict:
    i = int(lon // NAK)
    within = lon - i * NAK
    return {"nakshatra_index": i, "pada": int(within // (NAK / 4)) + 1, "lord": LORDS[i % 9], "fraction": within / NAK}


def julian_day(dt: datetime) -> float:
    # Independent of Swiss Ephemeris: Unix epoch is JD 2440587.5
    return dt.timestamp() / 86400.0 + 2440587.5


def main() -> None:
    inputs = json.loads((HERE / "inputs.json").read_text())
    out = []
    for c in inputs:
        local = datetime.fromisoformat(f"{c['date']}T{c['time']}").replace(tzinfo=ZoneInfo(c["tz"]))
        utc = local.astimezone(UTC)
        jd = julian_day(utc)
        ayan = lahiri(jd)
        planets = {}
        for name in BODIES:
            lon, speed = tropical(name, jd)
            sid = (lon - ayan) % 360
            planets[name] = {
                "longitude": round(sid, 7),
                "retrograde": bool(speed < 0),
                "sign": SIGNS[int(sid // 30)],
                **{k: v for k, v in nak_info(sid).items() if k != "fraction"},
            }
        rahu = (mean_node_tropical(jd) - ayan) % 360
        ketu = (rahu + 180) % 360
        for name, val in (("rahu", rahu), ("ketu", ketu)):
            planets[name] = {
                "longitude": round(val, 7),
                "retrograde": True,
                "sign": SIGNS[int(val // 30)],
                **{k: v for k, v in nak_info(val).items() if k != "fraction"},
            }
        asc = (ascendant_tropical(jd, c["lat"], c["lon"]) - ayan) % 360

        # Navamsa signs by plain arithmetic: each 3°20' from Aries is one sign.
        d9 = {n: int(p["longitude"] // (10 / 3)) % 12 for n, p in planets.items()}

        # Vimshottari Mahadasha starts
        moon = planets["moon"]["longitude"]
        ni = nak_info(moon)
        k = LORDS.index(ni["lord"])
        start = jd - ni["fraction"] * YEARS[k] * 365.25
        mahas = []
        for j in range(9):
            lord = LORDS[(k + j) % 9]
            mahas.append({"lord": lord, "start_jd": round(start, 6)})
            start += YEARS[(k + j) % 9] * 365.25

        out.append(
            {
                **c,
                "expected": {
                    "julian_day_ut": round(jd, 8),
                    "utc": utc.isoformat(),
                    "utc_offset_minutes": int(local.utcoffset().total_seconds() // 60),
                    "ayanamsa": round(ayan, 7),
                    "lagna": {"longitude": round(asc, 7), "sign": SIGNS[int(asc // 30)]},
                    "planets": planets,
                    "navamsa_sign_index": d9,
                    "navamsa_lagna_index": int(asc // (10 / 3)) % 12,
                    "mahadashas": mahas,
                },
                "source": "Skyfield 1.x + JPL DE421; Meeus mean node; classical ascendant formula",
                "expert_check": {"jagannatha_hora": None, "signed_off_by": None},
            }
        )
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} charts to {OUT}")


if __name__ == "__main__":
    main()

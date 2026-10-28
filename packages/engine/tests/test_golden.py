"""Gate M1 / M3: the engine must match 20 independent reference charts.

Reference values come from NASA JPL DE421 via Skyfield (see
tools/golden/make_reference.py), not from Swiss Ephemeris itself.
A failure names the chart and the field.
"""

import json
from datetime import date, time
from pathlib import Path

import pytest
from jyotish_engine.chart import BirthData, compute_chart
from jyotish_engine.core import angular_distance

GOLDEN = json.loads((Path(__file__).parent / "golden" / "golden_charts.json").read_text())
ARCSEC = 1 / 3600

# Tolerances from the backlog (US-19, US-20, US-22, US-39)
JD_TOL = 1e-6  # 6 decimal places
PLANET_TOL = 1.0 * ARCSEC  # within 1 arcsecond
NODE_TOL = 1.0 * ARCSEC
LAGNA_TOL = 1.0 * ARCSEC  # backlog asks for 1 arcminute; we hold 1 arcsecond
DASHA_TOL_DAYS = 1.0


def _chart(c: dict) -> dict:
    birth = BirthData(
        birth_date=date.fromisoformat(c["date"]),
        birth_time=time.fromisoformat(c["time"]),
        latitude=c["lat"],
        longitude=c["lon"],
        tz_name=c["tz"],
    )
    return compute_chart(birth, vargas=("D1", "D9"))


@pytest.fixture(scope="module", params=GOLDEN, ids=[c["id"] for c in GOLDEN])
def pair(request: pytest.FixtureRequest) -> tuple[dict, dict]:
    return request.param, _chart(request.param)


def test_julian_day(pair: tuple[dict, dict]) -> None:
    ref, got = pair
    assert abs(got["input"]["julian_day_ut"] - ref["expected"]["julian_day_ut"]) < JD_TOL, ref["id"]
    assert got["input"]["utc_offset_minutes"] == ref["expected"]["utc_offset_minutes"], ref["id"]


def test_planet_longitudes(pair: tuple[dict, dict]) -> None:
    ref, got = pair
    for p in got["planets"]:
        exp = ref["expected"]["planets"][p["id"]]
        tol = NODE_TOL if p["id"] in ("rahu", "ketu") else PLANET_TOL
        diff = angular_distance(p["longitude"], exp["longitude"])
        assert diff < tol, f'{ref["id"]} {p["id"]} longitude off by {diff * 3600:.3f}"'
        assert p["retrograde"] == exp["retrograde"], f"{ref['id']} {p['id']} retrograde flag"
        assert p["sign"] == exp["sign"], f"{ref['id']} {p['id']} sign"
        assert p["nakshatra_index"] == exp["nakshatra_index"], f"{ref['id']} {p['id']} nakshatra"
        assert p["pada"] == exp["pada"], f"{ref['id']} {p['id']} pada"


def test_ketu_opposite_rahu(pair: tuple[dict, dict]) -> None:
    _, got = pair
    by = {p["id"]: p for p in got["planets"]}
    assert abs(((by["ketu"]["longitude"] - by["rahu"]["longitude"]) % 360) - 180) < 1e-6


def test_lagna(pair: tuple[dict, dict]) -> None:
    ref, got = pair
    diff = angular_distance(got["lagna"]["longitude"], ref["expected"]["lagna"]["longitude"])
    assert diff < LAGNA_TOL, f'{ref["id"]} lagna off by {diff * 3600:.2f}"'
    assert got["lagna"]["sign"] == ref["expected"]["lagna"]["sign"], ref["id"]
    assert got["houses"][0]["sign"] == got["lagna"]["sign"]


def test_navamsa(pair: tuple[dict, dict]) -> None:
    ref, got = pair
    d9 = got["vargas"]["D9"]
    assert d9["lagna_sign_index"] == ref["expected"]["navamsa_lagna_index"], ref["id"]
    for pid, exp in ref["expected"]["navamsa_sign_index"].items():
        assert d9["planets"][pid]["sign_index"] == exp, f"{ref['id']} {pid} navamsa"


def test_mahadasha_dates(pair: tuple[dict, dict]) -> None:
    ref, got = pair
    for m, exp in zip(got["dasha"]["mahadashas"], ref["expected"]["mahadashas"], strict=True):
        assert m["lord"] == exp["lord"], ref["id"]
        assert abs(m["start_jd"] - exp["start_jd"]) < DASHA_TOL_DAYS, f"{ref['id']} {m['lord']} start"


def test_deterministic_output() -> None:
    c = GOLDEN[0]
    a = json.dumps(_chart(c), sort_keys=True)
    b = json.dumps(_chart(c), sort_keys=True)
    assert a == b

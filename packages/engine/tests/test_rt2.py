"""Release 2 engine parts: Panchang, Ashtakavarga, matching, Sade Sati."""

from datetime import UTC, date, datetime, time
from pathlib import Path

import pytest

from jyotish_engine.ashtakavarga import BENEFIC_PLACES, EXPECTED_TOTALS, ashtakavarga
from jyotish_engine.chart import BirthData, compute_chart
from jyotish_engine.constants import SEVEN_GRAHAS, Graha
from jyotish_engine.matching import ashtakoota, manglik
from jyotish_engine.panchang import find_change, panchang, tithi_index
from jyotish_engine.settings import ChartSettings
from jyotish_engine.timeutil import julian_day_ut, jd_to_utc
from jyotish_engine.transits import sade_sati, sign_ingresses


def test_ashtakavarga_table_totals() -> None:
    for planet, table in BENEFIC_PLACES.items():
        assert sum(len(v) for v in table.values()) == EXPECTED_TOTALS[planet], planet


@pytest.mark.parametrize("year", [1950, 1977, 1990, 2005, 2021])
def test_sarva_total_is_337(year: int) -> None:
    c = compute_chart(BirthData(date(year, 6, 1), time(6, 0), 19.07, 72.88, "Asia/Kolkata"), vargas=("D1",))
    signs = {Graha(p["id"]): p["sign_index"] for p in c["planets"] if Graha(p["id"]) in SEVEN_GRAHAS}
    av = ashtakavarga(signs, c["lagna"]["sign_index"])
    assert av["sarva_total"] == 337
    assert sum(av["bhinna"]["sun"]) == 48


def _skyfield_phases(year: int) -> list[tuple[datetime, int]]:
    from skyfield import almanac
    from skyfield.api import Loader
    from skyfield_data import get_skyfield_data_path

    load = Loader(get_skyfield_data_path(), verbose=False)
    ts = load.timescale(builtin=True)
    eph = load("de421.bsp")
    t, y = almanac.find_discrete(ts.utc(year, 1, 1), ts.utc(year, 12, 31), almanac.moon_phases(eph))
    return [(ti.utc_datetime(), int(yi)) for ti, yi in zip(t, y, strict=True) if yi in (0, 2)]


def test_tithi_boundaries_match_jpl_new_and_full_moons() -> None:
    """Purnima ends at full moon and Amavasya at new moon (JPL DE421)."""
    phases = _skyfield_phases(2024)
    assert len(phases) >= 24
    for when, phase in phases[:10]:
        jd = julian_day_ut(when)
        start = jd - 0.5
        expected_from = 14 if phase == 2 else 29
        assert tithi_index(start) == expected_from
        found = find_change(tithi_index, start, max_days=1.0)
        assert found is not None
        assert abs(found - jd) * 1440 < 1.0, f"{when}: {jd_to_utc(found)}"


def test_panchang_purnima_2024_04_23_delhi() -> None:
    p = panchang(date(2024, 4, 23), "Asia/Kolkata", 28.6139, 77.2090)
    assert p["vara"]["name"] == "tuesday"
    assert p["tithi"][0]["name"] == {"paksha": "shukla", "name": "purnima"}
    assert p["sunrise"].startswith("2024-04-23T00:1")  # about 05:47 IST


def test_saturn_enters_pisces_march_2025() -> None:
    s = ChartSettings()
    ing = sign_ingresses(Graha.SATURN, julian_day_ut(datetime(2025, 1, 1, tzinfo=UTC)), julian_day_ut(datetime(2025, 12, 31, tzinfo=UTC)), s)
    assert ing and ing[0].to_sign == 11
    assert jd_to_utc(ing[0].jd).date() == date(2025, 3, 29)


def test_sade_sati_for_sagittarius_moon() -> None:
    # Sagittarius Moon: Saturn entered Scorpio (12th) in Nov 2014 and left
    # Capricorn (2nd) in Jan 2023.
    r = sade_sati(8, julian_day_ut(datetime(2000, 1, 1, tzinfo=UTC)), ChartSettings(), years=30)
    first = r["cycles"][0]
    assert first["start"].startswith("2014-11")
    assert first["end"].startswith("2023-01")
    assert [p["phase"] for p in first["phases"]] == ["rising", "peak", "setting"]


def test_ashtakoota_same_nakshatra() -> None:
    r = ashtakoota(10.0, 10.0)
    assert r["max"] == 36
    nadi = next(k for k in r["kootas"] if k["koota"] == "nadi")
    assert nadi["points"] == 0  # same nadi
    assert r["doshas"]["nadi"]
    assert 0 <= r["total"] <= 36


def test_ashtakoota_points_never_exceed_max() -> None:
    for a in range(0, 360, 7):
        for b in range(0, 360, 11):
            r = ashtakoota(a + 0.5, b + 0.5)
            for k in r["kootas"]:
                assert 0 <= k["points"] <= k["max"]


def test_manglik() -> None:
    assert manglik(mars_sign=6, lagna_sign=0, moon_sign=3, venus_sign=3)["is_manglik"]  # Mars 7th from Lagna
    assert not manglik(mars_sign=2, lagna_sign=0, moon_sign=0, venus_sign=0)["is_manglik"]  # 3rd

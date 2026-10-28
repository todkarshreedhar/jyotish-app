from datetime import date, time

import pytest
from jyotish_engine import ephemeris
from jyotish_engine.constants import Graha
from jyotish_engine.core import dignity, dms, is_combust, nakshatra_of
from jyotish_engine.dasha import vimshottari
from jyotish_engine.settings import Ayanamsa, ChartSettings
from jyotish_engine.timeutil import InputError, to_moment
from jyotish_engine.vargas import VARGAS, varga_sign


def test_us24_moon_at_13_20_is_bharani_pada_1() -> None:
    n = nakshatra_of(13 + 20 / 60)
    assert (n.key, n.pada) == ("bharani", 1)


@pytest.mark.parametrize(
    ("lon", "key", "pada"),
    [(0.0, "ashwini", 1), (3.3333334, "ashwini", 2), (359.99, "revati", 4), (120.0, "magha", 1), (266.67, "uttara_ashadha", 1)],
)
def test_nakshatra_boundaries(lon: float, key: str, pada: int) -> None:
    n = nakshatra_of(lon)
    assert (n.key, n.pada) == (key, pada)


def test_lahiri_matches_official_definition() -> None:
    # Indian Astronomical Ephemeris: 23°15'00.658" on 21 March 1956, 0h ET (true).
    jd_et = 2435553.5
    value = ephemeris.ayanamsa(jd_et, Ayanamsa.LAHIRI)
    assert abs(value - (23 + 15 / 60 + 0.658 / 3600)) * 3600 < 1.0


def test_raman_differs_from_lahiri() -> None:
    jd = 2451545.0
    diff = ephemeris.ayanamsa(jd, Ayanamsa.LAHIRI) - ephemeris.ayanamsa(jd, Ayanamsa.RAMAN)
    assert 1.3 < diff < 1.5  # about 1°26'


def test_us15_pune_1950_offset() -> None:
    m = to_moment(date(1950, 3, 10), time(10, 30), "Asia/Kolkata")
    assert m.utc_offset_minutes == 330


def test_us15_kolkata_war_time_1943() -> None:
    m = to_moment(date(1943, 3, 10), time(6, 10), "Asia/Kolkata")
    assert m.utc_offset_minutes == 390  # UTC+06:30


def test_nonexistent_local_time_raises() -> None:
    with pytest.raises(InputError):
        to_moment(date(2021, 3, 14), time(2, 30), "America/New_York")


def test_unknown_zone_raises() -> None:
    with pytest.raises(InputError):
        to_moment(date(2000, 1, 1), time(0, 0), "Mars/Olympus")


def test_fixed_offset() -> None:
    m = to_moment(date(2000, 1, 1), time(5, 30), None, 330)
    assert m.utc.hour == 0 and m.jd_ut == pytest.approx(2451544.5)


def test_dignities() -> None:
    assert dignity(Graha.SUN, 10.0) == "exalted"
    assert dignity(Graha.SUN, 190.0) == "debilitated"
    assert dignity(Graha.SUN, 125.0) == "moolatrikona"
    assert dignity(Graha.SUN, 145.0) == "own"
    assert dignity(Graha.MOON, 31.0) == "exalted"
    assert dignity(Graha.MOON, 40.0) == "moolatrikona"
    assert dignity(Graha.MERCURY, 160.0) == "exalted"
    assert dignity(Graha.MERCURY, 167.0) == "moolatrikona"
    assert dignity(Graha.MERCURY, 175.0) == "own"
    assert dignity(Graha.SATURN, 280.0) == "own"


def test_combustion() -> None:
    assert is_combust(Graha.MARS, 100.0, 110.0, False)
    assert not is_combust(Graha.MARS, 100.0, 120.0, False)
    assert is_combust(Graha.MERCURY, 100.0, 112.5, False)
    assert not is_combust(Graha.MERCURY, 100.0, 112.5, True)  # 12° orb when retrograde
    assert not is_combust(Graha.RAHU, 100.0, 100.0, False)


def test_dms() -> None:
    assert dms(13.3333333) == "13°20'00\""


def test_vimshottari_structure() -> None:
    d = vimshottari(13 + 20 / 60, 2451545.0)  # start of Bharani: full Venus dasha
    assert d.first_lord == Graha.VENUS
    assert d.balance_years == pytest.approx(20.0)
    total = d.mahadashas[-1].end_jd - d.mahadashas[0].start_jd
    assert total == pytest.approx(120 * 365.25)
    seq = [str(m.lord) for m in d.mahadashas]
    assert seq == ["venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury", "ketu"]
    venus = d.mahadashas[0]
    assert [str(a.lord) for a in venus.children][:2] == ["venus", "sun"]
    assert venus.children[0].end_jd - venus.children[0].start_jd == pytest.approx(20 * 20 / 120 * 365.25)
    assert venus.children[-1].end_jd == venus.end_jd
    assert len(venus.children[0].children) == 9


def test_dasha_year_length_changes_dates() -> None:
    a = vimshottari(100.0, 2451545.0, 365.25)
    b = vimshottari(100.0, 2451545.0, 365.2422)
    assert a.mahadashas[3].start_jd != b.mahadashas[3].start_jd


def test_settings_reject_bad_year() -> None:
    with pytest.raises(ValueError):
        ChartSettings(dasha_year_days=360)


# Divisional charts: hand-checked examples from BPHS rules.
@pytest.mark.parametrize(
    ("code", "lon", "expected"),
    [
        ("D9", 0.5, 0),  # Aries 0°30' -> Aries navamsa
        ("D9", 33.0, 9),  # Taurus 3° -> Capricorn
        ("D9", 95.0, 4),  # Cancer 5° -> Leo (Cancer, Leo)
        ("D2", 5.0, 4),  # odd sign first half -> Sun (Leo)
        ("D2", 35.0, 3),  # even sign first half -> Moon (Cancer)
        ("D3", 25.0, 8),  # Aries 25° -> 9th = Sagittarius
        ("D4", 40.0, 4),  # Taurus 10° -> 4th from Taurus = Leo
        ("D7", 35.0, 8),  # Taurus 5° (even): starts at 7th (Scorpio), part 2 -> Sagittarius
        ("D10", 31.0, 9),  # Taurus 1° (even) -> 9th from Taurus = Capricorn
        ("D12", 2.6, 1),  # Aries 2.6° -> Taurus
        ("D16", 31.0, 4),  # Taurus (fixed) -> starts Leo
        ("D20", 61.0, 4),  # Gemini (dual) -> starts Leo
        ("D24", 1.0, 4),  # Aries (odd) -> Leo
        ("D24", 31.0, 3),  # Taurus (even) -> Cancer
        ("D27", 30.5, 3),  # Taurus first part -> Cancer
        ("D30", 3.0, 0),  # odd 0-5 Mars -> Aries
        ("D30", 12.0, 8),  # odd 10-18 Jupiter -> Sagittarius
        ("D30", 33.0, 1),  # even 0-5 Venus -> Taurus
        ("D30", 58.0, 7),  # even 25-30 Mars -> Scorpio
        ("D40", 30.1, 6),  # even -> starts Libra
        ("D45", 120.1, 4),  # Leo (fixed) -> starts Leo
        ("D60", 0.6, 1),  # Aries 0.6° -> second part -> Taurus
    ],
)
def test_varga_examples(code: str, lon: float, expected: int) -> None:
    assert varga_sign(code, lon) == expected


def test_all_sixteen_vargas_defined() -> None:
    assert len(VARGAS) == 16
    for code in VARGAS:
        for lon in (0.0, 15.0, 29.999, 359.999):
            assert 0 <= varga_sign(code, lon) < 12


def test_ephemeris_files_used_in_every_thread():
    """Swiss Ephemeris settings are per thread; a new thread must not fall back to Moshier."""
    import threading

    from jyotish_engine import ephemeris
    from jyotish_engine.constants import Graha
    from jyotish_engine.settings import Ayanamsa

    ephemeris.body(2447907.0, Graha.SUN, Ayanamsa.LAHIRI)  # initialise the main thread first
    sources: list[str] = []
    t = threading.Thread(target=lambda: sources.append(ephemeris.body(2447907.0, Graha.MOON, Ayanamsa.LAHIRI).source))
    t.start()
    t.join()
    assert sources == ["swiss_ephemeris"]

from jyotish_engine import ENGINE_VERSION, engine_info


def test_engine_info_reports_versions() -> None:
    info = engine_info()
    assert info["engine_version"] == ENGINE_VERSION
    assert info["swiss_ephemeris_version"]  # not empty

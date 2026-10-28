"""US-40 to US-42: rule loading, evaluation, and fire / no-fire coverage."""

from datetime import date, time, timedelta
from pathlib import Path

import pytest
from jyotish_engine.chart import BirthData, compute_chart
from jyotish_engine.rules import Facts, RuleError, evaluate, load_rules, run_rules, texts

RULES = load_rules()


def _sample_charts() -> list[dict]:
    """A fixed, varied set of charts: every 37 days and 5 hours from 1950."""
    out = []
    d = date(1950, 1, 1)
    for i in range(240):
        dt = d + timedelta(days=37 * i)
        out.append(compute_chart(BirthData(dt, time((5 * i) % 24, (7 * i) % 60), 18.52, 73.86, "Asia/Kolkata"), vargas=("D1",)))
    return out


SAMPLES = _sample_charts()


def test_at_least_forty_rules() -> None:
    assert len(RULES) >= 40


@pytest.mark.parametrize("rule", RULES, ids=[r.id for r in RULES])
def test_rule_fires_and_does_not_fire(rule) -> None:  # type: ignore[no-untyped-def]
    results = [evaluate(rule.when, Facts(c)) for c in SAMPLES]
    assert any(results), f"{rule.id} never fires on the sample charts"
    assert not all(results), f"{rule.id} fires on every sample chart"


@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
def test_every_rule_has_text(lang: str) -> None:
    t = texts(lang)
    for r in RULES:
        assert r.text_key in t, f"{lang} missing {r.text_key}"
        assert t[r.text_key]["title"] and t[r.text_key]["text"]


def test_run_rules_records_version_and_ids() -> None:
    out = run_rules(SAMPLES[0], RULES)
    assert out["ruleset_version"]
    assert all("id" in r and "source" in r for r in out["results"])


def _write(tmp: Path, body: str) -> Path:
    (tmp / "bad.yaml").write_text(body)
    return tmp


def test_missing_field_reports_file_and_line(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "- id: A\n  topic: career\n  kind: yoga\n  source: x\n  when: {retrograde: mars}\n  text_key: A\n\n- id: B\n  topic: career\n",
    )
    with pytest.raises(RuleError, match=r"bad.yaml:8: rule B is missing"):
        load_rules(tmp_path)


def test_bad_condition_reports_file_and_line(tmp_path: Path) -> None:
    _write(tmp_path, "- id: A\n  topic: career\n  kind: yoga\n  source: x\n  when: {explode: mars}\n  text_key: A\n")
    with pytest.raises(RuleError, match=r"bad.yaml:1: unknown condition 'explode'"):
        load_rules(tmp_path)


def test_gajakesari_by_construction() -> None:
    # Build a minimal fake chart: Moon in Aries, Jupiter in Cancer (4th from Moon).
    planets = []
    signs = {"sun": 5, "moon": 0, "mars": 6, "mercury": 5, "jupiter": 3, "venus": 7, "saturn": 8, "rahu": 2, "ketu": 8}
    for pid, s in signs.items():
        planets.append(
            {"id": pid, "sign_index": s, "longitude": s * 30 + 10.0, "dignity": "neutral", "retrograde": False, "combust": False}
        )
    chart = {"lagna": {"sign_index": 0}, "planets": planets}
    rule = next(r for r in RULES if r.id == "Y-GAJAKESARI")
    assert evaluate(rule.when, Facts(chart))
    planets[4]["sign_index"] = 1  # Jupiter to Taurus: 2nd from Moon
    assert not evaluate(rule.when, Facts(chart))

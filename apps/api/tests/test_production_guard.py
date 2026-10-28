"""The API refuses to start in production with unsafe settings."""

import pytest
from jyotish_api import crypto
from jyotish_api.settings import settings

STRONG = {"secret_key": "x" * 64, "data_encryption_keys": "aGVsbG8taGVsbG8taGVsbG8taGVsbG8taGVsbG8tMTI="}


@pytest.fixture
def production(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    monkeypatch.setattr(settings, "environment", "production")
    for k, v in STRONG.items():
        monkeypatch.setattr(settings, k, v)
    return monkeypatch


def test_strong_settings_pass(production: pytest.MonkeyPatch) -> None:
    crypto.check_production_secrets()


def test_dev_secret_key_is_refused(production: pytest.MonkeyPatch) -> None:
    production.setattr(settings, "secret_key", "dev-only-secret-change-me-dev-only-secret-change-me")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        crypto.check_production_secrets()


def test_ip_rate_limits_cannot_be_turned_off(production: pytest.MonkeyPatch) -> None:
    production.setattr(settings, "ip_rate_limits", False)
    with pytest.raises(RuntimeError, match="IP_RATE_LIMITS"):
        crypto.check_production_secrets()


def test_charts_skip_ip_limit_only_when_turned_off(client, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
    body = {
        "birth": {
            "birth_date": "1990-01-15",
            "birth_time": "10:30",
            "latitude": 18.52,
            "longitude": 73.85,
            "tz_name": "Asia/Kolkata",
        }
    }
    monkeypatch.setattr(settings, "ip_rate_limits", False)
    codes = {client.post("/v1/charts", json=body, headers={"X-CSRF": "1"}).status_code for _ in range(65)}
    assert codes == {200}

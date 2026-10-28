"""API tests run against a real PostgreSQL database (TEST_DATABASE_URL).

Locally: `docker compose up -d db redis`, then `uv run pytest`. CI starts
Postgres as a service. Tests that need the database are skipped if it is not
reachable, so the pure unit tests still run anywhere.
"""

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("TEST_DATABASE_URL", "postgresql+psycopg://jyotish:jyotish@localhost:5432/jyotish_test")
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

import re  # noqa: E402
from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from jyotish_api import emailer  # noqa: E402
from jyotish_api.db import database_is_up, engine  # noqa: E402
from sqlalchemy import text  # noqa: E402

API_DIR = Path(__file__).resolve().parent.parent
_migrated = False


def _migrate() -> None:
    global _migrated
    if _migrated:
        return
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "migrations"))
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    command.upgrade(cfg, "head")
    _migrated = True


TABLES = "api_usage, api_keys, alert_prefs, reports, audit_log, profiles, sessions, login_tokens, consents, users, places"


@pytest.fixture
def db_ready() -> Iterator[None]:
    if not database_is_up():
        pytest.skip("PostgreSQL is not reachable")
    _migrate()
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {TABLES} RESTART IDENTITY CASCADE"))
        conn.execute(
            text(
                "INSERT INTO places (id, name, ascii_name, name_deva, search, admin1, country_code, country, latitude, longitude, tz, population) VALUES "
                "(1259229, 'Pune', 'Pune', 'पुणे', '|pune|poona|पुणे|', 'Maharashtra', 'IN', 'India', 18.51957, 73.85535, 'Asia/Kolkata', 3124458),"
                "(1275339, 'Mumbai', 'Mumbai', 'मुंबई', '|mumbai|bombay|मुंबई|', 'Maharashtra', 'IN', 'India', 19.07283, 72.88261, 'Asia/Kolkata', 12691836),"
                "(1264527, 'Chennai', 'Chennai', 'चेन्नई', '|chennai|madras|', 'Tamil Nadu', 'IN', 'India', 13.08784, 80.27847, 'Asia/Kolkata', 4646732)"
            )
        )
    from jyotish_api import cache

    cache._local.clear()
    cache._client = None
    r = cache._redis()
    if r is not None:
        r.flushdb()
    emailer.outbox.clear()
    yield


@pytest.fixture
def client(db_ready: None) -> TestClient:
    from jyotish_api.main import app

    c = TestClient(app, base_url="http://testserver")
    c.headers["X-CSRF"] = "1"
    return c


def sign_in(c: TestClient, email: str, consent: bool = True) -> TestClient:
    r = c.post("/v1/auth/email/start", json={"email": email})
    assert r.status_code == 202, r.text
    body = emailer.outbox[-1].get_content()
    token = re.search(r"token=([A-Za-z0-9_\-]+)", body).group(1)  # type: ignore[union-attr]
    r = c.post("/v1/auth/email/verify", json={"token": token})
    assert r.status_code == 200, r.text
    if consent:
        assert c.post("/v1/me/consent", json={"accept": True}).status_code == 200
    return c


@pytest.fixture
def user(client: TestClient) -> TestClient:
    return sign_in(client, "asha@example.com")


PUNE = {
    "name": "Asha",
    "birth_date": "1990-05-15",
    "birth_time": "10:30:00",
    "latitude": 18.5204,
    "longitude": 73.8567,
    "place_name": "Pune, Maharashtra, India",
    "tz_name": "Asia/Kolkata",
}

from fastapi.testclient import TestClient

from jyotish_api import main
from jyotish_api.main import app

client = TestClient(app)


def test_health_reports_engine_version(monkeypatch) -> None:
    # Pretend the database and Redis are up, so this test runs without Docker.
    monkeypatch.setattr(main, "database_is_up", lambda: True)
    monkeypatch.setattr(main, "redis_is_up", lambda: True)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["engine_version"] == "0.1.0"


def test_health_is_degraded_when_database_is_down(monkeypatch) -> None:
    monkeypatch.setattr(main, "database_is_up", lambda: False)
    monkeypatch.setattr(main, "redis_is_up", lambda: True)

    assert client.get("/health").json()["status"] == "degraded"
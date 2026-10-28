"""Mobile app support: code sign-in, bearer tokens, push alerts, chart layout (US-81 to US-85)."""

import re
from datetime import datetime
from typing import Any

import pytest
from conftest import PUNE
from fastapi.testclient import TestClient
from jyotish_api import emailer
from jyotish_api.db import SessionLocal
from jyotish_api.services import push

PUSH = "ExponentPushToken[abcdefghijklmnop1234]"


def _app() -> TestClient:
    from jyotish_api.main import app

    return TestClient(app, base_url="http://testserver")


def _code_sign_in(email: str = "ravi@example.com") -> tuple[TestClient, dict[str, Any]]:
    c = _app()
    c.headers["X-CSRF"] = "1"
    assert c.post("/v1/auth/app/email/start", json={"email": email, "locale": "hi"}).status_code == 202
    msg = emailer.outbox[-1]
    code = re.search(r"\b(\d{6})\b", msg.get_content()).group(1)  # type: ignore[union-attr]
    assert "कोड" in msg["Subject"]
    r = c.post("/v1/auth/app/email/verify", json={"email": email, "code": code})
    assert r.status_code == 200, r.text
    return c, r.json()


def _bearer(token: str) -> TestClient:
    c = _app()  # no cookies, no CSRF header: like the phone
    c.headers["Authorization"] = f"Bearer {token}"
    return c


def test_code_sign_in_gives_bearer_token(db_ready: None) -> None:
    _, out = _code_sign_in()
    assert out["needs_consent"] is True
    phone = _bearer(out["token"])
    assert phone.get("/v1/me").json()["email"] == "ravi@example.com"
    # Writes work without the CSRF header when a bearer token is used.
    assert phone.post("/v1/me/consent", json={"accept": True}).status_code == 200
    assert phone.post("/v1/profiles", json=PUNE).status_code == 201
    assert phone.post("/v1/auth/logout").status_code == 200
    assert phone.get("/v1/me").status_code == 401


def test_code_works_once(db_ready: None) -> None:
    c = _app()
    c.headers["X-CSRF"] = "1"
    c.post("/v1/auth/app/email/start", json={"email": "a@example.com"})
    code = re.search(r"\b(\d{6})\b", emailer.outbox[-1].get_content()).group(1)  # type: ignore[union-attr]
    assert c.post("/v1/auth/app/email/verify", json={"email": "a@example.com", "code": code}).status_code == 200
    assert c.post("/v1/auth/app/email/verify", json={"email": "a@example.com", "code": code}).status_code == 400


def test_new_code_replaces_old(db_ready: None) -> None:
    c = _app()
    c.headers["X-CSRF"] = "1"
    c.post("/v1/auth/app/email/start", json={"email": "b@example.com"})
    old = re.search(r"\b(\d{6})\b", emailer.outbox[-1].get_content()).group(1)  # type: ignore[union-attr]
    c.post("/v1/auth/app/email/start", json={"email": "b@example.com"})
    new = re.search(r"\b(\d{6})\b", emailer.outbox[-1].get_content()).group(1)  # type: ignore[union-attr]
    if old != new:
        assert c.post("/v1/auth/app/email/verify", json={"email": "b@example.com", "code": old}).status_code == 400
    assert c.post("/v1/auth/app/email/verify", json={"email": "b@example.com", "code": new}).status_code == 200


def test_code_guessing_is_limited(db_ready: None) -> None:
    c = _app()
    c.headers["X-CSRF"] = "1"
    c.post("/v1/auth/app/email/start", json={"email": "g@example.com"})
    code = re.search(r"\b(\d{6})\b", emailer.outbox[-1].get_content()).group(1)  # type: ignore[union-attr]
    wrong = f"{(int(code) + 1) % 1_000_000:06d}"
    codes = [c.post("/v1/auth/app/email/verify", json={"email": "g@example.com", "code": wrong}).status_code for _ in range(5)]
    assert codes == [400] * 5
    # Even the right code is refused after too many wrong ones.
    assert c.post("/v1/auth/app/email/verify", json={"email": "g@example.com", "code": code}).status_code == 429


def test_cookie_requests_still_need_csrf(user: TestClient) -> None:
    user.headers.pop("X-CSRF")
    assert user.post("/v1/profiles", json=PUNE).status_code == 403
    # A bearer header alongside the cookie does not get the write through.
    user.headers["Authorization"] = "Bearer nonsense"
    assert user.post("/v1/profiles", json=PUNE).status_code in (401, 403)


def test_bad_bearer_token(db_ready: None) -> None:
    assert _bearer("not-a-token").get("/v1/me").status_code == 401


def test_google_app_sign_in_needs_config(db_ready: None) -> None:
    c = _app()
    c.headers["X-CSRF"] = "1"
    assert c.post("/v1/auth/app/google", json={"id_token": "x"}).status_code == 404


def test_google_app_sign_in(db_ready: None, monkeypatch: pytest.MonkeyPatch) -> None:
    from jyotish_api.routers import auth
    from jyotish_api.settings import settings

    monkeypatch.setattr(settings, "google_mobile_client_ids", ["android-id"])
    seen: dict[str, Any] = {}

    def fake_verify(token: str, nonce: str | None, audience: list[str] | None = None) -> dict[str, object]:
        seen.update(token=token, nonce=nonce, audience=audience)
        if token != "good":
            raise ValueError("bad")
        return {"sub": "g-123", "email": "Meera@Example.com", "email_verified": True, "name": "Meera"}

    monkeypatch.setattr(auth, "_verify_google_id_token", fake_verify)
    c = _app()
    c.headers["X-CSRF"] = "1"
    assert c.post("/v1/auth/app/google", json={"id_token": "bad"}).status_code == 401
    r = c.post("/v1/auth/app/google", json={"id_token": "good"})
    assert r.status_code == 200
    assert seen["audience"] == ["android-id"] and seen["nonce"] is None
    me = _bearer(r.json()["token"]).get("/v1/me").json()
    assert me["email"] == "meera@example.com"


def test_profiles_shared_between_web_and_phone(user: TestClient) -> None:
    """US-82: the same account sees the same profiles on both."""
    c = _app()
    c.headers["X-CSRF"] = "1"
    c.post("/v1/auth/app/email/start", json={"email": "asha@example.com"})
    code = re.search(r"\b(\d{6})\b", emailer.outbox[-1].get_content()).group(1)  # type: ignore[union-attr]
    phone = _bearer(c.post("/v1/auth/app/email/verify", json={"email": "asha@example.com", "code": code}).json()["token"])
    web_made = user.post("/v1/profiles", json=PUNE).json()
    assert [p["id"] for p in phone.get("/v1/profiles").json()["items"]] == [web_made["id"]]
    phone_made = phone.post("/v1/profiles", json={**PUNE, "name": "Ravi"}).json()
    assert phone_made["id"] in [p["id"] for p in user.get("/v1/profiles").json()["items"]]


def test_chart_layout(user: TestClient) -> None:
    p = user.post("/v1/profiles", json=PUNE).json()
    north = user.get(f"/v1/profiles/{p['id']}/chart-layout", params={"lang": "mr"}).json()
    assert north["style"] == "north" and north["size"] == 400
    assert north["svg"].startswith("<svg") and "stroke" in north["svg"]
    kinds = {lb["kind"] for lb in north["labels"]}
    assert {"planet", "sign", "asc"} <= kinds
    assert any(lb["text"] == "लग्न" for lb in north["labels"])
    south = user.get(f"/v1/profiles/{p['id']}/chart-layout", params={"style": "south", "varga": "d9"}).json()
    assert south["style"] == "south" and south["varga"] == "D9"
    assert any(lb["kind"] == "title" and lb["text"] == "D9" for lb in south["labels"])
    assert user.get(f"/v1/profiles/{p['id']}/chart-layout", params={"varga": "D99"}).status_code == 422


def test_chart_layout_matches_pdf_drawing(user: TestClient) -> None:
    """The phone gets exactly the layout the PDF report draws."""
    from jyotish_api.services import charts, svg
    from jyotish_engine.names import names
    from jyotish_engine.settings import ChartSettings

    p = user.post("/v1/profiles", json=PUNE).json()
    out = user.get(f"/v1/profiles/{p['id']}/chart-layout").json()
    c = charts.chart_dict(charts.birth_from(PUNE), ChartSettings.from_dict({}), ("D1",))
    _, labels = svg.layout(c, "D1", "north", names("en"), "Asc")
    assert [(lb["x"], lb["y"], lb["text"]) for lb in out["labels"]] == [(lb.x, lb.y, lb.text) for lb in labels]


def test_push_tokens(user: TestClient) -> None:
    assert user.post("/v1/alerts/push-tokens", json={"token": "junk", "platform": "android"}).status_code == 422
    assert user.post("/v1/alerts/push-tokens", json={"token": PUSH, "platform": "android"}).status_code == 204
    assert user.post("/v1/alerts/push-tokens", json={"token": PUSH, "platform": "android"}).status_code == 204
    assert user.get("/v1/alerts").json()["push_enabled"] is True
    # The web app's settings form leaves push_enabled out; it must stay as it was.
    user.put("/v1/alerts", json={"dasha_change": True, "major_transit": True, "email_enabled": False})
    assert user.get("/v1/alerts").json()["push_enabled"] is True
    assert user.post("/v1/alerts/push-tokens/remove", json={"token": PUSH}).status_code == 204


def test_daily_alerts_go_to_the_phone(user: TestClient) -> None:
    from jyotish_api.services.alerts import run_daily

    push.outbox.clear()
    p = user.post("/v1/profiles", json=PUNE).json()
    c = user.get(f"/v1/profiles/{p['id']}/chart").json()
    day = datetime.fromisoformat(c["dasha"]["mahadashas"][2]["start"]).replace(hour=12)
    user.post("/v1/alerts/push-tokens", json={"token": PUSH, "platform": "ios"})
    # Email off, push on: only the push message goes out.
    user.put("/v1/alerts", json={"dasha_change": True, "major_transit": False, "email_enabled": False, "push_enabled": True})
    before = len(emailer.outbox)
    with SessionLocal() as db:
        assert run_daily(db, day) == 1
        assert run_daily(db, day) == 0
    assert len(emailer.outbox) == before
    assert len(push.outbox) == 1
    msg = push.outbox[0]
    assert msg["to"] == PUSH and "Mahadasha" in msg["body"] and msg["data"]["profile_id"] == p["id"]
    assert "unsubscribe" not in msg["body"].lower()


def test_push_switched_off(user: TestClient) -> None:
    from jyotish_api.services.alerts import run_daily

    push.outbox.clear()
    p = user.post("/v1/profiles", json=PUNE).json()
    c = user.get(f"/v1/profiles/{p['id']}/chart").json()
    day = datetime.fromisoformat(c["dasha"]["mahadashas"][2]["start"]).replace(hour=12)
    user.post("/v1/alerts/push-tokens", json={"token": PUSH, "platform": "ios"})
    user.put("/v1/alerts", json={"dasha_change": True, "major_transit": False, "email_enabled": False, "push_enabled": False})
    with SessionLocal() as db:
        assert run_daily(db, day) == 0
    assert push.outbox == []


def test_dead_push_tokens_are_removed(monkeypatch: pytest.MonkeyPatch) -> None:
    from jyotish_api.settings import settings

    class Resp:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return {"data": [{"status": "ok"}, {"status": "error", "details": {"error": "DeviceNotRegistered"}}]}

    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(push.httpx, "post", lambda *a, **k: Resp())
    dead = push.send([PUSH, "ExponentPushToken[zzzzzzzzzzzzzzzzzzzz]"], "t", "b")
    assert dead == ["ExponentPushToken[zzzzzzzzzzzzzzzzzzzz]"]


def test_valid_push_token() -> None:
    assert push.valid_token(PUSH)
    assert push.valid_token("ExpoPushToken[xxxxxxxxxxxxxxxxxxxxxx]")
    assert not push.valid_token("ExponentPushToken[]")
    assert not push.valid_token("https://evil.example/")

"""End-to-end API behaviour against PostgreSQL, story by story."""

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select, text, update

from jyotish_api import emailer
from jyotish_api.db import SessionLocal, engine
from jyotish_api.models import LoginToken, Profile

from conftest import PUNE, sign_in


def _new_client() -> TestClient:
    from jyotish_api.main import app

    c = TestClient(app)
    c.headers["X-CSRF"] = "1"
    return c


# --- US-07 / US-08: sign-in and access control ------------------------------

def test_email_sign_in_and_me(client: TestClient) -> None:
    sign_in(client, "Ravi@Example.com", consent=False)
    me = client.get("/v1/me").json()
    assert me["email"] == "ravi@example.com"
    assert me["consent"]["given"] is False


def test_login_link_works_once(client: TestClient) -> None:
    client.post("/v1/auth/email/start", json={"email": "a@example.com"})
    import re

    token = re.search(r"token=([A-Za-z0-9_\-]+)", emailer.outbox[-1].get_content()).group(1)  # type: ignore[union-attr]
    assert client.post("/v1/auth/email/verify", json={"token": token}).status_code == 200
    assert client.post("/v1/auth/email/verify", json={"token": token}).status_code == 400


def test_expired_link_is_refused(client: TestClient) -> None:
    client.post("/v1/auth/email/start", json={"email": "b@example.com"})
    import re

    token = re.search(r"token=([A-Za-z0-9_\-]+)", emailer.outbox[-1].get_content()).group(1)  # type: ignore[union-attr]
    with SessionLocal() as db:
        db.execute(update(LoginToken).values(expires_at=datetime.now(UTC) - timedelta(minutes=1)))
        db.commit()
    assert client.post("/v1/auth/email/verify", json={"token": token}).status_code == 400


def test_no_session_is_401(client: TestClient) -> None:
    assert client.get("/v1/me").status_code == 401
    assert client.get("/v1/profiles").status_code == 401


def test_expired_session_is_401(user: TestClient) -> None:
    with engine.begin() as conn:
        conn.execute(text("UPDATE sessions SET expires_at = now() - interval '1 minute'"))
    assert user.get("/v1/me").status_code == 401


def test_csrf_header_required(user: TestClient) -> None:
    r = user.post("/v1/profiles", json=PUNE, headers={"X-CSRF": ""})
    assert r.status_code == 403


def test_logout(user: TestClient) -> None:
    assert user.post("/v1/auth/logout").status_code == 200
    assert user.get("/v1/me").status_code == 401


def test_other_users_profile_is_404(client: TestClient) -> None:
    a = sign_in(client, "a@example.com")
    pid = a.post("/v1/profiles", json=PUNE).json()["id"]
    b = sign_in(_new_client(), "b@example.com")
    assert b.get(f"/v1/profiles/{pid}").status_code == 404
    assert b.get(f"/v1/profiles/{pid}/chart").status_code == 404
    assert b.delete(f"/v1/profiles/{pid}").status_code == 404


# --- US-09: consent ----------------------------------------------------------

def test_consent_required_before_profiles(client: TestClient) -> None:
    sign_in(client, "c@example.com", consent=False)
    r = client.post("/v1/profiles", json=PUNE)
    assert r.status_code == 403 and r.json()["detail"] == "consent_required"
    assert client.post("/v1/me/consent", json={"accept": False}).status_code == 400
    assert client.post("/v1/me/consent", json={"accept": True}).json()["consent"]["given"]
    with engine.begin() as conn:
        row = conn.execute(text("SELECT purpose, version, accepted_at FROM consents")).one()
    assert row.purpose == "chart_calculation" and row.accepted_at is not None
    assert client.post("/v1/profiles", json=PUNE).status_code == 201


# --- US-13 to US-18: profiles -------------------------------------------------

def test_impossible_date_is_rejected(user: TestClient) -> None:
    r = user.post("/v1/profiles", json={**PUNE, "birth_date": "1990-02-31"})
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"][-1] == "birth_date"


def test_manual_coordinates_find_time_zone(user: TestClient) -> None:
    body = {k: v for k, v in PUNE.items() if k != "tz_name"}
    p = user.post("/v1/profiles", json=body).json()
    assert p["tz_name"] == "Asia/Kolkata"


def test_us15_war_time_offset(user: TestClient) -> None:
    p = user.post("/v1/profiles", json={**PUNE, "birth_date": "1943-03-10", "latitude": 22.5726, "longitude": 88.3639}).json()
    c = user.get(f"/v1/profiles/{p['id']}/chart").json()
    assert c["input"]["utc_offset_minutes"] == 390


def test_profile_limit_and_encryption(user: TestClient) -> None:
    for i in range(10):
        assert user.post("/v1/profiles", json={**PUNE, "name": f"Person {i}"}).status_code == 201
    r = user.post("/v1/profiles", json=PUNE)
    assert r.status_code == 409
    with SessionLocal() as db:
        raw = db.scalars(select(Profile.birth_enc)).first()
    assert raw is not None and b"Person" not in bytes(raw) and b"1990" not in bytes(raw)
    lst = user.get("/v1/profiles").json()
    assert lst["count"] == 10 and lst["limit"] == 10
    assert sum(1 for i in lst["items"] if i["is_main"]) == 1


def test_edit_birth_time_recalculates(user: TestClient) -> None:
    p = user.post("/v1/profiles", json=PUNE).json()
    before = user.get(f"/v1/profiles/{p['id']}/chart").json()["lagna"]["longitude"]
    user.put(f"/v1/profiles/{p['id']}", json={**PUNE, "birth_time": "18:30:00"})
    after = user.get(f"/v1/profiles/{p['id']}/chart").json()["lagna"]["longitude"]
    assert before != after


def test_ayanamsa_setting_shifts_longitudes(user: TestClient) -> None:
    lahiri = user.post("/v1/profiles", json=PUNE).json()
    raman = user.post("/v1/profiles", json={**PUNE, "settings": {"ayanamsa": "raman"}}).json()
    a = user.get(f"/v1/profiles/{lahiri['id']}/chart").json()
    b = user.get(f"/v1/profiles/{raman['id']}/chart").json()
    diff = a["meta"]["ayanamsa_value"] - b["meta"]["ayanamsa_value"]
    for pa, pb in zip(a["planets"], b["planets"], strict=True):
        assert abs(((pb["longitude"] - pa["longitude"]) % 360) - diff) < 1e-5
    assert b["meta"]["settings"]["ayanamsa"] == "raman"
    assert a["meta"]["settings"] == {"ayanamsa": "lahiri", "node_type": "mean", "house_system": "whole_sign",
                                     "dasha_year_days": 365.25, "chart_style": "north"}


# --- US-25: chart API ---------------------------------------------------------

def test_chart_is_byte_identical_and_versioned(user: TestClient) -> None:
    p = user.post("/v1/profiles", json=PUNE).json()
    r1 = user.get(f"/v1/profiles/{p['id']}/chart")
    r2 = user.get(f"/v1/profiles/{p['id']}/chart")
    assert r1.content == r2.content
    meta = r1.json()["meta"]
    assert {"engine_version", "ephemeris_version", "ayanamsa", "settings"} <= set(meta)


def test_preview_chart_needs_no_account(client: TestClient) -> None:
    body = {"birth": {k: v for k, v in PUNE.items() if k != "name"}, "vargas": ["D1", "D9", "D60"], "bhava_chalit": True}
    r = client.post("/v1/charts", json=body)
    assert r.status_code == 200
    c = r.json()
    assert set(c["vargas"]) == {"D1", "D9", "D60"} and "bhava_chalit" in c
    assert client.post("/v1/charts", json={**body, "vargas": ["D5"]}).status_code == 422


def test_readings_in_hindi_have_sources(user: TestClient) -> None:
    p = user.post("/v1/profiles", json=PUNE).json()
    r = user.get(f"/v1/profiles/{p['id']}/readings", params={"lang": "hi"}).json()
    assert r["readings"]
    first = r["readings"][0]
    assert first["source"] and first["id"] and any("ऀ" <= ch <= "ॿ" for ch in first["text"])


def test_transits_and_strength(user: TestClient) -> None:
    p = user.post("/v1/profiles", json=PUNE).json()
    t = user.get(f"/v1/profiles/{p['id']}/transits", params={"on": "2026-01-01"}).json()
    assert len(t["planets"]) == 9 and all(1 <= x["house_from_moon"] <= 12 for x in t["planets"])
    assert t["sade_sati"]["cycles"]
    s = user.get(f"/v1/profiles/{p['id']}/strength").json()
    assert s["ashtakavarga"]["sarva_total"] == 337
    assert len(s["shadbala"]["planets"]) == 7


def test_csv_export(user: TestClient) -> None:
    p = user.post("/v1/profiles", json=PUNE).json()
    r = user.get(f"/v1/profiles/{p['id']}/export.csv")
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
    assert len(r.text.strip().splitlines()) == 11  # header + lagna + 9 grahas


# --- places, Panchang, names ---------------------------------------------------

def test_place_search(client: TestClient) -> None:
    items = client.get("/v1/places/search", params={"q": "pun"}).json()["items"]
    assert items[0]["label"] == "Pune, Maharashtra, India" and items[0]["tz_name"] == "Asia/Kolkata"
    assert client.get("/v1/places/search", params={"q": "bombay"}).json()["items"][0]["name"] == "Mumbai"
    assert client.get("/v1/places/search", params={"q": "पुणे"}).json()["items"][0]["name"] == "Pune"


def test_panchang_endpoint(client: TestClient) -> None:
    r = client.get("/v1/panchang", params={"on": "2024-04-23", "lat": 28.6139, "lon": 77.209})
    assert r.status_code == 200
    assert r.json()["tithi"][0]["name"]["name"] == "purnima"


def test_names(client: TestClient) -> None:
    n = client.get("/v1/names", params={"lang": "mr"}).json()
    assert n["planets"]["mars"] == "मंगळ" and n["signs"]["libra"] == "तूळ"


# --- matching and reports ------------------------------------------------------

def test_match_and_pdf_reports(user: TestClient) -> None:
    a = user.post("/v1/profiles", json={**PUNE, "name": "Arjun", "gender": "male"}).json()
    b = user.post("/v1/profiles", json={**PUNE, "name": "Meera", "birth_date": "1992-08-01", "gender": "female"}).json()
    m = user.post("/v1/match", json={"boy_profile_id": a["id"], "girl_profile_id": b["id"]}).json()
    assert m["ashtakoota"]["max"] == 36 and len(m["ashtakoota"]["kootas"]) == 8
    for kind, extra in (("natal", {}), ("match", {"partner_profile_id": b["id"]})):
        for lang in ("en", "hi"):
            r = user.post("/v1/reports", json={"profile_id": a["id"], "kind": kind, "lang": lang, **extra}).json()
            got = user.get(f"/v1/reports/{r['id']}").json()
            assert got["status"] == "ready", got
            pdf = user.get(f"/v1/reports/{r['id']}/download")
            assert pdf.content[:4] == b"%PDF" and len(pdf.content) > 10_000
    assert len(user.get("/v1/reports").json()["items"]) == 4


# --- US-10 / US-11: export and delete ------------------------------------------

def test_export_and_delete_account(user: TestClient) -> None:
    user.post("/v1/profiles", json=PUNE)
    data = json.loads(user.get("/v1/me/export").content)
    assert data["account"]["email"] == "asha@example.com" and data["profiles"][0]["name"] == "Asha"
    assert user.request("DELETE", "/v1/me", json={"confirm_email": "wrong@example.com"}).status_code == 400
    assert user.request("DELETE", "/v1/me", json={"confirm_email": "asha@example.com"}).status_code == 200
    assert user.get("/v1/me").status_code == 401
    with engine.begin() as conn:
        for t in ("users", "profiles", "sessions", "consents", "login_tokens"):
            assert conn.execute(text(f"SELECT count(*) FROM {t}")).scalar() == 0, t
        assert conn.execute(text("SELECT count(*) FROM audit_log WHERE actor_id IS NOT NULL OR target_user_id IS NOT NULL")).scalar() == 0


# --- US-12: admin audit -------------------------------------------------------

def test_admin_needs_reason_for_birth_details(client: TestClient) -> None:
    u = sign_in(client, "user@example.com")
    u.post("/v1/profiles", json=PUNE)
    uid = u.get("/v1/me").json()["id"]
    admin = sign_in(_new_client(), "admin@example.com")
    assert admin.get(f"/v1/admin/users/{uid}").status_code == 403
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET role='admin' WHERE email='admin@example.com'"))
    opened = admin.get(f"/v1/admin/users/{uid}").json()
    assert "profiles" in opened and "birth_date" not in json.dumps(opened)
    assert admin.post(f"/v1/admin/users/{uid}/birth-details", json={"reason": "short"}).status_code == 422
    r = admin.post(f"/v1/admin/users/{uid}/birth-details", json={"reason": "User asked support to check their birth time"})
    assert r.json()["items"][0]["name"] == "Asha"
    log = admin.get("/v1/admin/audit", params={"user_id": uid}).json()["items"]
    actions = [x["what"] for x in log]
    assert "admin.view_birth_details" in actions and "admin.open_user" in actions
    assert any(x["reason"] for x in log if x["what"] == "admin.view_birth_details")


# --- alerts ------------------------------------------------------------------

def test_alert_prefs_and_unsubscribe(user: TestClient) -> None:
    assert user.get("/v1/alerts").json()["email_enabled"] is True
    user.put("/v1/alerts", json={"dasha_change": True, "major_transit": False, "email_enabled": True})
    with engine.begin() as conn:
        token = conn.execute(text("SELECT unsubscribe_token FROM alert_prefs")).scalar()
    assert user.get("/v1/alerts/unsubscribe", params={"token": token}).status_code == 200
    assert user.get("/v1/alerts").json()["email_enabled"] is False


def test_daily_alerts_send_once(user: TestClient) -> None:
    from jyotish_api.services.alerts import run_daily

    p = user.post("/v1/profiles", json=PUNE).json()
    c = user.get(f"/v1/profiles/{p['id']}/chart").json()
    maha = c["dasha"]["mahadashas"][2]
    day = datetime.fromisoformat(maha["start"]).replace(hour=12)
    user.get("/v1/alerts")
    with SessionLocal() as db:
        assert run_daily(db, day) == 1
        assert run_daily(db, day) == 0  # not twice
    msg = emailer.outbox[-1]
    assert "Mahadasha" in msg.get_content() and msg["List-Unsubscribe"]


# --- US-77 to US-80: partner API -----------------------------------------------

def test_api_keys_and_limits(user: TestClient) -> None:
    k = user.post("/v1/developer/keys", json={"name": "test"}).json()
    key = k["key"]
    pub = _new_client()
    body = {"birth": {k2: v for k2, v in PUNE.items() if k2 != "name"}}
    assert pub.post("/public/v1/chart", json=body).status_code == 401
    r = pub.post("/public/v1/chart", json=body, headers={"X-API-Key": key})
    assert r.status_code == 200 and r.headers["X-RateLimit-Limit-Day"] == "1000"
    with engine.begin() as conn:
        conn.execute(text("UPDATE api_keys SET daily_limit = 1"))
    assert pub.post("/public/v1/chart", json=body, headers={"X-API-Key": key}).status_code == 429
    user.delete(f"/v1/developer/keys/{k['id']}")
    assert pub.post("/public/v1/chart", json=body, headers={"X-API-Key": key}).status_code == 401
    keys = user.get("/v1/developer/keys").json()["items"]
    assert "key" not in keys[0] and keys[0]["revoked_at"]

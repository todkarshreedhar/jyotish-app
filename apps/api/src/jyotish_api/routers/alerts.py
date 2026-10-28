"""Alert preferences and one-click unsubscribe (US-69 to US-71)."""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select

from jyotish_api.models import AlertPrefs
from jyotish_api.security import DB, CurrentUser
from jyotish_api.services.alerts import prefs_for

router = APIRouter(prefix="/v1/alerts", tags=["alerts"])


def _out(p: AlertPrefs) -> dict[str, Any]:
    return {"dasha_change": p.dasha_change, "major_transit": p.major_transit, "email_enabled": p.email_enabled}


@router.get("")
def get_prefs(user: CurrentUser, db: DB) -> dict[str, Any]:
    p = prefs_for(db, user)
    db.commit()
    return _out(p)


class PrefsIn(BaseModel):
    dasha_change: bool
    major_transit: bool
    email_enabled: bool


@router.put("")
def put_prefs(body: PrefsIn, user: CurrentUser, db: DB) -> dict[str, Any]:
    p = prefs_for(db, user)
    p.dasha_change, p.major_transit, p.email_enabled = body.dasha_change, body.major_transit, body.email_enabled
    db.commit()
    return _out(p)


def _unsubscribe(db: DB, token: str) -> bool:
    p = db.scalar(select(AlertPrefs).where(AlertPrefs.unsubscribe_token == token))
    if p is None:
        return False
    p.email_enabled = False
    db.commit()
    return True


@router.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_page(token: str, db: DB) -> str:
    ok = _unsubscribe(db, token)
    msg = "You will not receive alert emails any more." if ok else "This link is not valid."
    return f"<!doctype html><meta charset=utf-8><title>Jyotish</title><p style='font-family:sans-serif;margin:3rem'>{msg}</p>"


@router.post("/unsubscribe")
def unsubscribe_one_click(token: str, db: DB) -> dict[str, bool]:
    """RFC 8058 one-click unsubscribe (mail clients POST here)."""
    return {"ok": _unsubscribe(db, token)}

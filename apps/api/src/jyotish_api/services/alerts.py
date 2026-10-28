"""Daily alerts (US-69 to US-71): Dasha changes and major transits.

Sent once per event, by email, only for the user's main profile, and only
for alert types the user has switched on. Every email has a one-click
unsubscribe link.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from jyotish_engine.constants import Graha
from jyotish_engine.names import names
from jyotish_engine.timeutil import julian_day_ut
from jyotish_engine.transits import sign_ingresses

from jyotish_api import emailer
from jyotish_api.crypto import decrypt_json, new_token
from jyotish_api.models import AlertPrefs, Profile, User
from jyotish_api.services import charts
from jyotish_api.settings import settings

SLOW = (Graha.SATURN, Graha.JUPITER, Graha.RAHU)

SUBJECT = {"en": "Your Jyotish update", "hi": "आपका ज्योतिष अपडेट", "mr": "तुमचे ज्योतिष अपडेट"}
LINES = {
    "en": {"maha": "Your {lord} Mahadasha begins today.", "antar": "Your {maha}/{lord} Antardasha begins today.",
           "transit": "{planet} enters {sign} today, the {house} house from your Moon.", "unsub": "Stop these emails: {url}"},
    "hi": {"maha": "आज से आपकी {lord} महादशा आरंभ होती है।", "antar": "आज से आपकी {maha}/{lord} अंतर्दशा आरंभ होती है।",
           "transit": "आज {planet} {sign} में प्रवेश करता है, जो आपके चंद्र से {house}वाँ भाव है।", "unsub": "ये ईमेल बंद करें: {url}"},
    "mr": {"maha": "आजपासून तुमची {lord} महादशा सुरू होते.", "antar": "आजपासून तुमची {maha}/{lord} अंतर्दशा सुरू होते.",
           "transit": "आज {planet} {sign} राशीत प्रवेश करतो, जे तुमच्या चंद्रापासून {house}वे स्थान आहे.", "unsub": "हे ईमेल बंद करा: {url}"},
}


def prefs_for(db: Session, user: User) -> AlertPrefs:
    p = db.get(AlertPrefs, user.id)
    if p is None:
        p = AlertPrefs(user_id=user.id, unsubscribe_token=new_token(24), last_sent={})
        db.add(p)
        db.flush()
    return p


def events_for(chart: dict[str, Any], day_start: datetime, settings_obj: Any, prefs: AlertPrefs) -> list[tuple[str, dict[str, Any]]]:
    jd0 = julian_day_ut(day_start)
    jd1 = jd0 + 1
    out: list[tuple[str, dict[str, Any]]] = []
    if prefs.dasha_change:
        for m in chart["dasha"]["mahadashas"]:
            if jd0 <= m["start_jd"] < jd1:
                out.append((f"maha:{m['start_jd']}", {"type": "maha", "lord": m["lord"]}))
            for a in m.get("periods", []):
                if jd0 <= a["start_jd"] < jd1 and a["lord"] != m["lord"]:
                    out.append((f"antar:{a['start_jd']}", {"type": "antar", "maha": m["lord"], "lord": a["lord"]}))
    if prefs.major_transit:
        moon_sign = next(p["sign_index"] for p in chart["planets"] if p["id"] == "moon")
        for g in SLOW:
            for ing in sign_ingresses(g, jd0, jd1, settings_obj, step=0.25):
                house = (ing.to_sign - moon_sign) % 12 + 1
                out.append((f"transit:{g}:{round(ing.jd, 2)}", {"type": "transit", "planet": str(g), "sign": ing.to_sign, "house": house}))
    return out


def render(lang: str, events: list[dict[str, Any]], unsub_url: str) -> str:
    n = names(lang)
    t = LINES.get(lang, LINES["en"])
    signs = list(n["signs"].values())
    lines = []
    for e in events:
        if e["type"] == "maha":
            lines.append(t["maha"].format(lord=n["planets"][e["lord"]]))
        elif e["type"] == "antar":
            lines.append(t["antar"].format(maha=n["planets"][e["maha"]], lord=n["planets"][e["lord"]]))
        else:
            lines.append(t["transit"].format(planet=n["planets"][e["planet"]], sign=signs[e["sign"]], house=e["house"]))
    return "\n".join(lines) + "\n\n" + t["unsub"].format(url=unsub_url)


def run_daily(db: Session, now: datetime) -> int:
    sent = 0
    day_start = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    for user in db.scalars(select(User)):
        prefs = prefs_for(db, user)
        if not prefs.email_enabled or not (prefs.dasha_change or prefs.major_transit):
            continue
        main = db.scalar(select(Profile).where(Profile.user_id == user.id, Profile.is_main.is_(True)))
        if main is None:
            continue
        b = decrypt_json(main.birth_enc)
        from jyotish_engine.settings import ChartSettings

        cs = ChartSettings.from_dict(main.settings)
        chart = charts.chart_dict(charts.birth_from(b), cs, ("D1",))
        new = [(k, e) for k, e in events_for(chart, day_start, cs, prefs) if k not in (prefs.last_sent or {})]
        if not new:
            continue
        url = f"{settings.web_url}/api/v1/alerts/unsubscribe?token={prefs.unsubscribe_token}"
        emailer.send(user.email, SUBJECT.get(user.locale, SUBJECT["en"]), render(user.locale, [e for _, e in new], url),
                     headers={"List-Unsubscribe": f"<{url}>", "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"})
        ls = dict(prefs.last_sent or {})
        cutoff = (day_start - timedelta(days=400)).isoformat()
        ls = {k: v for k, v in ls.items() if v >= cutoff}
        ls.update({k: day_start.isoformat() for k, _ in new})
        prefs.last_sent = ls
        sent += 1
    db.commit()
    return sent

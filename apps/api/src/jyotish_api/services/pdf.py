"""PDF reports (US-48, US-52, US-68, US-74) rendered with WeasyPrint."""

import base64
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from jyotish_engine.core import dms
from jyotish_engine.names import names
from jyotish_engine.timeutil import julian_day_ut

from jyotish_api.services import svg
from jyotish_api.services.report_text import ASC, LABELS

HERE = Path(__file__).resolve().parent.parent
env = Environment(loader=FileSystemLoader(HERE / "templates"), autoescape=select_autoescape(["html"]))
FONT_DIR = (HERE / "fonts").as_uri()


def _render(template: str, ctx: dict[str, Any]) -> bytes:
    from weasyprint import HTML  # imported lazily: heavy, and only the worker needs it

    html = env.get_template(template).render(font_dir=FONT_DIR, **ctx)
    return HTML(string=html, base_url=str(HERE)).write_pdf()


def _brand(user: Any) -> dict[str, Any]:
    logo = None
    if getattr(user, "brand_logo", None):
        logo = f"data:{user.brand_logo_type or 'image/png'};base64," + base64.b64encode(user.brand_logo).decode()
    return {"brand_name": getattr(user, "brand_name", None), "brand_logo": logo}


def _footer(chart: dict[str, Any], lang: str) -> str:
    n = names(lang)
    return LABELS[lang]["footer"].format(
        ayanamsa=n["ayanamsas"][chart["meta"]["ayanamsa"]],
        engine=chart["meta"]["engine_version"],
        rules=chart.get("interpretations", {}).get("ruleset_version", "-"),
    )


def natal_pdf(
    profile: dict[str, Any],
    chart: dict[str, Any],
    readings: list[dict[str, Any]],
    lang: str,
    style: str,
    user: Any = None,
    now: datetime | None = None,
) -> bytes:
    L, N = LABELS[lang], names(lang)
    now = now or datetime.now(UTC)
    jd_now = julian_day_ut(now)
    moon = next(p for p in chart["planets"] if p["id"] == "moon")
    cur_maha, antars = None, []
    for m in chart["dasha"]["mahadashas"]:
        if m["start_jd"] <= jd_now < m["end_jd"]:
            cur_maha = m["lord"]
            antars = [{**a, "current": a["start_jd"] <= jd_now < a["end_jd"]} for a in m.get("periods", [])]
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for r in readings:
        by_topic.setdefault(r["topic"], []).append(r)
    off = chart["input"]["utc_offset_minutes"]
    acc = chart["input"].get("time_accuracy", "exact")
    ctx = {
        "lang": lang,
        "L": L,
        "N": N,
        "profile": profile,
        "chart": chart,
        "moon": moon,
        "offset": f"{'+' if off >= 0 else '-'}{abs(off) // 60:02d}:{abs(off) % 60:02d}",
        "ayanamsa_dms": dms(chart["meta"]["ayanamsa_value"]),
        "svg_d1": svg.draw(chart, "D1", style, N, ASC[lang], ""),
        "svg_d9": svg.draw(chart, "D9", style, N, ASC[lang], "D9") if "D9" in chart["vargas"] else "",
        "current_maha": cur_maha,
        "antars": antars,
        "readings": list(by_topic.items()),
        "time_note": L["time_note"].format(acc=L["accuracy"][acc]) if acc != "exact" else None,
        "footer": _footer(chart, lang),
        **_brand(user),
    }
    return _render("natal.html", ctx)


def match_pdf(data: dict[str, Any], lang: str, style: str, user: Any = None) -> bytes:
    L, N = LABELS[lang], names(lang)
    boy, girl = data["boy"], data["girl"]
    ctx = {
        "lang": lang,
        "L": L,
        "N": N,
        "boy": boy,
        "girl": girl,
        "score": data["ashtakoota"],
        "boy_moon": next(p for p in boy["chart"]["planets"] if p["id"] == "moon"),
        "girl_moon": next(p for p in girl["chart"]["planets"] if p["id"] == "moon"),
        "svg_boy": svg.draw(boy["chart"], "D1", style, N, ASC[lang]),
        "svg_girl": svg.draw(girl["chart"], "D1", style, N, ASC[lang]),
        "footer": _footer(boy["chart"], lang),
        **_brand(user),
    }
    return _render("match.html", ctx)

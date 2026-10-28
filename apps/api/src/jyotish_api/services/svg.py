"""North and South Indian chart drawings for PDF reports.

Lines are drawn in SVG; labels are placed as HTML on top of the SVG, because
PDF renderers shape Devanagari correctly in HTML text but not in SVG text.
The web app has a TypeScript twin (apps/web/components/chart) with the same
layout, so a printed report matches the screen.
"""

from dataclasses import dataclass
from html import escape
from typing import Any

SIZE = 400

# North Indian: house -> (planet text centre, sign number position)
NORTH = {
    1: ((200, 100), (200, 182)), 2: ((100, 36), (100, 86)), 3: ((36, 100), (86, 100)),
    4: ((100, 200), (182, 200)), 5: ((36, 300), (86, 300)), 6: ((100, 364), (100, 316)),
    7: ((200, 300), (200, 220)), 8: ((300, 364), (300, 316)), 9: ((364, 300), (316, 300)),
    10: ((300, 200), (220, 200)), 11: ((364, 100), (316, 100)), 12: ((300, 36), (300, 86)),
}  # fmt: skip
# South Indian: sign index -> grid cell (col, row); Pisces sits top-left.
SOUTH = {
    11: (0, 0),
    0: (1, 0),
    1: (2, 0),
    2: (3, 0),
    3: (3, 1),
    4: (3, 2),
    5: (3, 3),
    6: (2, 3),
    7: (1, 3),
    8: (0, 3),
    9: (0, 2),
    10: (0, 1),
}

LINE = 'stroke="#7a4b16" stroke-width="2" fill="none"'


@dataclass
class Label:
    x: float
    y: float
    text: str
    kind: str  # planet | retro | sign | asc | title
    anchor: str = "middle"  # middle | start | end


def _planet_text(p: dict[str, Any], abbr: dict[str, str]) -> tuple[str, bool]:
    deg = p.get("degree_in_sign")
    retro = bool(p.get("retrograde")) and p["id"] not in ("rahu", "ketu")
    return abbr[p["id"]] + (f"{int(deg)}°" if deg is not None else "") + ("(R)" if retro else ""), retro


def _stack(x: float, y: float, items: list[tuple[str, bool]]) -> list[Label]:
    lh = 15
    y0 = y - (len(items) - 1) * lh / 2
    return [Label(x, y0 + i * lh, t, "retro" if r else "planet") for i, (t, r) in enumerate(items)]


def north_layout(lagna_sign: int, planets: list[dict[str, Any]], abbr: dict[str, str], asc_label: str) -> tuple[str, list[Label]]:
    lines = f'<rect x="1" y="1" width="398" height="398" {LINE}/><path d="M0 0L400 400M400 0L0 400M200 0L400 200L200 400L0 200Z" {LINE}/>'
    by_house: dict[int, list[tuple[str, bool]]] = {h: [] for h in range(1, 13)}
    for p in planets:
        by_house[int(p["house"])].append(_planet_text(p, abbr))
    labels: list[Label] = []
    for h, ((px, py), (sx, sy)) in NORTH.items():
        labels.append(Label(sx, sy, str((lagna_sign + h - 1) % 12 + 1), "sign"))
        if h == 1:
            labels.append(Label(200, py - 38, asc_label, "asc"))
        labels += _stack(px, py, by_house[h])
    return lines, labels


def south_layout(
    lagna_sign: int, planets: list[dict[str, Any]], abbr: dict[str, str], sign_short: list[str], asc_label: str, title: str
) -> tuple[str, list[Label]]:
    c = SIZE / 4
    parts = [f'<rect x="1" y="1" width="398" height="398" {LINE}/>']
    for i in (1, 2, 3):
        parts.append(f'<path d="M{c * i} 0V{c if i == 2 else SIZE}M{c * i} {c * 3 if i == 2 else 0}V{SIZE}" {LINE}/>')
        parts.append(f'<path d="M0 {c * i}H{c if i == 2 else SIZE}M{c * 3 if i == 2 else 0} {c * i}H{SIZE}" {LINE}/>')
    by_sign: dict[int, list[tuple[str, bool]]] = {s: [] for s in range(12)}
    for p in planets:
        by_sign[int(p["sign_index"])].append(_planet_text(p, abbr))
    labels: list[Label] = []
    for s, (col, row) in SOUTH.items():
        x0, y0 = col * c, row * c
        # Lagna cell: the sign name sits right of the diagonal Lagna mark.
        labels.append(Label(x0 + (22 if s == lagna_sign else 6), y0 + 10, sign_short[s], "sign", "start"))
        if s == lagna_sign:
            parts.append(f'<path d="M{x0} {y0 + 24}L{x0 + 24} {y0}" {LINE}/>')
            labels.append(Label(x0 + c - 6, y0 + 10, asc_label, "asc", "end"))
        labels += _stack(x0 + c / 2, y0 + c / 2 + 6, by_sign[s])
    if title:
        labels.append(Label(200, 200, title, "title"))
    return "".join(parts), labels


def varga_planets(chart: dict[str, Any], code: str) -> tuple[int, list[dict[str, Any]]]:
    v = chart["vargas"][code]
    out = []
    for p in chart["planets"]:
        vp = v["planets"][p["id"]]
        out.append(
            {
                "id": p["id"],
                "house": vp["house"],
                "sign_index": vp["sign_index"],
                "degree_in_sign": p["degree_in_sign"] if code == "D1" else None,
                "retrograde": p["retrograde"],
            }
        )
    return v["lagna_sign_index"], out


def layout(
    chart: dict[str, Any], code: str, style: str, names: dict[str, Any], asc_label: str, title: str = ""
) -> tuple[str, list[Label]]:
    lagna, planets = varga_planets(chart, code)
    abbr = names["planet_abbr"]
    if style == "south":
        return south_layout(lagna, planets, abbr, list(names["sign_short"].values()), asc_label, title)
    return north_layout(lagna, planets, abbr, asc_label)


def draw(chart: dict[str, Any], code: str, style: str, names: dict[str, Any], asc_label: str, title: str = "") -> str:
    """HTML block: SVG lines with absolutely positioned HTML labels."""
    lines, labels = layout(chart, code, style, names, asc_label, title)
    spans = []
    for lb in labels:
        shift = {"middle": "-50%", "start": "0", "end": "-100%"}[lb.anchor]
        spans.append(
            f'<span class="k-{lb.kind}" style="left:{lb.x / SIZE * 100:.2f}%;top:{lb.y / SIZE * 100:.2f}%;'
            f'transform:translate({shift},-50%)">{escape(lb.text)}</span>'
        )
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" aria-hidden="true">{lines}</svg>'
    return f'<div class="kundli">{svg}{"".join(spans)}</div>'

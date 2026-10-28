"""Birthplace search (US-14) over GeoNames cities (population >= 1000).

Data: GeoNames (CC BY 4.0) via the geonamescache package. Run
`uv run python -m jyotish_api.services.places` once to load it; the API
container does this automatically when the table is empty.
"""

import json
import os
import sys
from typing import Any

from sqlalchemy import case, func, insert, or_, select, text
from sqlalchemy.orm import Session

from jyotish_api.models import Place

# GeoNames admin1 codes for India (checked against the largest city in each).
INDIA_ADMIN1 = {
    "01": "Andaman and Nicobar Islands", "02": "Andhra Pradesh", "03": "Assam", "05": "Chandigarh",
    "07": "Delhi", "09": "Gujarat", "10": "Haryana", "11": "Himachal Pradesh", "12": "Jammu and Kashmir",
    "13": "Kerala", "14": "Lakshadweep", "16": "Maharashtra", "17": "Manipur", "18": "Meghalaya",
    "19": "Karnataka", "20": "Nagaland", "21": "Odisha", "22": "Puducherry", "23": "Punjab",
    "24": "Rajasthan", "25": "Tamil Nadu", "26": "Tripura", "28": "West Bengal", "29": "Sikkim",
    "30": "Arunachal Pradesh", "31": "Mizoram", "33": "Goa", "34": "Bihar", "35": "Madhya Pradesh",
    "36": "Uttar Pradesh", "37": "Chhattisgarh", "38": "Jharkhand", "39": "Uttarakhand", "40": "Telangana",
    "41": "Ladakh", "52": "Dadra and Nagar Haveli and Daman and Diu",
}  # fmt: skip


def _is_deva(s: str) -> bool:
    return any("ऀ" <= ch <= "ॿ" for ch in s)


def rows_from_geonames(min_population: int = 1000) -> list[dict[str, Any]]:
    import geonamescache

    base = os.path.join(os.path.dirname(geonamescache.__file__), "data")
    with open(os.path.join(base, "cities1000.json"), encoding="utf-8") as f:
        cities = json.load(f)
    with open(os.path.join(base, "countries.json"), encoding="utf-8") as f:
        countries = {c["iso"]: c["name"] for c in json.load(f).values()}
    with open(os.path.join(base, "us_states.json"), encoding="utf-8") as f:
        us_states = {s["code"]: s["name"] for s in json.load(f).values()}

    rows = []
    for c in cities.values():
        if c.get("population", 0) < min_population or not c.get("timezone"):
            continue
        cc = c["countrycode"]
        admin1 = INDIA_ADMIN1.get(c["admin1code"]) if cc == "IN" else us_states.get(c["admin1code"]) if cc == "US" else None
        alts = [a for a in c.get("alternatenames", []) if a]
        deva = next((a for a in alts if _is_deva(a)), None)
        names = {c["name"].lower()} | {a.lower() for a in alts if len(a) <= 60}
        rows.append(
            {
                "id": c["geonameid"],
                "name": c["name"][:200],
                "ascii_name": _ascii(c["name"])[:200],
                "name_deva": deva[:200] if deva else None,
                "search": "|" + "|".join(sorted(names)) + "|",
                "admin1": admin1,
                "country_code": cc,
                "country": countries.get(cc, cc),
                "latitude": c["latitude"],
                "longitude": c["longitude"],
                "tz": c["timezone"],
                "population": c.get("population", 0),
            }
        )
    return rows


def _ascii(s: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def seed(db: Session, force: bool = False) -> int:
    if not force and db.scalar(select(func.count()).select_from(Place)):
        return 0
    db.execute(text("TRUNCATE places"))
    rows = rows_from_geonames()
    for i in range(0, len(rows), 5000):
        db.execute(insert(Place), rows[i : i + 5000])
    db.commit()
    return len(rows)


def search(db: Session, q: str, limit: int = 10) -> list[dict[str, Any]]:
    q = q.strip().lower()
    if len(q) < 2:
        return []
    like = q.replace("%", "").replace("_", "") + "%"
    stmt = (
        select(Place)
        .where(or_(func.lower(Place.ascii_name).like(like), func.lower(Place.name).like(like), Place.search.like("%|" + like)))
        .order_by(
            case((or_(func.lower(Place.ascii_name).like(like), func.lower(Place.name).like(like)), 0), else_=1),
            Place.population.desc(),
        )
        .limit(limit)
    )
    return [place_out(p) for p in db.scalars(stmt)]


def place_out(p: Place) -> dict[str, Any]:
    label = ", ".join(x for x in (p.name, p.admin1, p.country) if x)
    return {
        "id": p.id,
        "name": p.name,
        "name_deva": p.name_deva,
        "admin1": p.admin1,
        "country": p.country,
        "country_code": p.country_code,
        "label": label,
        "latitude": p.latitude,
        "longitude": p.longitude,
        "tz_name": p.tz,
        "population": p.population,
    }


if __name__ == "__main__":
    from jyotish_api.db import SessionLocal

    with SessionLocal() as s:
        n = seed(s, force="--force" in sys.argv)
        print(f"loaded {n} places" if n else "places already loaded (use --force to reload)")

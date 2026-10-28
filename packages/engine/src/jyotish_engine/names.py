"""Display names in English, Hindi and Marathi (shared by API, web and PDFs)."""

import json
from functools import cache
from pathlib import Path
from typing import Any

LANGS = ("en", "hi", "mr")


@cache
def all_names() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "names.json").read_text(encoding="utf-8"))


def names(lang: str) -> dict[str, Any]:
    return all_names().get(lang, all_names()["en"])

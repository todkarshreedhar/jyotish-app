"""Rule engine (US-40, US-41): interpretations written as YAML, no code.

A rule file is a list of rules. Each rule needs:
  id        unique, e.g. Y-GAJAKESARI
  topic     one of TOPICS
  kind      yoga | placement | dosha
  source    classical reference, e.g. "Phaladeepika ch. 6"
  when      a condition (see `evaluate`)
  text_key  key into the translation files (rules/texts/<lang>.yaml)

Conditions are data, never code. Supported forms:
  {all: [cond, ...]}  {any: [cond, ...]}  {not: cond}
  {in_house: {planet: mars, houses: [1, 4], from: lagna|moon|<planet>}}
  {dignity: {planet: jupiter, is: [exalted, own, moolatrikona]}}
  {conjunct: [sun, mercury]}
  {lord_in_house: {lord_of: 10, houses: [1, 4, 7, 10], from: lagna}}
  {lords_conjunct: {a: [1, 4, 7, 10], b: [1, 5, 9], distinct: true}}
  {any_planet_in_house: {houses: [2], from: moon, planets: [...]}}
  {no_planet_in_house: {houses: [2, 12], from: moon, planets: [...]}}
  {retrograde: planet}  {combust: planet}
  {all_between_nodes: true}
  {debilitated_with_cancellation: true}
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from jyotish_engine.constants import SIGN_LORDS, Graha
from jyotish_engine.core import house_from

RULES_DIR = Path(__file__).parent
TOPICS = ("personality", "career", "wealth", "family", "relationships", "health", "spirituality", "general")
KINDS = ("yoga", "placement", "dosha")
REQUIRED = ("id", "topic", "kind", "source", "when", "text_key")
RULESET_VERSION = "1.0.0"
PLANETS = {str(g) for g in Graha}


class RuleError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    id: str
    topic: str
    kind: str
    source: str
    when: dict[str, Any]
    text_key: str
    file: str
    line: int
    weight: int = 1


def _check_condition(cond: Any, where: str) -> None:
    if not isinstance(cond, dict) or len(cond) != 1:
        raise RuleError(f"{where}: a condition must be a mapping with exactly one key, got {cond!r}")
    (op, arg), = cond.items()
    if op in ("all", "any"):
        if not isinstance(arg, list) or not arg:
            raise RuleError(f"{where}: '{op}' needs a non-empty list")
        for c in arg:
            _check_condition(c, where)
    elif op == "not":
        _check_condition(arg, where)
    elif op in ("in_house", "any_planet_in_house", "no_planet_in_house"):
        if not isinstance(arg, dict) or "houses" not in arg:
            raise RuleError(f"{where}: '{op}' needs 'houses'")
        if op == "in_house" and arg.get("planet") not in PLANETS:
            raise RuleError(f"{where}: '{op}' has unknown planet {arg.get('planet')!r}")
        if not all(isinstance(h, int) and 1 <= h <= 12 for h in arg["houses"]):
            raise RuleError(f"{where}: houses must be 1..12")
    elif op == "dignity":
        if arg.get("planet") not in PLANETS or not arg.get("is"):
            raise RuleError(f"{where}: 'dignity' needs planet and is")
    elif op == "conjunct":
        if not isinstance(arg, list) or len(arg) < 2 or any(p not in PLANETS for p in arg):
            raise RuleError(f"{where}: 'conjunct' needs a list of 2+ planets")
    elif op == "lord_in_house":
        if not 1 <= int(arg.get("lord_of", 0)) <= 12 or "houses" not in arg:
            raise RuleError(f"{where}: 'lord_in_house' needs lord_of and houses")
    elif op == "lords_conjunct":
        if "a" not in arg or "b" not in arg:
            raise RuleError(f"{where}: 'lords_conjunct' needs a and b")
    elif op in ("retrograde", "combust"):
        if arg not in PLANETS:
            raise RuleError(f"{where}: '{op}' needs a planet")
    elif op in ("all_between_nodes", "debilitated_with_cancellation"):
        pass
    else:
        raise RuleError(f"{where}: unknown condition '{op}'")


def load_rules(directory: Path = RULES_DIR) -> list[Rule]:
    rules: list[Rule] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        try:
            node = yaml.compose(text, Loader=yaml.SafeLoader)
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise RuleError(f"{path.name}: invalid YAML: {exc}") from exc
        if not isinstance(data, list):
            raise RuleError(f"{path.name}: the file must be a list of rules")
        for item, item_node in zip(data, node.value, strict=True):  # type: ignore[union-attr]
            line = item_node.start_mark.line + 1
            where = f"{path.name}:{line}"
            if not isinstance(item, dict):
                raise RuleError(f"{where}: a rule must be a mapping")
            missing = [k for k in REQUIRED if k not in item]
            if missing:
                raise RuleError(f"{where}: rule {item.get('id', '?')} is missing {', '.join(missing)}")
            if item["id"] in seen:
                raise RuleError(f"{where}: duplicate rule id {item['id']}")
            if item["topic"] not in TOPICS:
                raise RuleError(f"{where}: unknown topic {item['topic']}")
            if item["kind"] not in KINDS:
                raise RuleError(f"{where}: unknown kind {item['kind']}")
            _check_condition(item["when"], where)
            seen.add(item["id"])
            rules.append(Rule(item["id"], item["topic"], item["kind"], item["source"], item["when"],
                              item["text_key"], path.name, line, int(item.get("weight", 1))))
    return rules


class Facts:
    """The view of a computed chart that rules can see."""

    def __init__(self, chart: dict[str, Any]):
        self.lagna = chart["lagna"]["sign_index"]
        self.p = {p["id"]: p for p in chart["planets"]}
        self.sign = {k: v["sign_index"] for k, v in self.p.items()}

    def ref_sign(self, ref: str) -> int:
        if ref == "lagna":
            return int(self.lagna)
        if ref in self.sign:
            return int(self.sign[ref])
        raise RuleError(f"unknown reference point {ref}")

    def house(self, planet: str, ref: str = "lagna") -> int:
        return house_from(self.sign[planet], self.ref_sign(ref))

    def lord_of(self, house: int, ref: str = "lagna") -> str:
        return str(SIGN_LORDS[(self.ref_sign(ref) + house - 1) % 12])


SEVEN = [str(g) for g in Graha][:7]


def evaluate(cond: dict[str, Any], f: Facts) -> bool:
    (op, arg), = cond.items()
    if op == "all":
        return all(evaluate(c, f) for c in arg)
    if op == "any":
        return any(evaluate(c, f) for c in arg)
    if op == "not":
        return not evaluate(arg, f)
    if op == "in_house":
        return f.house(arg["planet"], arg.get("from", "lagna")) in arg["houses"]
    if op == "any_planet_in_house":
        ref = arg.get("from", "lagna")
        pl = [p for p in arg.get("planets", SEVEN) if p != ref]
        return any(f.house(p, ref) in arg["houses"] for p in pl)
    if op == "no_planet_in_house":
        ref = arg.get("from", "lagna")
        pl = [p for p in arg.get("planets", SEVEN) if p != ref]
        return not any(f.house(p, ref) in arg["houses"] for p in pl)
    if op == "dignity":
        return f.p[arg["planet"]]["dignity"] in arg["is"]
    if op == "conjunct":
        return len({f.sign[p] for p in arg}) == 1
    if op == "lord_in_house":
        ref = arg.get("from", "lagna")
        lord = f.lord_of(int(arg["lord_of"]), ref)
        return f.house(lord, ref) in arg["houses"]
    if op == "lords_conjunct":
        a = {f.lord_of(h) for h in arg["a"]}
        b = {f.lord_of(h) for h in arg["b"]}
        for x in a:
            for y in b:
                if x == y and arg.get("distinct", True):
                    continue
                if f.sign[x] == f.sign[y]:
                    return True
        return False
    if op == "retrograde":
        return bool(f.p[arg]["retrograde"])
    if op == "combust":
        return bool(f.p[arg]["combust"])
    if op == "all_between_nodes":
        rahu = f.p["rahu"]["longitude"]
        others = [f.p[p]["longitude"] for p in SEVEN]
        side = [((lon - rahu) % 360) < 180 for lon in others]
        return all(side) or not any(side)
    if op == "debilitated_with_cancellation":
        # Neecha Bhanga (Phaladeepika ch. 7): a debilitated planet whose
        # dispositor, or the planet exalted in that sign, is in a kendra from
        # the Lagna or the Moon.
        from jyotish_engine.constants import EXALTATION

        for p in SEVEN:
            if f.p[p]["dignity"] != "debilitated":
                continue
            s = f.sign[p]
            helpers = {str(SIGN_LORDS[s])}
            helpers |= {str(g) for g, (es, _) in EXALTATION.items() if es == s and str(g) in SEVEN}
            for h in helpers:
                if f.house(h, "lagna") in (1, 4, 7, 10) or f.house(h, "moon") in (1, 4, 7, 10):
                    return True
        return False
    raise RuleError(f"unknown condition {op}")


def run_rules(chart: dict[str, Any], rules: list[Rule] | None = None) -> dict[str, Any]:
    rules = rules if rules is not None else load_rules()
    f = Facts(chart)
    fired = [
        {"id": r.id, "topic": r.topic, "kind": r.kind, "source": r.source, "text_key": r.text_key}
        for r in rules
        if evaluate(r.when, f)
    ]
    return {"ruleset_version": RULESET_VERSION, "count": len(fired), "results": fired}


_texts: dict[str, dict[str, Any]] = {}


def texts(lang: str) -> dict[str, Any]:
    if lang not in _texts:
        path = RULES_DIR / "texts" / f"{lang}.yaml"
        if not path.exists():
            path = RULES_DIR / "texts" / "en.yaml"
        _texts[lang] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _texts[lang]

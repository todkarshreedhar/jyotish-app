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

Shape (Nabhasa) and other forms; `planets` defaults to the seven planets
Sun to Saturn, and `from` to the Lagna:
  {planets_within: {houses: [1, 7], occupy_all: true}}   all planets in these houses
  {consecutive: {length: 7, start: [1]}}                  all planets in a run of houses, each occupied
  {houses_occupied: {houses: [1, 4, 7, 10]}}              every listed house has a planet
  {sign_type: {type: movable|fixed|dual}}                 all planets in that kind of sign
  {lagna_sign_type: fixed}
  {occupied_signs: {count: [7]}}                          how many signs the planets occupy
  {max_in_one_sign: {min: 4}}
  {exchange: {a: [9], b: [10]}}                           sign exchange (parivartana) between lords
  {lord_dignity: {lord_of: 9, is: [exalted, own]}}
  {lords_relation: {a: 5, b: 6, houses: [1, 4, 7, 10]}}   lord of b counted from lord of a
  {aspects: {by: jupiter, to: moon|lagna|lord:1}}         full sign aspect (graha drishti)

A rule may carry `example`: sign numbers (1 = Aries) for lagna and planets,
used by the tests to show the rule fires (rare yogas never appear in a
sample of real charts).
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
RULESET_VERSION = "1.1.0"
PLANETS = {str(g) for g in Graha}
SEVEN = [str(g) for g in Graha][:7]
SIGN_TYPES = {"movable": 0, "fixed": 1, "dual": 2}
# Special aspects in houses counted from the planet; every planet aspects the 7th.
ASPECTS = {"mars": (4, 7, 8), "jupiter": (5, 7, 9), "saturn": (3, 7, 10)}


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
    example: dict[str, int] | None = None


def _check_condition(cond: Any, where: str) -> None:
    if not isinstance(cond, dict) or len(cond) != 1:
        raise RuleError(f"{where}: a condition must be a mapping with exactly one key, got {cond!r}")
    ((op, arg),) = cond.items()
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
    elif op in ("planets_within", "houses_occupied"):
        if not isinstance(arg, dict) or not arg.get("houses"):
            raise RuleError(f"{where}: '{op}' needs 'houses'")
        _check_planets(arg.get("planets", SEVEN), where)
        if not all(isinstance(h, int) and 1 <= h <= 12 for h in arg["houses"]):
            raise RuleError(f"{where}: houses must be 1..12")
    elif op == "consecutive":
        if not 1 <= int(arg.get("length", 0)) <= 12 or not arg.get("start"):
            raise RuleError(f"{where}: 'consecutive' needs length and start")
    elif op == "sign_type":
        if arg.get("type") not in SIGN_TYPES:
            raise RuleError(f"{where}: 'sign_type' needs type movable, fixed or dual")
        _check_planets(arg.get("planets", SEVEN), where)
    elif op == "lagna_sign_type":
        if arg not in SIGN_TYPES:
            raise RuleError(f"{where}: 'lagna_sign_type' must be movable, fixed or dual")
    elif op == "occupied_signs":
        if not arg.get("count"):
            raise RuleError(f"{where}: 'occupied_signs' needs count")
    elif op == "max_in_one_sign":
        if not 1 <= int(arg.get("min", 0)) <= 9:
            raise RuleError(f"{where}: 'max_in_one_sign' needs min")
    elif op == "exchange":
        if not arg.get("a") or not arg.get("b"):
            raise RuleError(f"{where}: 'exchange' needs a and b")
    elif op == "lord_dignity":
        if not 1 <= int(arg.get("lord_of", 0)) <= 12 or not arg.get("is"):
            raise RuleError(f"{where}: 'lord_dignity' needs lord_of and is")
    elif op == "lords_relation":
        if not (1 <= int(arg.get("a", 0)) <= 12 and 1 <= int(arg.get("b", 0)) <= 12) or not arg.get("houses"):
            raise RuleError(f"{where}: 'lords_relation' needs a, b and houses")
    elif op == "aspects":
        if arg.get("by") not in SEVEN or not arg.get("to"):
            raise RuleError(f"{where}: 'aspects' needs by (Sun to Saturn) and to")
    else:
        raise RuleError(f"{where}: unknown condition '{op}'")


def _check_example(ex: Any, where: str) -> dict[str, int] | None:
    if ex is None:
        return None
    if not isinstance(ex, dict) or "lagna" not in ex or any(k != "lagna" and k not in PLANETS for k in ex):
        raise RuleError(f"{where}: 'example' needs lagna and planet sign numbers")
    if not all(isinstance(v, int) and 1 <= v <= 12 for v in ex.values()):
        raise RuleError(f"{where}: example sign numbers must be 1..12")
    return {k: int(v) for k, v in ex.items()}


def _check_planets(planets: Any, where: str) -> None:
    if not isinstance(planets, list) or not planets or any(p not in PLANETS for p in planets):
        raise RuleError(f"{where}: unknown planet in {planets!r}")


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
        for item, item_node in zip(data, node.value, strict=True):
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
            rules.append(
                Rule(
                    item["id"],
                    item["topic"],
                    item["kind"],
                    item["source"],
                    item["when"],
                    item["text_key"],
                    path.name,
                    line,
                    int(item.get("weight", 1)),
                    _check_example(item.get("example"), where),
                )
            )
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


def evaluate(cond: dict[str, Any], f: Facts) -> bool:
    ((op, arg),) = cond.items()
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
    if op == "planets_within":
        ref = arg.get("from", "lagna")
        hs = [f.house(p, ref) for p in arg.get("planets", SEVEN)]
        if not all(h in arg["houses"] for h in hs):
            return False
        return not arg.get("occupy_all") or set(arg["houses"]) <= set(hs)
    if op == "consecutive":
        ref = arg.get("from", "lagna")
        run_hs = {f.house(p, ref) for p in arg.get("planets", SEVEN)}
        n = int(arg["length"])
        return any(run_hs == {(int(s0) - 1 + i) % 12 + 1 for i in range(n)} for s0 in arg["start"])
    if op == "houses_occupied":
        ref = arg.get("from", "lagna")
        occupied = {f.house(p, ref) for p in arg.get("planets", SEVEN) if p != ref}
        return set(arg["houses"]) <= occupied
    if op == "sign_type":
        t = SIGN_TYPES[arg["type"]]
        return all(f.sign[p] % 3 == t for p in arg.get("planets", SEVEN))
    if op == "lagna_sign_type":
        return int(f.lagna) % 3 == SIGN_TYPES[arg]
    if op == "occupied_signs":
        return len({f.sign[p] for p in arg.get("planets", SEVEN)}) in arg["count"]
    if op == "max_in_one_sign":
        signs = [f.sign[p] for p in arg.get("planets", SEVEN)]
        return max(signs.count(s) for s in signs) >= int(arg["min"])
    if op == "exchange":
        # Planet X sits in a sign of Y and Y in a sign of X (X != Y): the
        # houses of those two signs exchange lords.
        for x in SEVEN:
            y = str(SIGN_LORDS[f.sign[x]])
            if y == x or str(SIGN_LORDS[f.sign[y]]) != x:
                continue
            hx, hy = f.house(x), f.house(y)
            if (hx in arg["a"] and hy in arg["b"]) or (hx in arg["b"] and hy in arg["a"]):
                return True
        return False
    if op == "lord_dignity":
        lord = f.lord_of(int(arg["lord_of"]), arg.get("from", "lagna"))
        return f.p[lord]["dignity"] in arg["is"]
    if op == "lords_relation":
        la, lb = f.lord_of(int(arg["a"])), f.lord_of(int(arg["b"]))
        return f.house(lb, la) in arg["houses"]
    if op == "aspects":
        by = arg["by"]
        to = str(arg["to"])
        target = int(f.lagna) if to == "lagna" else f.sign[f.lord_of(int(to[5:]))] if to.startswith("lord:") else f.sign[to]
        return house_from(target, f.sign[by]) in ASPECTS.get(by, (7,))
    raise RuleError(f"unknown condition {op}")


def example_chart(ex: dict[str, int]) -> dict[str, Any]:
    """A minimal chart from a rule's `example` (sign numbers, 1 = Aries)."""
    from jyotish_engine.constants import Graha as G
    from jyotish_engine.core import dignity

    signs = {g: ex.get(str(g), 0) - 1 for g in G}
    # Unlisted planets: nodes opposite each other, the rest with the Sun.
    if signs[G.RAHU] < 0:
        signs[G.RAHU] = (signs[G.KETU] + 6) % 12 if signs[G.KETU] >= 0 else 2
    if signs[G.KETU] < 0:
        signs[G.KETU] = (signs[G.RAHU] + 6) % 12
    for g in G:
        if signs[g] < 0:
            signs[g] = max(signs[G.SUN], 0)
    planets = []
    for g, s in signs.items():
        lon = s * 30 + 15.0
        planets.append(
            {
                "id": str(g),
                "sign_index": s,
                "longitude": lon,
                "dignity": dignity(g, lon, signs),
                "retrograde": False,
                "combust": False,
            }
        )
    return {"lagna": {"sign_index": ex["lagna"] - 1}, "planets": planets}


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

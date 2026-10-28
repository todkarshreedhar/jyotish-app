"""Chart settings. Every chart result stores the settings it was made with."""

from dataclasses import asdict, dataclass
from enum import StrEnum

import swisseph as swe


class Ayanamsa(StrEnum):
    LAHIRI = "lahiri"
    RAMAN = "raman"
    KRISHNAMURTI = "krishnamurti"
    YUKTESHWAR = "yukteshwar"
    TRUE_CHITRAPAKSHA = "true_chitrapaksha"


AYANAMSA_SWE: dict[Ayanamsa, int] = {
    Ayanamsa.LAHIRI: swe.SIDM_LAHIRI,
    Ayanamsa.RAMAN: swe.SIDM_RAMAN,
    Ayanamsa.KRISHNAMURTI: swe.SIDM_KRISHNAMURTI,
    Ayanamsa.YUKTESHWAR: swe.SIDM_YUKTESHWAR,
    Ayanamsa.TRUE_CHITRAPAKSHA: swe.SIDM_TRUE_CITRA,
}


class NodeType(StrEnum):
    MEAN = "mean"
    TRUE = "true"


class ChartStyle(StrEnum):
    NORTH = "north"
    SOUTH = "south"


DASHA_YEAR_SAVANA = 365.25
DASHA_YEAR_TROPICAL = 365.2422
ALLOWED_DASHA_YEARS = (DASHA_YEAR_SAVANA, DASHA_YEAR_TROPICAL)


@dataclass(frozen=True, slots=True)
class ChartSettings:
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    node_type: NodeType = NodeType.MEAN
    house_system: str = "whole_sign"
    dasha_year_days: float = DASHA_YEAR_SAVANA
    chart_style: ChartStyle = ChartStyle.NORTH

    def __post_init__(self) -> None:
        if self.dasha_year_days not in ALLOWED_DASHA_YEARS:
            raise ValueError(f"dasha_year_days must be one of {ALLOWED_DASHA_YEARS}")
        if self.house_system != "whole_sign":
            raise ValueError("only whole_sign houses are supported (Bhava Chalit is extra)")

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        return {k: (str(v) if isinstance(v, StrEnum) else v) for k, v in d.items()}

    @classmethod
    def from_dict(cls, d: dict[str, object] | None) -> "ChartSettings":
        d = dict(d or {})
        return cls(
            ayanamsa=Ayanamsa(str(d.get("ayanamsa", Ayanamsa.LAHIRI))),
            node_type=NodeType(str(d.get("node_type", NodeType.MEAN))),
            house_system=str(d.get("house_system", "whole_sign")),
            dasha_year_days=float(d.get("dasha_year_days", DASHA_YEAR_SAVANA)),  # type: ignore[arg-type]
            chart_style=ChartStyle(str(d.get("chart_style", ChartStyle.NORTH))),
        )

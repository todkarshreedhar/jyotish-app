"""Request and response shapes shared by the routers."""

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from jyotish_engine.settings import ALLOWED_DASHA_YEARS, Ayanamsa, ChartStyle, NodeType

MIN_DATE = date(1800, 1, 1)
MAX_DATE = date(2399, 12, 31)
VARGA_CODES = ("D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60")
Lang = Literal["en", "hi", "mr"]


class SettingsIn(BaseModel):
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    node_type: NodeType = NodeType.MEAN
    chart_style: ChartStyle = ChartStyle.NORTH
    dasha_year_days: float = 365.25

    @field_validator("dasha_year_days")
    @classmethod
    def _year(cls, v: float) -> float:
        if v not in ALLOWED_DASHA_YEARS:
            raise ValueError(f"must be one of {ALLOWED_DASHA_YEARS}")
        return v


class BirthIn(BaseModel):
    birth_date: date
    birth_time: time
    time_accuracy: Literal["exact", "approximate", "unknown"] = "exact"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    place_name: str | None = Field(default=None, max_length=300)
    tz_name: str | None = Field(default=None, max_length=64)
    utc_offset_minutes: int | None = Field(default=None, ge=-14 * 60, le=14 * 60)

    @field_validator("birth_date")
    @classmethod
    def _range(cls, v: date) -> date:
        if not MIN_DATE <= v <= MAX_DATE:
            raise ValueError("birth date must be between 1800 and 2399")
        return v


class ProfileIn(BirthIn):
    name: str = Field(min_length=1, max_length=100)
    gender: Literal["male", "female", "other"] | None = None
    folder: str | None = Field(default=None, max_length=100)
    settings: SettingsIn = SettingsIn()
    is_main: bool = False


class ProfileOut(BaseModel):
    id: str
    name: str
    birth_date: date
    birth_time: time
    time_accuracy: str
    latitude: float
    longitude: float
    place_name: str | None
    tz_name: str | None
    utc_offset_minutes: int | None
    gender: str | None
    folder: str | None
    settings: SettingsIn
    is_main: bool
    created_at: str
    updated_at: str


class ChartRequest(BaseModel):
    birth: BirthIn
    settings: SettingsIn = SettingsIn()
    vargas: list[str] = ["D1", "D9"]
    bhava_chalit: bool = False
    lang: Lang = "en"

    @model_validator(mode="after")
    def _vargas(self) -> "ChartRequest":
        bad = [v for v in self.vargas if v not in VARGA_CODES]
        if bad:
            raise ValueError(f"unknown divisional charts: {bad}")
        return self


class MatchRequest(BaseModel):
    boy_profile_id: str
    girl_profile_id: str
    lang: Lang = "en"

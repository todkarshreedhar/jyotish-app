"""Step 1-3 of the pipeline: local birth time -> UTC -> Julian Day (UT).

Historical offsets come from the IANA time zone database (zoneinfo), which
knows, for example, India's war-time UTC+06:30 (1942-1945) and the old
Bombay/Calcutta times.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe


class InputError(ValueError):
    """Raised when birth details cannot be turned into a valid moment."""


@dataclass(frozen=True, slots=True)
class BirthMoment:
    local: datetime  # aware, in the birth time zone
    utc: datetime
    jd_ut: float
    tz_name: str | None
    utc_offset_minutes: int


def validate_location(latitude: float, longitude: float) -> None:
    if not -90.0 <= latitude <= 90.0:
        raise InputError(f"latitude {latitude} is outside -90..90")
    if not -180.0 <= longitude <= 180.0:
        raise InputError(f"longitude {longitude} is outside -180..180")
    if abs(latitude) > 66.5:
        # Whole-sign houses work, but Bhava cusps and sunrise become unreliable.
        pass


def to_moment(
    birth_date: date,
    birth_time: time,
    tz_name: str | None = None,
    utc_offset_minutes: int | None = None,
) -> BirthMoment:
    """Convert a local civil time to UTC and Julian Day.

    Either an IANA zone name (preferred, handles history) or a fixed UTC offset
    must be given. Times that do not exist (spring-forward gap) raise; times
    that happen twice (fall-back) use the first occurrence (fold=0).
    """
    naive = datetime.combine(birth_date, birth_time.replace(tzinfo=None))
    if tz_name:
        try:
            zone = ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise InputError(f"unknown time zone '{tz_name}'") from exc
        local = naive.replace(tzinfo=zone, fold=0)
        # Detect non-existent local times: round-trip through UTC.
        back = local.astimezone(UTC).astimezone(zone)
        if back.replace(tzinfo=None) != naive:
            raise InputError(f"{naive.isoformat()} does not exist in {tz_name} (clock change)")
    elif utc_offset_minutes is not None:
        if not -14 * 60 <= utc_offset_minutes <= 14 * 60:
            raise InputError("UTC offset must be between -14:00 and +14:00")
        from datetime import timezone

        local = naive.replace(tzinfo=timezone(timedelta(minutes=utc_offset_minutes)))
    else:
        raise InputError("a time zone name or a UTC offset is required")

    utc = local.astimezone(UTC)
    offset = local.utcoffset()
    assert offset is not None
    return BirthMoment(
        local=local,
        utc=utc,
        jd_ut=julian_day_ut(utc),
        tz_name=tz_name,
        utc_offset_minutes=int(offset.total_seconds() // 60),
    )


def julian_day_ut(utc: datetime) -> float:
    """Julian Day (UT) for an aware UTC datetime, Gregorian calendar."""
    if utc.tzinfo is None:
        raise InputError("datetime must be timezone-aware")
    u = utc.astimezone(UTC)
    hours = u.hour + u.minute / 60 + (u.second + u.microsecond / 1e6) / 3600
    return float(swe.julday(u.year, u.month, u.day, hours, swe.GREG_CAL))


def jd_to_utc(jd_ut: float) -> datetime:
    y, m, d, h = swe.revjul(jd_ut, swe.GREG_CAL)
    base = datetime(y, m, d, tzinfo=UTC)
    # round to the nearest second for stable output
    return base + timedelta(seconds=round(h * 3600))

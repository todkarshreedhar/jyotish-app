"""Jyotish calculation engine.

Rule: this package never touches a database, the network or the clock.
"""

import swisseph as swe

from jyotish_engine.version import ENGINE_VERSION

__all__ = ["ENGINE_VERSION", "engine_info"]


def engine_info() -> dict[str, str]:
    """Return the versions every chart result will record in its meta block."""
    return {
        "engine_version": ENGINE_VERSION,
        "swiss_ephemeris_version": swe.version,
    }

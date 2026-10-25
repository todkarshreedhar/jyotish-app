"""Jyotish calculation engine.

Rule: this package never touches a database, the network or the clock.
"""

import swisseph as swe

ENGINE_VERSION = "0.1.0"


def engine_info() -> dict[str, str]:
    """Return the versions every chart result will record in its meta block."""
    return {
        "engine_version": ENGINE_VERSION,
        "swiss_ephemeris_version": swe.version,
    }
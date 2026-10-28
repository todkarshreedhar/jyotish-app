"""Fixed Jyotish tables: signs, grahas, Nakshatras and their lords.

Everything here is classical reference data (BPHS and standard practice).
Names are given as stable English keys; translations live in `names.py`.
"""

from enum import StrEnum

import swisseph as swe


class Graha(StrEnum):
    SUN = "sun"
    MOON = "moon"
    MARS = "mars"
    MERCURY = "mercury"
    JUPITER = "jupiter"
    VENUS = "venus"
    SATURN = "saturn"
    RAHU = "rahu"
    KETU = "ketu"


# Order used everywhere (tables, JSON output, PDFs).
GRAHAS: tuple[Graha, ...] = tuple(Graha)
SEVEN_GRAHAS: tuple[Graha, ...] = GRAHAS[:7]

SWE_IDS: dict[Graha, int] = {
    Graha.SUN: swe.SUN,
    Graha.MOON: swe.MOON,
    Graha.MARS: swe.MARS,
    Graha.MERCURY: swe.MERCURY,
    Graha.JUPITER: swe.JUPITER,
    Graha.VENUS: swe.VENUS,
    Graha.SATURN: swe.SATURN,
}

# Signs are numbered 0..11 internally (0 = Aries/Mesha).
SIGNS: tuple[str, ...] = (
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
)

SIGN_LORDS: tuple[Graha, ...] = (
    Graha.MARS,
    Graha.VENUS,
    Graha.MERCURY,
    Graha.MOON,
    Graha.SUN,
    Graha.MERCURY,
    Graha.VENUS,
    Graha.MARS,
    Graha.JUPITER,
    Graha.SATURN,
    Graha.SATURN,
    Graha.JUPITER,
)

NAKSHATRAS: tuple[str, ...] = (
    "ashwini",
    "bharani",
    "krittika",
    "rohini",
    "mrigashira",
    "ardra",
    "punarvasu",
    "pushya",
    "ashlesha",
    "magha",
    "purva_phalguni",
    "uttara_phalguni",
    "hasta",
    "chitra",
    "swati",
    "vishakha",
    "anuradha",
    "jyeshtha",
    "mula",
    "purva_ashadha",
    "uttara_ashadha",
    "shravana",
    "dhanishta",
    "shatabhisha",
    "purva_bhadrapada",
    "uttara_bhadrapada",
    "revati",
)

NAKSHATRA_SPAN = 360.0 / 27.0  # 13°20'
PADA_SPAN = NAKSHATRA_SPAN / 4.0  # 3°20'

# Vimshottari cycle: lord sequence and years (total 120).
VIMSHOTTARI_ORDER: tuple[Graha, ...] = (
    Graha.KETU,
    Graha.VENUS,
    Graha.SUN,
    Graha.MOON,
    Graha.MARS,
    Graha.RAHU,
    Graha.JUPITER,
    Graha.SATURN,
    Graha.MERCURY,
)
VIMSHOTTARI_YEARS: dict[Graha, int] = {
    Graha.KETU: 7,
    Graha.VENUS: 20,
    Graha.SUN: 6,
    Graha.MOON: 10,
    Graha.MARS: 7,
    Graha.RAHU: 18,
    Graha.JUPITER: 16,
    Graha.SATURN: 19,
    Graha.MERCURY: 17,
}

# Nakshatra lords repeat the Vimshottari order three times from Ashwini.
NAKSHATRA_LORDS: tuple[Graha, ...] = tuple(VIMSHOTTARI_ORDER[i % 9] for i in range(27))

# Dignity tables (BPHS ch. 3). Degrees are within the sign.
EXALTATION: dict[Graha, tuple[int, float]] = {
    Graha.SUN: (0, 10.0),
    Graha.MOON: (1, 3.0),
    Graha.MARS: (9, 28.0),
    Graha.MERCURY: (5, 15.0),
    Graha.JUPITER: (3, 5.0),
    Graha.VENUS: (11, 27.0),
    Graha.SATURN: (6, 20.0),
    # Rahu/Ketu exaltation varies between authorities; we follow the common
    # BPHS reading (Rahu in Taurus, Ketu in Scorpio).
    Graha.RAHU: (1, 20.0),
    Graha.KETU: (7, 20.0),
}

# Moolatrikona: sign and degree range [start, end).
MOOLATRIKONA: dict[Graha, tuple[int, float, float]] = {
    Graha.SUN: (4, 0.0, 20.0),
    Graha.MOON: (1, 3.0, 30.0),
    Graha.MARS: (0, 0.0, 12.0),
    Graha.MERCURY: (5, 15.0, 20.0),
    Graha.JUPITER: (8, 0.0, 10.0),
    Graha.VENUS: (6, 0.0, 15.0),
    Graha.SATURN: (10, 0.0, 20.0),
}

OWN_SIGNS: dict[Graha, tuple[int, ...]] = {
    Graha.SUN: (4,),
    Graha.MOON: (3,),
    Graha.MARS: (0, 7),
    Graha.MERCURY: (2, 5),
    Graha.JUPITER: (8, 11),
    Graha.VENUS: (1, 6),
    Graha.SATURN: (9, 10),
    Graha.RAHU: (10,),
    Graha.KETU: (7,),
}

# Natural relationships (BPHS ch. 3): friends, neutrals; the rest are enemies.
NATURAL_FRIENDS: dict[Graha, frozenset[Graha]] = {
    Graha.SUN: frozenset({Graha.MOON, Graha.MARS, Graha.JUPITER}),
    Graha.MOON: frozenset({Graha.SUN, Graha.MERCURY}),
    Graha.MARS: frozenset({Graha.SUN, Graha.MOON, Graha.JUPITER}),
    Graha.MERCURY: frozenset({Graha.SUN, Graha.VENUS}),
    Graha.JUPITER: frozenset({Graha.SUN, Graha.MOON, Graha.MARS}),
    Graha.VENUS: frozenset({Graha.MERCURY, Graha.SATURN}),
    Graha.SATURN: frozenset({Graha.MERCURY, Graha.VENUS}),
}
NATURAL_NEUTRALS: dict[Graha, frozenset[Graha]] = {
    Graha.SUN: frozenset({Graha.MERCURY}),
    Graha.MOON: frozenset({Graha.MARS, Graha.JUPITER, Graha.VENUS, Graha.SATURN}),
    Graha.MARS: frozenset({Graha.VENUS, Graha.SATURN}),
    Graha.MERCURY: frozenset({Graha.MARS, Graha.JUPITER, Graha.SATURN}),
    Graha.JUPITER: frozenset({Graha.SATURN}),
    Graha.VENUS: frozenset({Graha.MARS, Graha.JUPITER}),
    Graha.SATURN: frozenset({Graha.JUPITER}),
}

# Default combustion orbs in degrees (Surya Siddhanta values as used in most
# Jyotish software). Mercury and Venus use smaller orbs when retrograde.
COMBUSTION_ORBS: dict[Graha, float] = {
    Graha.MOON: 12.0,
    Graha.MARS: 17.0,
    Graha.MERCURY: 14.0,
    Graha.JUPITER: 11.0,
    Graha.VENUS: 10.0,
    Graha.SATURN: 15.0,
}
COMBUSTION_ORBS_RETRO: dict[Graha, float] = {
    Graha.MERCURY: 12.0,
    Graha.VENUS: 8.0,
}

NATURAL_BENEFICS = frozenset({Graha.JUPITER, Graha.VENUS})
NATURAL_MALEFICS = frozenset({Graha.SUN, Graha.MARS, Graha.SATURN, Graha.RAHU, Graha.KETU})

WEEKDAY_LORDS: tuple[Graha, ...] = (
    Graha.SUN,
    Graha.MOON,
    Graha.MARS,
    Graha.MERCURY,
    Graha.JUPITER,
    Graha.VENUS,
    Graha.SATURN,
)

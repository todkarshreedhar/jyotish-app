# ADR 0002: Swiss Ephemeris under the AGPL

- **Status:** Accepted
- **Date:** 2026-10-28

## Context

Accuracy is the first priority. The Swiss Ephemeris is the standard library for astrological calculations and has good Python bindings (pyswisseph). It is dual licensed: AGPL for free use, or a paid professional licence for closed source products.

## Decision

The whole project is open source under the AGPL-3.0, so the Swiss Ephemeris is used free of charge. The default ayanamsa is Lahiri (`SE_SIDM_LAHIRI`). The ephemeris files `sepl_18`, `semo_18` and `seas_18` ship with the engine and cover 1800 to 2399, which is also the allowed range for birth dates.

The product owner may revisit this (paid licence, or Skyfield with JPL data) if the code must become closed source.

## Consequences

- Anyone who runs a modified version as a network service must offer its source. The web footer links to the repository.
- Calculations are checked against an independent source (JPL DE421 through Skyfield) so we do not depend on trusting one library.
- The C library keeps settings per thread, so the engine sets the ephemeris path in every thread (see `ephemeris.py`).

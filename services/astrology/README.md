# Nakshatra AI astrology calculation service

FastAPI service for deterministic sidereal chart calculations. It does not use a language model.

## Licensing and ephemeris data

This service uses `pyswisseph` 2.10.3.2, the Python binding to Swiss Ephemeris. The Python package is distributed under **GNU Affero General Public License v3 (AGPL-3.0)**; the Swiss Ephemeris itself is dual-licensed. Review the binding's license and Swiss Ephemeris licensing terms before distributing or operating a network service. Obtain and comply with the applicable commercial license if AGPL terms do not fit your use.

Swiss Ephemeris `.se1` data files are not included. Set `SE_EPHE_PATH` to an operator-provided directory containing the required files. Without files, Swiss Ephemeris falls back to its built-in Moshier ephemeris; that fallback is returned as `ephemeris_source: "moshier_fallback"` and logged. Set `NAKSHATRA_REQUIRE_SWISSEPH=1` to reject calculations unless Swiss Ephemeris files are available. The response records the ephemeris library version and actual source.

## Setup

Python 3.11 or newer is required. Python 3.11 is recommended on Windows because the pinned `pyswisseph` release provides a prebuilt Windows wheel for that version; newer Windows Python versions may need a Visual C++ build toolchain to compile the binding.

```powershell
Set-Location services\astrology
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

By default, the service persists calculation provenance and JSON output to a local SQLite database. Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL for a PostgreSQL deployment, for example `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB_NAME`. The database table is created on startup; production schema changes should be managed through migrations.

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/nakshatra"
$env:SE_EPHE_PATH = "C:\path\to\swisseph\ephe"
uvicorn app.main:app --reload
```

The endpoint is `POST /api/chart/calculate`; interactive OpenAPI documentation is available at `/docs`.

### Request

```json
{
  "birth_date": "1990-01-15",
  "birth_time": "12:30:00",
  "latitude": 19.076,
  "longitude": 72.8777,
  "timezone": "Asia/Kolkata",
  "ayanamsa": "lahiri",
  "node_type": "mean"
}
```

`timezone` must be an IANA timezone identifier. Latitude is geodetic degrees north; longitude is degrees east (negative west). The submitted date and time are interpreted as local civil time, then converted with IANA timezone rules to UTC. Nonexistent DST wall-times are rejected. Repeated wall-times require `fold: 0` (earlier occurrence) or `fold: 1` (later occurrence). Windows installations use the `tzdata` package; keep it current for historical timezone rule updates.

Supported ayanamsas: `lahiri` (default), `raman`, and `krishnamurti`. Supported nodes: `mean` (default) and `true`. Swiss Ephemeris calculations use geocentric apparent ecliptic positions and sidereal coordinates. Ketu is defined exactly 180 degrees from the selected Rahu longitude.

## Calculation conventions

- D1 houses use whole signs: the sidereal ascendant's sign is house 1; each subsequent zodiac sign is the next house. The ascendant's degree is the tropical ascendant from Swiss Ephemeris minus the selected ayanamsa.
- Nakshatras divide 360 degrees into 27 equal arcs of 13°20′, starting at 0° Aries; each pada is one quarter of an arc (3°20′). Nakshatra lords follow the repeating nine-lord Vimshottari sequence Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury.
- Tithi is derived from the Moon-Sun sidereal longitude difference (equivalent to their tropical elongation): each 12° is one tithi. The two 15-tithi pakshas are named Shukla and Krishna; the 15th is Purnima or Amavasya.
- D9 Navamsha divides each sign into nine equal 3°20′ parts. The first Navamsha begins from the sign itself for movable signs, the ninth sign from it for fixed signs, and the fifth sign from it for dual signs; successive parts advance through the zodiac.
- D10 Dashamsha divides each sign into ten equal 3° parts. Odd-numbered zodiac signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius) start from themselves; even-numbered signs start from the ninth sign from themselves. Successive parts advance through the zodiac.
- Divisional chart houses are whole-sign houses counted from that division's derived ascendant sign. Varga placement uses the degree within the sidereal D1 sign, without rounding before assigning the segment.

Retrograde status is based on geocentric ecliptic longitude speed from the ephemeris. The ascendant has no retrograde status. Ketu's speed/status follows the selected node.

## Tests

```powershell
python -m pytest
```

Reference fixtures in `tests\fixtures\jpl_horizons_reference.json` were generated independently with NASA/JPL Horizons geocentric vector ephemerides (JPL DE441), converted from the published J2000 ecliptic vectors to Lahiri sidereal longitude. The fixture records the raw X/Y vectors, query settings, conversion, and tolerance. Reference checks compare planetary positions, not derived astrology interpretations.

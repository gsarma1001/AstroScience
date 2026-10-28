from __future__ import annotations

import logging
import os
import threading
from datetime import date, datetime, time, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import swisseph as swe

from app.schemas import (
    Ayanamsa,
    ChartHouse,
    ChartProvenance,
    ChartPlacement,
    ChartRequest,
    ChartResponse,
    DivisionChart,
    NodeType,
    PlanetPosition,
)

ENGINE_VERSION = "0.1.0"
SIGNS = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)
NAKSHATRAS = (
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
)
VIMSHOTTARI_LORDS = (
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
)
AYANAMSA_MODES = {
    Ayanamsa.LAHIRI: swe.SIDM_LAHIRI,
    Ayanamsa.RAMAN: swe.SIDM_RAMAN,
    Ayanamsa.KRISHNAMURTI: swe.SIDM_KRISHNAMURTI,
}
PLANETS = {
    "sun": ("Sun", swe.SUN),
    "moon": ("Moon", swe.MOON),
    "mars": ("Mars", swe.MARS),
    "mercury": ("Mercury", swe.MERCURY),
    "jupiter": ("Jupiter", swe.JUPITER),
    "venus": ("Venus", swe.VENUS),
    "saturn": ("Saturn", swe.SATURN),
}
TITHIS = (
    "Pratipada",
    "Dwitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dwadashi",
    "Trayodashi",
    "Chaturdashi",
)

_EPHEMERIS_LOCK = threading.RLock()
_LOGGER = logging.getLogger(__name__)
swe.set_ephe_path(os.environ.get("SE_EPHE_PATH") or None)


class InvalidBirthTime(ValueError):
    pass


class EphemerisCalculationError(RuntimeError):
    pass


def _resolve_birth_datetime(
    birth_date: date, birth_time: time, timezone_id: str, fold: int | None
) -> datetime:
    try:
        zone = ZoneInfo(timezone_id)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise InvalidBirthTime(f"Unknown IANA timezone: {timezone_id}") from exc

    local_naive = datetime.combine(birth_date, birth_time)
    candidates: list[datetime] = []
    for candidate_fold in (0, 1):
        candidate = local_naive.replace(tzinfo=zone, fold=candidate_fold)
        if candidate.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) == local_naive:
            candidates.append(candidate)

    unique_offsets = {candidate.utcoffset() for candidate in candidates}
    if not candidates:
        raise InvalidBirthTime(
            "The local birth time does not exist in this timezone because of a clock change"
        )
    if len(unique_offsets) > 1 and fold is None:
        raise InvalidBirthTime(
            "The local birth time is ambiguous because of a clock change; provide fold 0 or 1"
        )
    if fold is not None:
        matching = next((candidate for candidate in candidates if candidate.fold == fold), None)
        if matching is None:
            raise InvalidBirthTime("The supplied fold is not valid for this local birth time")
        return matching.astimezone(timezone.utc)
    return candidates[0].astimezone(timezone.utc)


def _longitude_sign(longitude: float) -> tuple[str, int, float]:
    normalized = longitude % 360.0
    sign_index = int(normalized // 30.0)
    return SIGNS[sign_index], sign_index, normalized % 30.0


def _nakshatra_details(longitude: float) -> tuple[str, int, str]:
    normalized = longitude % 360.0
    segment_size = 360.0 / 27.0
    index = min(int(normalized / segment_size), 26)
    pada = min(int((normalized % segment_size) / (segment_size / 4.0)) + 1, 4)
    return NAKSHATRAS[index], pada, VIMSHOTTARI_LORDS[index % 9]


def _varga_sign(sign_index: int, degree_in_sign: float, division: int) -> int:
    """Map a sign-degree into D9/D10 using the classical Parashari sign-start rules."""
    segment = min(int(degree_in_sign / (30.0 / division)), division - 1)
    if division == 9:
        modality_offset = (0, 8, 4)[sign_index % 3]
        return (sign_index + modality_offset + segment) % 12
    if division == 10:
        start = sign_index if sign_index % 2 == 0 else (sign_index + 8) % 12
        return (start + segment) % 12
    raise ValueError(f"Unsupported divisional chart: D{division}")


def _make_division_chart(
    division_name: str,
    division: int,
    ascendant_longitude: float,
    positions: dict[str, float],
) -> DivisionChart:
    _, asc_sign_index, asc_degree = _longitude_sign(ascendant_longitude)
    varga_asc_sign_index = _varga_sign(asc_sign_index, asc_degree, division)
    occupants: list[list[str]] = [[] for _ in SIGNS]
    placements = [
        ChartPlacement(
            name="Ascendant",
            sign=SIGNS[varga_asc_sign_index],
            house=1,
            degree_in_sign=(asc_degree % (30.0 / division)) * division,
        )
    ]
    occupants[varga_asc_sign_index].append("Ascendant")
    for name, longitude in positions.items():
        _, sign_index, degree = _longitude_sign(longitude)
        varga_sign_index = _varga_sign(sign_index, degree, division)
        house = (varga_sign_index - varga_asc_sign_index) % 12 + 1
        occupants[varga_sign_index].append(name.title())
        placements.append(
            ChartPlacement(
                name=name.title(),
                sign=SIGNS[varga_sign_index],
                house=house,
                degree_in_sign=(degree % (30.0 / division)) * division,
            )
        )

    houses = []
    for house_number in range(1, 13):
        sign_index = (varga_asc_sign_index + house_number - 1) % 12
        houses.append(
            ChartHouse(
                number=house_number,
                sign=SIGNS[sign_index],
                occupants=occupants[sign_index],
            )
        )
    return DivisionChart(
        division=division_name,
        ascendant_sign=SIGNS[varga_asc_sign_index],
        houses=houses,
        placements=placements,
    )


def _tithi(sun_longitude: float, moon_longitude: float) -> dict[str, str | int | float]:
    elongation = (moon_longitude - sun_longitude) % 360.0
    tithi_number = min(int(elongation / 12.0) + 1, 30)
    if tithi_number <= 15:
        paksha = "Shukla"
        name = "Purnima" if tithi_number == 15 else TITHIS[tithi_number - 1]
    else:
        paksha = "Krishna"
        name = "Amavasya" if tithi_number == 30 else TITHIS[tithi_number - 16]
    return {
        "paksha": paksha,
        "number_in_paksha": ((tithi_number - 1) % 15) + 1,
        "name": name,
        "elongation_degrees": elongation,
    }


def calculate_chart(request: ChartRequest) -> ChartResponse:
    utc_birth = _resolve_birth_datetime(
        request.birth_date, request.birth_time, request.timezone, request.fold
    )
    with _EPHEMERIS_LOCK:
        swe.set_sid_mode(AYANAMSA_MODES[request.ayanamsa])
        _, julian_day_ut = swe.utc_to_jd(
            utc_birth.year,
            utc_birth.month,
            utc_birth.day,
            utc_birth.hour,
            utc_birth.minute,
            utc_birth.second + utc_birth.microsecond / 1_000_000.0,
            swe.GREG_CAL,
        )
        ayanamsa_degrees = swe.get_ayanamsa_ut(julian_day_ut)

        # Swiss Ephemeris exposes sidereal positions through process-global ayanamsa state.
        # Keep the sidereal planetary calculations and tropical ascendant under one lock.
        calc_flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        body_ids = {name: body_id for name, (_, body_id) in PLANETS.items()}
        node_id = swe.MEAN_NODE if request.node_type == NodeType.MEAN else swe.TRUE_NODE
        body_ids["rahu"] = node_id
        raw: dict[str, tuple[float, float, int]] = {}
        source = "swiss_ephemeris"
        for key, body_id in body_ids.items():
            try:
                coordinates, returned_flags = swe.calc_ut(julian_day_ut, body_id, calc_flags)
            except swe.Error as exc:
                raise EphemerisCalculationError(str(exc)) from exc
            if returned_flags & swe.FLG_SWIEPH:
                pass
            elif returned_flags & swe.FLG_MOSEPH:
                source = "moshier_fallback"
                if os.environ.get("NAKSHATRA_REQUIRE_SWISSEPH", "").lower() in {"1", "true", "yes"}:
                    raise EphemerisCalculationError(
                        "Swiss Ephemeris data files are unavailable; Moshier fallback is disabled"
                    )
                _LOGGER.warning(
                    "Swiss Ephemeris files unavailable; using the explicitly reported Moshier fallback"
                )
            else:
                raise EphemerisCalculationError(
                    f"Unexpected ephemeris flags returned for {key}: {returned_flags}"
                )
            raw[key] = (coordinates[0] % 360.0, coordinates[3], returned_flags)

        try:
            _, ascendant_data = swe.houses_ex(
                julian_day_ut, request.latitude, request.longitude, b"P"
            )
        except swe.Error as exc:
            raise EphemerisCalculationError(
                f"Unable to calculate the ascendant at these coordinates and time: {exc}"
            ) from exc
        ascendant_longitude = (ascendant_data[0] - ayanamsa_degrees) % 360.0

        ketu_longitude = (raw["rahu"][0] + 180.0) % 360.0
        position_longitudes = {
            key: value[0] for key, value in raw.items() if key != "rahu"
        }
        position_longitudes["rahu"] = raw["rahu"][0]
        position_longitudes["ketu"] = ketu_longitude
        asc_sign, asc_sign_index, _ = _longitude_sign(ascendant_longitude)
        positions: dict[str, PlanetPosition] = {}
        for key, longitude in position_longitudes.items():
            sign, sign_index, degree = _longitude_sign(longitude)
            nakshatra, pada, _ = _nakshatra_details(longitude)
            speed = raw["rahu"][1] if key in {"rahu", "ketu"} else raw[key][1]
            positions[key] = PlanetPosition(
                name=key.title(),
                sidereal_longitude=longitude,
                zodiac_sign=sign,
                degree_in_sign=degree,
                house=(sign_index - asc_sign_index) % 12 + 1,
                nakshatra=nakshatra,
                nakshatra_pada=pada,
                retrograde=speed < 0.0,
            )
        asc_nakshatra, asc_pada, _ = _nakshatra_details(ascendant_longitude)
        ascendant = PlanetPosition(
            name="Ascendant",
            sidereal_longitude=ascendant_longitude,
            zodiac_sign=asc_sign,
            degree_in_sign=_longitude_sign(ascendant_longitude)[2],
            house=1,
            nakshatra=asc_nakshatra,
            nakshatra_pada=asc_pada,
            retrograde=None,
        )

        d1_occupants: list[list[str]] = [[] for _ in SIGNS]
        d1_occupants[asc_sign_index].append("Ascendant")
        for key, position in positions.items():
            d1_occupants[(asc_sign_index + position.house - 1) % 12].append(position.name)
        d1 = DivisionChart(
            division="D1 Rashi",
            ascendant_sign=asc_sign,
            houses=[
                ChartHouse(
                    number=house_number,
                    sign=SIGNS[(asc_sign_index + house_number - 1) % 12],
                    occupants=d1_occupants[(asc_sign_index + house_number - 1) % 12],
                )
                for house_number in range(1, 13)
            ],
            placements=[
                ChartPlacement(
                    name="Ascendant",
                    sign=asc_sign,
                    house=1,
                    degree_in_sign=_longitude_sign(ascendant_longitude)[2],
                ),
                *[
                    ChartPlacement(
                        name=position.name,
                        sign=position.zodiac_sign,
                        house=position.house,
                        degree_in_sign=position.degree_in_sign,
                    )
                    for position in positions.values()
                ],
            ],
        )
        d9 = _make_division_chart("D9 Navamsha", 9, ascendant_longitude, position_longitudes)
        d10 = _make_division_chart("D10 Dashamsha", 10, ascendant_longitude, position_longitudes)

        moon_nakshatra, _, moon_nakshatra_lord = _nakshatra_details(position_longitudes["moon"])
        return ChartResponse(
            chart_id=uuid4(),
            provenance=ChartProvenance(
                utc_birth_timestamp=utc_birth.isoformat().replace("+00:00", "Z"),
                latitude=request.latitude,
                longitude=request.longitude,
                timezone=request.timezone,
                ayanamsa=request.ayanamsa,
                ayanamsa_degrees=ayanamsa_degrees,
                node_type=request.node_type,
                ephemeris_version=str(swe.version),
                ephemeris_source=source,
                calculation_engine_version=ENGINE_VERSION,
            ),
            ascendant=ascendant,
            planets=positions,
            moon_rashi=positions["moon"].zodiac_sign,
            lagna=asc_sign,
            birth_nakshatra=moon_nakshatra,
            nakshatra_lord=moon_nakshatra_lord,
            tithi=_tithi(position_longitudes["sun"], position_longitudes["moon"]),
            d1_rashi_chart=d1,
            d9_navamsa=d9,
            d10_dashamsa=d10,
        )

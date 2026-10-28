from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from app.calculations import NAKSHATRAS, VIMSHOTTARI_LORDS
from app.dasha_schemas import DashaParent, DashaPeriod, DashaSequence

DASHA_YEARS: tuple[tuple[str, int], ...] = (
    ("Ketu", 7),
    ("Venus", 20),
    ("Sun", 6),
    ("Moon", 10),
    ("Mars", 7),
    ("Rahu", 18),
    ("Jupiter", 16),
    ("Saturn", 19),
    ("Mercury", 17),
)
DASHA_YEARS_BY_PLANET = dict(DASHA_YEARS)
NAKSHATRA_ARC_DEGREES = 360.0 / 27.0
VIMSHOTTARI_CYCLE_YEARS = 120
VIMSHOTTARI_YEAR_DAYS = 365.25
SECONDS_PER_DAY = 86_400
SECONDS_PER_DASHA_YEAR = VIMSHOTTARI_YEAR_DAYS * SECONDS_PER_DAY
YEAR_LENGTH_CONVENTION = (
    "One Vimshottari year is 365.25 days (a Julian year); period durations "
    "are converted to elapsed UTC seconds, not calendar-year anniversaries."
)
CHILD_LEVEL: dict[str, Literal["antardasha", "pratyantardasha", "sukshma"]] = {
    "mahadasha": "antardasha",
    "antardasha": "pratyantardasha",
    "pratyantardasha": "sukshma",
}


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Stored chart birth timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _periods_for_interval(
    *,
    start: datetime,
    end: datetime,
    parent: DashaParent | None,
    start_planet_index: int,
    level: Literal["mahadasha", "antardasha", "pratyantardasha", "sukshma"],
    path: str,
) -> list[DashaPeriod]:
    parent_seconds = (end - start).total_seconds()
    child_level = CHILD_LEVEL.get(level)
    periods: list[DashaPeriod] = []
    cursor = start
    for offset in range(len(DASHA_YEARS)):
        planet_index = (start_planet_index + offset) % len(DASHA_YEARS)
        planet, _ = DASHA_YEARS[planet_index]
        child_start = cursor
        if offset == len(DASHA_YEARS) - 1:
            child_end = end
        else:
            child_end = start + timedelta(
                seconds=parent_seconds
                * sum(
                    DASHA_YEARS[(start_planet_index + step) % len(DASHA_YEARS)][1]
                    for step in range(offset + 1)
                )
                / VIMSHOTTARI_CYCLE_YEARS
            )
        period_id = f"{path}.{planet_index}"
        next_parent = DashaParent(period_id=period_id, level=level, planet=planet)
        children = (
            _periods_for_interval(
                start=child_start,
                end=child_end,
                parent=next_parent,
                start_planet_index=planet_index,
                level=child_level,
                path=period_id,
            )
            if child_level is not None
            else []
        )
        duration_seconds = (child_end - child_start).total_seconds()
        periods.append(
            DashaPeriod(
                period_id=period_id,
                level=level,
                planet=planet,
                starts_at=_iso_utc(child_start),
                ends_at=_iso_utc(child_end),
                duration_seconds=duration_seconds,
                duration_years=duration_seconds / SECONDS_PER_DASHA_YEAR,
                parent_period=parent,
                children=children,
            )
        )
        cursor = child_end
    return periods


def calculate_vimshottari_sequence(
    *,
    chart_id: UUID,
    birth_timestamp: str,
    moon_sidereal_longitude: float,
) -> DashaSequence:
    if not 0.0 <= moon_sidereal_longitude < 360.0:
        raise ValueError("Moon sidereal longitude must be in [0, 360)")

    birth = _parse_utc(birth_timestamp)
    nakshatra_index = min(
        int(moon_sidereal_longitude / NAKSHATRA_ARC_DEGREES), 26
    )
    nakshatra_start = nakshatra_index * NAKSHATRA_ARC_DEGREES
    birth_nakshatra = NAKSHATRAS[nakshatra_index]
    nakshatra_lord = VIMSHOTTARI_LORDS[nakshatra_index % len(VIMSHOTTARI_LORDS)]
    elapsed_fraction = (
        moon_sidereal_longitude - nakshatra_start
    ) / NAKSHATRA_ARC_DEGREES
    lord_index = next(
        index
        for index, (planet, _) in enumerate(DASHA_YEARS)
        if planet == nakshatra_lord
    )
    maha_years = DASHA_YEARS_BY_PLANET[nakshatra_lord]
    elapsed_seconds = elapsed_fraction * maha_years * SECONDS_PER_DASHA_YEAR
    sequence_start = birth - timedelta(seconds=elapsed_seconds)
    sequence_end = sequence_start + timedelta(
        seconds=VIMSHOTTARI_CYCLE_YEARS * SECONDS_PER_DASHA_YEAR
    )
    mahadashas: list[DashaPeriod] = []
    cursor = sequence_start

    for offset in range(len(DASHA_YEARS)):
        planet_index = (lord_index + offset) % len(DASHA_YEARS)
        planet, years = DASHA_YEARS[planet_index]
        if offset == len(DASHA_YEARS) - 1:
            end = sequence_end
        else:
            end = cursor + timedelta(seconds=years * SECONDS_PER_DASHA_YEAR)
        period_id = f"maha.{planet_index}"
        parent = None
        children = _periods_for_interval(
            start=cursor,
            end=end,
            parent=DashaParent(period_id=period_id, level="mahadasha", planet=planet),
            start_planet_index=planet_index,
            level="antardasha",
            path=period_id,
        )
        mahadashas.append(
            DashaPeriod(
                period_id=period_id,
                level="mahadasha",
                planet=planet,
                starts_at=_iso_utc(cursor),
                ends_at=_iso_utc(end),
                duration_seconds=(end - cursor).total_seconds(),
                duration_years=(end - cursor).total_seconds()
                / SECONDS_PER_DASHA_YEAR,
                parent_period=parent,
                children=children,
            )
        )
        cursor = end

    return DashaSequence(
        chart_id=chart_id,
        moon_sidereal_longitude=moon_sidereal_longitude,
        birth_nakshatra=birth_nakshatra,
        nakshatra_lord=nakshatra_lord,
        elapsed_nakshatra_fraction=elapsed_fraction,
        balance_at_birth_years=(1.0 - elapsed_fraction) * maha_years,
        year_length_days=VIMSHOTTARI_YEAR_DAYS,
        year_length_convention=YEAR_LENGTH_CONVENTION,
        sequence_starts_at=_iso_utc(sequence_start),
        sequence_ends_at=_iso_utc(sequence_end),
        mahadashas=mahadashas,
    )

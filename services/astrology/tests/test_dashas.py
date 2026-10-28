from datetime import datetime
import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.dashas import (
    DASHA_YEARS,
    SECONDS_PER_DASHA_YEAR,
    calculate_vimshottari_sequence,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "vimshottari_reference.json").read_text(
        encoding="utf-8"
    )
)


def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def find_active_path(periods, instant):
    for period in periods:
        start = parse_date(period.starts_at)
        end = parse_date(period.ends_at)
        if start <= instant < end:
            return [period, *find_active_path(period.children, instant)]
    return []


@pytest.fixture
def sequence():
    return calculate_vimshottari_sequence(
        chart_id=uuid4(),
        birth_timestamp=FIXTURE["birth_timestamp"],
        moon_sidereal_longitude=FIXTURE["moon_sidereal_longitude"],
    )


def test_reference_birth_balance_and_first_mahadasha(sequence) -> None:
    assert sequence.birth_nakshatra == FIXTURE["birth_nakshatra"]
    assert sequence.nakshatra_lord == FIXTURE["nakshatra_lord"]
    assert sequence.elapsed_nakshatra_fraction == pytest.approx(
        FIXTURE["elapsed_nakshatra_fraction"], abs=1e-12
    )
    assert sequence.balance_at_birth_years == pytest.approx(
        FIXTURE["balance_at_birth_years"], abs=1e-12
    )
    assert sequence.sequence_starts_at == FIXTURE["sequence_starts_at"]
    assert [period.planet for period in sequence.mahadashas] == FIXTURE[
        "mahadasha_planets"
    ]
    assert sequence.mahadashas[0].ends_at == FIXTURE["first_mahadasha_ends_at"]
    assert [period.planet for period in sequence.mahadashas[0].children] == FIXTURE[
        "first_mahadasha_antardasha_planets"
    ]
    assert (
        sequence.mahadashas[0].children[0].ends_at
        == FIXTURE["first_antardasha_ends_at"]
    )
    assert sequence.year_length_days == 365.25


def test_complete_120_year_cycle_and_exact_parent_relationships(sequence) -> None:
    assert len(sequence.mahadashas) == 9
    assert sum(period.duration_years for period in sequence.mahadashas) == pytest.approx(
        120.0, abs=1e-10
    )
    assert sequence.mahadashas[0].starts_at == sequence.sequence_starts_at
    assert sequence.mahadashas[-1].ends_at == sequence.sequence_ends_at

    counts = {"mahadasha": 0, "antardasha": 0, "pratyantardasha": 0, "sukshma": 0}

    def verify(periods, parent=None):
        for index, period in enumerate(periods):
            counts[period.level] += 1
            assert period.duration_seconds > 0
            assert period.duration_years == pytest.approx(
                period.duration_seconds / SECONDS_PER_DASHA_YEAR, abs=1e-12
            )
            if parent is None:
                assert period.parent_period is None
            else:
                assert period.parent_period.period_id == parent.period_id
                assert period.parent_period.planet == parent.planet
            if period.children:
                assert period.children[0].starts_at == period.starts_at
                assert period.children[-1].ends_at == period.ends_at
                assert sum(child.duration_seconds for child in period.children) == pytest.approx(
                    period.duration_seconds, abs=1e-5
                )
                verify(period.children, period)
            if index:
                previous = periods[index - 1]
                assert previous.ends_at == period.starts_at

    verify(sequence.mahadashas)
    assert counts == {
        "mahadasha": 9,
        "antardasha": 81,
        "pratyantardasha": 729,
        "sukshma": 6561,
    }


def test_independent_birth_table_has_expected_nested_periods(sequence) -> None:
    birth = parse_date(FIXTURE["birth_timestamp"])
    active = find_active_path(sequence.mahadashas, birth)
    assert [period.planet for period in active] == FIXTURE["active_at_birth"]
    assert [period.starts_at for period in active] == FIXTURE[
        "active_at_birth_period_starts"
    ]
    assert [period.ends_at for period in active] == FIXTURE[
        "active_at_birth_period_ends"
    ]


@pytest.mark.parametrize("longitude", [-0.1, 360.0, 1000.0])
def test_invalid_moon_longitude_is_rejected(longitude: float) -> None:
    with pytest.raises(ValueError, match="longitude"):
        calculate_vimshottari_sequence(
            chart_id=uuid4(),
            birth_timestamp=FIXTURE["birth_timestamp"],
            moon_sidereal_longitude=longitude,
        )


def test_exact_nakshatra_boundary_starts_full_lord_period() -> None:
    boundary = 14 * (360.0 / 27.0)
    sequence = calculate_vimshottari_sequence(
        chart_id=uuid4(),
        birth_timestamp=FIXTURE["birth_timestamp"],
        moon_sidereal_longitude=boundary,
    )
    assert sequence.birth_nakshatra == "Swati"
    assert sequence.nakshatra_lord == "Rahu"
    assert sequence.elapsed_nakshatra_fraction == pytest.approx(0.0, abs=1e-14)
    assert sequence.balance_at_birth_years == 18.0
    assert parse_date(sequence.sequence_starts_at) == parse_date(
        FIXTURE["birth_timestamp"]
    )

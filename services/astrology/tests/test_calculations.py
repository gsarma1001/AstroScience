from datetime import date, time
import json
from pathlib import Path

import pytest

from app.calculations import (
    InvalidBirthTime,
    _make_division_chart,
    _resolve_birth_datetime,
    _tithi,
    _varga_sign,
    calculate_chart,
)
from app.schemas import ChartRequest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "jpl_horizons_reference.json"
REFERENCE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def chart_request(**overrides: object) -> ChartRequest:
    data: dict[str, object] = {
        "birth_date": "2000-01-01",
        "birth_time": "12:00:00",
        "latitude": 0,
        "longitude": 0,
        "timezone": "UTC",
    }
    data.update(overrides)
    return ChartRequest.model_validate(data)


def angular_difference(first: float, second: float) -> float:
    return abs((first - second + 180.0) % 360.0 - 180.0)


def test_dst_repeated_local_time_requires_fold() -> None:
    with pytest.raises(InvalidBirthTime, match="ambiguous"):
        _resolve_birth_datetime(
            date(2021, 11, 7), time(1, 30), "America/New_York", None
        )

    earlier = _resolve_birth_datetime(
        date(2021, 11, 7), time(1, 30), "America/New_York", 0
    )
    later = _resolve_birth_datetime(
        date(2021, 11, 7), time(1, 30), "America/New_York", 1
    )
    assert (later - earlier).total_seconds() == 3600


def test_dst_nonexistent_local_time_is_rejected() -> None:
    with pytest.raises(InvalidBirthTime, match="does not exist"):
        _resolve_birth_datetime(
            date(2021, 3, 14), time(2, 30), "America/New_York", None
        )


def test_historical_timezone_offset_is_resolved_from_iana_data() -> None:
    utc_birth = _resolve_birth_datetime(
        date(1900, 1, 1), time(12), "Asia/Kolkata", None
    )
    assert utc_birth.isoformat() == "1900-01-01T06:38:50+00:00"


def test_tithi_wraps_at_new_moon() -> None:
    tithi = _tithi(359.0, 1.0)
    assert tithi["paksha"] == "Shukla"
    assert tithi["name"] == "Pratipada"
    assert tithi["elongation_degrees"] == pytest.approx(2.0)

    new_moon = _tithi(359.0, 358.999)
    assert new_moon["paksha"] == "Krishna"
    assert new_moon["name"] == "Amavasya"


def test_varga_segment_rules_and_house_order() -> None:
    positions = {"sun": 0.0, "moon": 16.0, "mars": 29.999}
    navamsa = _make_division_chart("D9 Navamsha", 9, 0.0, positions)
    dashamsa = _make_division_chart("D10 Dashamsha", 10, 0.0, positions)

    assert navamsa.ascendant_sign == "Aries"
    assert navamsa.houses[0].occupants == ["Ascendant", "Sun"]
    assert navamsa.houses[4].occupants == ["Moon"]
    assert dashamsa.houses[0].occupants == ["Ascendant", "Sun"]
    assert dashamsa.houses[5].occupants == ["Moon"]
    assert dashamsa.houses[9].occupants == ["Mars"]
    assert [house.number for house in navamsa.houses] == list(range(1, 13))


def test_varga_start_sign_rules_for_all_modalities_and_even_signs() -> None:
    assert _varga_sign(0, 0.0, 9) == 0
    assert _varga_sign(1, 0.0, 9) == 9
    assert _varga_sign(2, 0.0, 9) == 6
    assert _varga_sign(3, 0.0, 9) == 3
    assert _varga_sign(0, 3.0, 10) == 1
    assert _varga_sign(1, 0.0, 10) == 9
    assert _varga_sign(1, 3.0, 10) == 10


def test_calculated_chart_structure_and_provenance() -> None:
    chart = calculate_chart(chart_request())
    assert chart.provenance.utc_birth_timestamp == "2000-01-01T12:00:00Z"
    assert chart.provenance.ayanamsa.value == "lahiri"
    assert chart.provenance.ephemeris_version
    assert chart.provenance.calculation_engine_version == "0.1.0"
    assert set(chart.planets) == {
        "sun",
        "moon",
        "mars",
        "mercury",
        "jupiter",
        "venus",
        "saturn",
        "rahu",
        "ketu",
    }
    assert len(chart.d1_rashi_chart.houses) == 12
    assert len(chart.d9_navamsa.houses) == 12
    assert len(chart.d10_dashamsa.houses) == 12
    assert chart.lagna == chart.ascendant.zodiac_sign
    assert chart.moon_rashi == chart.planets["moon"].zodiac_sign
    assert (
        chart.planets["ketu"].sidereal_longitude
        == (chart.planets["rahu"].sidereal_longitude + 180.0) % 360.0
    )
    assert chart.planets["rahu"].retrograde is True
    assert chart.planets["ketu"].retrograde == chart.planets["rahu"].retrograde
    for planet in chart.planets.values():
        assert 0.0 <= planet.sidereal_longitude < 360.0
        assert 0.0 <= planet.degree_in_sign < 30.0
        assert 1 <= planet.house <= 12
        assert 1 <= planet.nakshatra_pada <= 4


def test_ayanamsa_and_node_options_are_applied() -> None:
    lahiri = calculate_chart(chart_request())
    raman = calculate_chart(chart_request(ayanamsa="raman"))
    krishnamurti = calculate_chart(chart_request(ayanamsa="krishnamurti"))
    true_node = calculate_chart(chart_request(node_type="true"))

    assert raman.provenance.ayanamsa.value == "raman"
    assert krishnamurti.provenance.ayanamsa.value == "krishnamurti"
    assert raman.provenance.ayanamsa_degrees != lahiri.provenance.ayanamsa_degrees
    assert (
        krishnamurti.provenance.ayanamsa_degrees
        != lahiri.provenance.ayanamsa_degrees
    )
    assert true_node.provenance.node_type.value == "true"
    assert true_node.planets["rahu"].sidereal_longitude != (
        lahiri.planets["rahu"].sidereal_longitude
    )
    assert true_node.planets["ketu"].sidereal_longitude == (
        true_node.planets["rahu"].sidereal_longitude + 180.0
    ) % 360.0


@pytest.mark.parametrize("planet", REFERENCE["sidereal_longitudes"])
def test_positions_against_independent_jpl_horizons_reference(planet: str) -> None:
    chart = calculate_chart(chart_request())
    expected = REFERENCE["sidereal_longitudes"][planet]
    assert angular_difference(
        chart.planets[planet].sidereal_longitude, expected
    ) <= REFERENCE["tolerance_degrees"]

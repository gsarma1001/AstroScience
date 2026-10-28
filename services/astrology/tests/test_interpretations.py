from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.dashas import calculate_vimshottari_sequence
from app.interpretation_schemas import LifeDomain
from app.interpretation_schemas import ChartInterpretationRequest
from app.interpretations import (
    CLASSICAL_GRAHA_ASPECTS,
    EXALTATION_SIGNS,
    DEBILITATION_SIGNS,
    PLANET_NAMES,
    PLANET_SIGNS,
    SIGN_INDEX,
    SIGN_LORDS,
    interpret_chart,
)
from app.schemas import (
    Ayanamsa,
    ChartHouse,
    ChartPlacement,
    ChartProvenance,
    ChartResponse,
    DivisionChart,
    NodeType,
    PlanetPosition,
)


PLANETS = tuple(PLANET_NAMES)


def make_chart(
    *,
    ascendant_sign: str = "Aries",
    placements: dict[str, str] | None = None,
) -> ChartResponse:
    ascendant_index = SIGN_INDEX[ascendant_sign]
    signs = {
        "sun": "Leo",
        "moon": "Aries",
        "mars": "Capricorn",
        "mercury": "Virgo",
        "jupiter": "Libra",
        "venus": "Cancer",
        "saturn": "Aquarius",
        "rahu": "Pisces",
        "ketu": "Virgo",
    }
    signs.update(placements or {})
    planets: dict[str, PlanetPosition] = {}
    occupants: list[list[str]] = [[] for _ in range(12)]
    division_placements = [
        ChartPlacement(
            name="Ascendant",
            sign=ascendant_sign,
            house=1,
            degree_in_sign=0.0,
        )
    ]
    for key in PLANETS:
        sign = signs[key]
        sign_index = SIGN_INDEX[sign]
        house = (sign_index - ascendant_index) % 12 + 1
        degree = 10.0
        planets[key] = PlanetPosition(
            name=PLANET_NAMES[key],
            sidereal_longitude=sign_index * 30 + degree,
            zodiac_sign=sign,
            degree_in_sign=degree,
            house=house,
            nakshatra="Ashwini",
            nakshatra_pada=1,
            retrograde=False,
        )
        occupants[house - 1].append(PLANET_NAMES[key])
        division_placements.append(
            ChartPlacement(
                name=PLANET_NAMES[key],
                sign=sign,
                house=house,
                degree_in_sign=degree,
            )
        )
    houses = [
        ChartHouse(
            number=house,
            sign=(
                ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
                [(ascendant_index + house - 1) % 12]
            ),
            occupants=occupants[house - 1],
        )
        for house in range(1, 13)
    ]

    def division(name: str) -> DivisionChart:
        return DivisionChart(
            division=name,
            ascendant_sign=ascendant_sign,
            houses=houses,
            placements=division_placements,
        )

    return ChartResponse(
        chart_id=uuid4(),
        provenance=ChartProvenance(
            utc_birth_timestamp="2000-01-01T12:00:00Z",
            latitude=0,
            longitude=0,
            timezone="UTC",
            ayanamsa=Ayanamsa.LAHIRI,
            ayanamsa_degrees=23.8,
            node_type=NodeType.MEAN,
            ephemeris_version="test",
            ephemeris_source="test",
            calculation_engine_version="test",
        ),
        ascendant=PlanetPosition(
            name="Ascendant",
            sidereal_longitude=ascendant_index * 30,
            zodiac_sign=ascendant_sign,
            degree_in_sign=0,
            house=1,
            nakshatra="Ashwini",
            nakshatra_pada=1,
            retrograde=None,
        ),
        planets=planets,
        moon_rashi=signs["moon"],
        lagna=ascendant_sign,
        birth_nakshatra="Ashwini",
        nakshatra_lord="Ketu",
        tithi={"paksha": "Shukla", "number_in_paksha": 1, "name": "Pratipada"},
        d1_rashi_chart=division("D1 Rashi"),
        d9_navamsa=division("D9 Navamsha"),
        d10_dashamsa=division("D10 Dashamsha"),
    )


def rules_by_id(chart: ChartResponse):
    return interpret_chart(chart)


@pytest.mark.parametrize("ascendant_index", range(12))
def test_house_lords_are_derived_from_whole_sign_ascendant(ascendant_index: int):
    signs = (
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    )
    result = rules_by_id(make_chart(ascendant_sign=signs[ascendant_index]))
    lords = {
        rule.rule_name.split()[0]: rule
        for rule in result.relationship_rules
        if rule.rule_id.startswith("relationship.lordship.")
    }
    assert len(lords) == 9
    for house in range(1, 13):
        expected = SIGN_LORDS[(ascendant_index + house - 1) % 12]
        ownership = next(
            factor
            for factor in lords[expected].chart_factors_used
            if "owns house(s)" in factor
        )
        owned_houses = [
            int(value)
            for value in ownership.split("owns house(s) ", 1)[1].split(", ")
        ]
        assert house in owned_houses


@pytest.mark.parametrize(
    ("planet", "sign", "status"),
    [
        (planet, sign, "exalted")
        for planet, sign in EXALTATION_SIGNS.items()
    ]
    + [
        (planet, sign, "debilitated")
        for planet, sign in DEBILITATION_SIGNS.items()
    ],
)
def test_traditional_exaltation_and_debilitation_rules(planet, sign, status):
    key = planet.lower()
    result = rules_by_id(make_chart(placements={key: sign}))
    rule = next(
        item
        for item in result.relationship_rules
        if item.rule_id == f"relationship.dignity.{key}"
    )
    assert f"status: {status}" in rule.chart_factors_used
    assert rule.source_reference.startswith("Brihat Parashara Hora Shastra")


def test_own_sign_and_disputed_node_dignity_are_reported():
    result = rules_by_id(
        make_chart(placements={"sun": "Leo", "rahu": "Taurus", "ketu": "Scorpio"})
    )
    sun = next(
        rule
        for rule in result.relationship_rules
        if rule.rule_id == "relationship.dignity.sun"
    )
    rahu = next(
        rule
        for rule in result.relationship_rules
        if rule.rule_id == "relationship.dignity.rahu"
    )
    assert "status: own_sign" in sun.chart_factors_used
    assert "No dignity status is assigned" in rahu.traditional_meaning


@pytest.mark.parametrize(
    ("planet", "sign"),
    [
        (planet, sign)
        for planet, signs in PLANET_SIGNS.items()
        for sign in signs
    ],
)
def test_every_classical_own_sign_is_recognized(planet, sign):
    key = planet.lower()
    result = rules_by_id(make_chart(placements={key: sign}))
    rule = next(
        item
        for item in result.relationship_rules
        if item.rule_id == f"relationship.dignity.{key}"
    )
    assert "status: own_sign" in rule.chart_factors_used


def test_functional_benefic_and_malefic_relationships_are_contextual():
    result = rules_by_id(make_chart())
    jupiter = next(
        rule
        for rule in result.relationship_rules
        if rule.rule_id == "relationship.lordship.jupiter"
    )
    assert "contextual functional-benefic indication" in jupiter.chart_factors_used
    assert "contextual functional-malefic indication" in jupiter.chart_factors_used
    assert "not as a fixed" in jupiter.traditional_meaning


def test_nodes_have_explicitly_unassigned_house_lordships():
    result = rules_by_id(make_chart())
    node_rules = [
        rule
        for rule in result.relationship_rules
        if rule.rule_id in {
            "relationship.lordship.rahu",
            "relationship.lordship.ketu",
        }
    ]
    assert len(node_rules) == 2
    assert all(
        "No functional house lordships" in rule.traditional_meaning
        for rule in node_rules
    )


def test_conjunction_and_classical_graha_drishti_rules():
    result = rules_by_id(make_chart())
    assert any(
        rule.rule_id == "relationship.conjunction.house_6"
        for rule in result.relationship_rules
    )
    aspect_ids = {
        rule.rule_id for rule in result.relationship_rules if ".drishti." in rule.rule_id
    }
    assert "relationship.drishti.mars.house_4" in aspect_ids
    assert "relationship.drishti.jupiter.house_11" in aspect_ids
    assert "relationship.drishti.saturn.house_1" in aspect_ids


@pytest.mark.parametrize("planet,offsets", CLASSICAL_GRAHA_ASPECTS.items())
def test_each_classical_graha_drishti_pattern_is_applied(planet, offsets):
    target_signs = (
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    )
    target_houses = {
        (1 - 1 + offset - 1) % 12 + 1 for offset in offsets
    }
    other_planets = [name for name in PLANETS if PLANET_NAMES[name] != planet]
    placements = {planet.lower(): "Aries"}
    for name in other_planets:
        placements[name] = target_signs[min(target_houses) - 1]
    for index, house in enumerate(sorted(target_houses)):
        placements[other_planets[index]] = target_signs[house - 1]
    chart = make_chart(ascendant_sign="Aries", placements=placements)
    source = next(
        position
        for position in chart.planets.values()
        if position.name == planet
    )
    expected_houses = {
        (source.house - 1 + offset - 1) % 12 + 1 for offset in offsets
    }
    result = rules_by_id(chart)
    observed_houses = {
        int(rule.rule_id.rsplit("_", 1)[1])
        for rule in result.relationship_rules
        if rule.rule_id.startswith(f"relationship.drishti.{planet.lower()}.")
    }
    assert observed_houses == expected_houses


def test_raja_yoga_from_connected_kendra_and_trikona_lords():
    chart = make_chart(placements={"mars": "Libra", "jupiter": "Libra"})
    rules = rules_by_id(chart).yogas
    assert any(rule.rule_id.startswith("yoga.raja.") for rule in rules)


def test_raja_yoga_accepts_classical_graha_drishti_connection():
    chart = make_chart(placements={"mars": "Aries", "sun": "Libra"})
    assert any(
        rule.rule_id == "yoga.raja.mars.sun"
        and any("graha drishti" in item for item in rule.supporting_reasoning)
        for rule in rules_by_id(chart).yogas
    )


def test_raja_yoga_accepts_mutual_sign_exchange():
    chart = make_chart(placements={"mars": "Sagittarius", "jupiter": "Scorpio"})
    rules = rules_by_id(chart).yogas
    assert any(
        rule.rule_id == "yoga.raja.jupiter.mars"
        and any("sign exchange" in reason for reason in rule.supporting_reasoning)
        for rule in rules
    )


def test_single_planet_can_own_kendra_and_trikona_for_raja_yoga():
    chart = make_chart(ascendant_sign="Taurus")
    assert any(
        rule.rule_id == "yoga.raja.single.saturn"
        for rule in rules_by_id(chart).yogas
    )


def test_dhana_yoga_from_wealth_house_lord_connection():
    chart = make_chart(placements={"venus": "Aquarius", "jupiter": "Aquarius"})
    assert any(
        rule.rule_id == "yoga.dhana.venus.jupiter"
        for rule in rules_by_id(chart).yogas
    )


@pytest.mark.parametrize(
    ("planet", "sign", "ascendant", "yoga"),
    [
        ("mars", "Capricorn", "Aries", "ruchaka"),
        ("mercury", "Virgo", "Gemini", "bhadra"),
        ("jupiter", "Cancer", "Aries", "hamsa"),
        ("venus", "Pisces", "Sagittarius", "malavya"),
        ("saturn", "Libra", "Cancer", "sasa"),
    ],
)
def test_each_pancha_mahapurusha_yoga(planet, sign, ascendant, yoga):
    rules = rules_by_id(
        make_chart(ascendant_sign=ascendant, placements={planet: sign})
    ).yogas
    assert any(rule.rule_id == f"yoga.pancha_mahapurusha.{yoga}" for rule in rules)


def test_gaja_kesari_requires_jupiter_in_kendra_from_moon():
    result = rules_by_id(make_chart(placements={"moon": "Aries", "jupiter": "Cancer"}))
    assert any(rule.rule_id == "yoga.gaja_kesari" for rule in result.yogas)
    absent = rules_by_id(make_chart(placements={"moon": "Aries", "jupiter": "Leo"}))
    assert not any(rule.rule_id == "yoga.gaja_kesari" for rule in absent.yogas)


def test_vipareeta_raja_yoga_checks_dusthana_lord_in_dusthana():
    result = rules_by_id(make_chart(placements={"mercury": "Scorpio"}))
    assert any(rule.rule_id == "yoga.vipareeta.6.mercury" for rule in result.yogas)


def test_neecha_bhanga_reports_cancellation_condition_and_limitation():
    result = rules_by_id(
        make_chart(placements={"mars": "Cancer", "moon": "Aries"})
    )
    rule = next(
        rule for rule in result.yogas if rule.rule_id == "yoga.neecha_bhanga.mars"
    )
    assert any("dispositor of debilitation sign" in factor for factor in rule.chart_factors_used)
    assert any("subset" in item for item in rule.limitations_or_conflicting_factors)


@pytest.mark.parametrize("domain", list(LifeDomain))
def test_every_life_domain_returns_traceable_cautious_rule(domain):
    rule = rules_by_id(make_chart()).domains[domain]
    assert rule.rule_id == f"domain.{domain.value}"
    assert rule.chart_factors_used
    assert rule.source_reference
    assert rule.relevant_life_domains == [domain]
    assert "not a" in rule.traditional_meaning or "not outcome" in rule.traditional_meaning
    assert rule.limitations_or_conflicting_factors


def test_modern_synthesis_domains_are_separated_from_classical_rules():
    result = rules_by_id(make_chart())
    assert result.domains[LifeDomain.BUSINESS].tradition == "modern_synthesis"
    assert result.domains[LifeDomain.RELOCATION].tradition == "modern_synthesis"
    assert result.domains[LifeDomain.PERSONALITY].tradition == "classical"


def test_dasha_rules_use_active_lords_d1_natal_and_varga_factors():
    chart = make_chart()
    dashas = calculate_vimshottari_sequence(
        chart_id=chart.chart_id,
        birth_timestamp="2000-01-01T12:00:00Z",
        moon_sidereal_longitude=199.461824130,
    )
    result = interpret_chart(
        chart,
        dashas=dashas,
        as_of=datetime(2000, 1, 1, 12, tzinfo=timezone.utc),
    )
    assert [rule.rule_id for rule in result.active_dasha_rules] == [
        "dasha.mahadasha.rahu",
        "dasha.antardasha.mars",
        "dasha.pratyantardasha.jupiter",
    ]
    for rule in result.active_dasha_rules:
        assert any("D1 placement" in factor for factor in rule.chart_factors_used)
        assert any("D9 Navamsha" in factor for factor in rule.chart_factors_used)
        assert "D10 Dashamsha" not in " ".join(rule.chart_factors_used)
    assert "ambition" in result.active_dasha_rules[0].traditional_meaning


def test_d10_is_used_as_career_corroboration_in_active_saturn_dasha():
    chart = make_chart()
    dashas = calculate_vimshottari_sequence(
        chart_id=chart.chart_id,
        birth_timestamp="2000-01-01T12:00:00Z",
        moon_sidereal_longitude=199.461824130,
    )
    result = interpret_chart(
        chart,
        dashas=dashas,
        as_of=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    saturn_mahadasha = next(
        rule
        for rule in result.active_dasha_rules
        if rule.rule_id == "dasha.mahadasha.saturn"
    )
    assert any("D10 Dashamsha" in factor for factor in saturn_mahadasha.chart_factors_used)


def test_dasha_sequence_must_belong_to_supplied_chart():
    chart = make_chart()
    dashas = calculate_vimshottari_sequence(
        chart_id=uuid4(),
        birth_timestamp="2000-01-01T12:00:00Z",
        moon_sidereal_longitude=199.461824130,
    )
    with pytest.raises(ValueError, match="chart_id"):
        interpret_chart(chart, dashas=dashas)


def test_interpretations_disclaimers_do_not_assign_probabilities():
    result = rules_by_id(make_chart())
    assert "No probabilities" in result.interpretation_notice
    assert "death, disease" in result.interpretation_notice


def test_interpretation_request_rejects_incomplete_chart():
    chart = make_chart().model_dump(mode="json")
    del chart["planets"]["moon"]
    with pytest.raises(ValueError, match="nine supported planetary positions"):
        ChartInterpretationRequest.model_validate({"chart": chart})

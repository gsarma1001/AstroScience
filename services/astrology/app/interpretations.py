from __future__ import annotations

from datetime import datetime, timezone
from itertools import combinations

from app.dasha_schemas import DashaPeriod, DashaSequence
from app.interpretation_schemas import (
    ChartInterpretationResponse,
    InterpretationRule,
    InterpretationTradition,
    LifeDomain,
)
from app.schemas import ChartResponse, PlanetPosition

PLANET_NAMES = {
    "sun": "Sun",
    "moon": "Moon",
    "mars": "Mars",
    "mercury": "Mercury",
    "jupiter": "Jupiter",
    "venus": "Venus",
    "saturn": "Saturn",
    "rahu": "Rahu",
    "ketu": "Ketu",
}
SIGN_NAMES = (
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
SIGN_INDEX = {sign: index for index, sign in enumerate(SIGN_NAMES)}
SIGN_LORDS = (
    "Mars",
    "Venus",
    "Mercury",
    "Moon",
    "Sun",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Saturn",
    "Jupiter",
)
PLANET_SIGNS = {
    planet: tuple(
        sign for sign, lord in zip(SIGN_NAMES, SIGN_LORDS, strict=True) if lord == planet
    )
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
}
EXALTATION_SIGNS = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mars": "Capricorn",
    "Mercury": "Virgo",
    "Jupiter": "Cancer",
    "Venus": "Pisces",
    "Saturn": "Libra",
}
DEBILITATION_SIGNS = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mars": "Cancer",
    "Mercury": "Pisces",
    "Jupiter": "Capricorn",
    "Venus": "Virgo",
    "Saturn": "Aries",
}
CLASSICAL_GRAHA_ASPECTS = {
    "Sun": (7,),
    "Moon": (7,),
    "Mars": (4, 7, 8),
    "Mercury": (7,),
    "Jupiter": (5, 7, 9),
    "Venus": (7,),
    "Saturn": (3, 7, 10),
}
TRIKONA_HOUSES = {1, 5, 9}
KENDRA_HOUSES = {1, 4, 7, 10}
DUSTHANA_HOUSES = {6, 8, 12}
CLASSICAL_RELATIONSHIP_SOURCE = (
    "Brihat Parashara Hora Shastra (BPHS), planetary natures, lordship, "
    "and graha-drishti sections; chapter numbering differs across editions."
)
CLASSICAL_YOGA_SOURCE = (
    "BPHS, Raja Yoga and other yoga sections; corroborate with the relevant "
    "yoga discussions in Phaladeepika. Chapter numbering differs across editions."
)
CLASSICAL_BHAVA_SOURCE = (
    "BPHS, bhava significations (house-result sections); chapter numbering "
    "differs across editions. House topics are traditional symbolic associations."
)
MODERN_DOMAIN_SOURCE = (
    "Modern Jyotisha synthesis of traditional bhava significations; not a "
    "quotation or a single classical rule."
)
PLANETARY_DASHA_THEMES = {
    "Sun": "responsibility, visibility, authority, and vitality",
    "Moon": "mind, care, nourishment, and public responsiveness",
    "Mars": "initiative, effort, courage, and conflict management",
    "Mercury": "learning, communication, analysis, and exchange",
    "Jupiter": "learning, counsel, growth, and ethical reflection",
    "Venus": "relationships, art, comfort, and shared values",
    "Saturn": "discipline, obligations, endurance, and long-term work",
    "Rahu": "ambition, unfamiliar experiences, experimentation, and worldly aims",
    "Ketu": "detachment, simplification, introspection, and spiritual inquiry",
}
GENERAL_LIMITATIONS = [
    "This is a description of a traditional interpretive convention, not an empirically validated prediction.",
    "Results depend on the selected ayanamsa, birth-time accuracy, house system, and Jyotisha lineage.",
]

DOMAIN_HOUSES: dict[LifeDomain, tuple[tuple[int, ...], tuple[str, ...]]] = {
    LifeDomain.PERSONALITY: ((1,), ("Sun", "Moon")),
    LifeDomain.CAREER: ((6, 10, 11), ("Sun", "Saturn")),
    LifeDomain.BUSINESS: ((2, 7, 10, 11), ("Mercury",)),
    LifeDomain.MARRIAGE: ((2, 7, 8), ("Venus",)),
    LifeDomain.CHILDREN: ((5,), ("Jupiter",)),
    LifeDomain.HEALTH: ((1, 6, 8, 12), ("Sun", "Moon")),
    LifeDomain.WEALTH: ((2, 5, 9, 11), ("Jupiter", "Venus")),
    LifeDomain.RELOCATION: ((4, 9, 12), ()),
    LifeDomain.SPIRITUALITY: ((5, 9, 12), ("Jupiter", "Ketu")),
}
DOMAIN_TRADITION = {
    LifeDomain.BUSINESS: InterpretationTradition.MODERN_SYNTHESIS,
    LifeDomain.RELOCATION: InterpretationTradition.MODERN_SYNTHESIS,
}


def _rule(
    *,
    rule_id: str,
    name: str,
    factors: list[str],
    meaning: str,
    reasoning: list[str],
    domains: list[LifeDomain],
    source: str,
    limitations: list[str] | None = None,
    tradition: InterpretationTradition = InterpretationTradition.CLASSICAL,
) -> InterpretationRule:
    return InterpretationRule(
        rule_id=rule_id,
        rule_name=name,
        tradition=tradition,
        chart_factors_used=factors,
        traditional_meaning=meaning,
        supporting_reasoning=reasoning,
        relevant_life_domains=domains,
        source_reference=source,
        limitations_or_conflicting_factors=limitations or GENERAL_LIMITATIONS.copy(),
    )


def _house_lords(chart: ChartResponse) -> dict[int, str]:
    ascendant_index = SIGN_INDEX[chart.d1_rashi_chart.ascendant_sign]
    return {
        house: SIGN_LORDS[(ascendant_index + house - 1) % 12]
        for house in range(1, 13)
    }


def _owned_houses(chart: ChartResponse) -> dict[str, list[int]]:
    owned = {planet: [] for planet in PLANET_SIGNS}
    for house, lord in _house_lords(chart).items():
        owned[lord].append(house)
    return owned


def _placement(chart: ChartResponse, planet: str) -> PlanetPosition | None:
    key = planet.lower()
    return chart.planets.get(key)


def _dignity(planet: str, sign: str) -> str:
    if planet in {"Rahu", "Ketu"}:
        return "not_assessed_disputed_node"
    statuses = []
    if sign in PLANET_SIGNS.get(planet, ()):
        statuses.append("own_sign")
    if EXALTATION_SIGNS.get(planet) == sign:
        statuses.append("exalted")
    if DEBILITATION_SIGNS.get(planet) == sign:
        statuses.append("debilitated")
    return "_and_".join(statuses) or "neither_own_exalted_nor_debilitated"


def _aspects(source_house: int, target_house: int, planet: str) -> bool:
    distance = (target_house - source_house) % 12 + 1
    return distance in CLASSICAL_GRAHA_ASPECTS.get(planet, ())


def _associated(
    first: str,
    second: str,
    placements: dict[str, PlanetPosition],
) -> list[str]:
    first_position = placements[first.lower()]
    second_position = placements[second.lower()]
    reasons: list[str] = []
    if first_position.house == second_position.house:
        reasons.append("same whole-sign house (sign conjunction)")
    if _aspects(first_position.house, second_position.house, first):
        reasons.append(f"{first} casts a classical graha drishti to {second}")
    if _aspects(second_position.house, first_position.house, second):
        reasons.append(f"{second} casts a classical graha drishti to {first}")
    if (
        SIGN_LORDS[SIGN_INDEX[first_position.zodiac_sign]] == second
        and SIGN_LORDS[SIGN_INDEX[second_position.zodiac_sign]] == first
    ):
        reasons.append("mutual sign exchange (parivartana)")
    return reasons


def _relationship_rules(chart: ChartResponse) -> list[InterpretationRule]:
    owned = _owned_houses(chart)
    rules: list[InterpretationRule] = []
    for planet, houses in owned.items():
        tags: list[str] = []
        if set(houses) & TRIKONA_HOUSES:
            tags.append("trikona lordship (1, 5, or 9)")
            tags.append("contextual functional-benefic indication")
        if set(houses) & KENDRA_HOUSES:
            tags.append("kendra lordship (1, 4, 7, or 10)")
        if set(houses) & {3, 6, 11}:
            tags.append("dustha/upachaya lordship (3, 6, or 11)")
            tags.append("contextual functional-malefic indication")
        if set(houses) & {2, 7}:
            tags.append("maraka house lordship association (2 or 7)")
        if 8 in houses:
            tags.append("eighth-house lordship")
            tags.append("contextual functional-malefic indication")
        if 12 in houses:
            tags.append("twelfth-house lordship")
            tags.append("contextual functional-malefic indication")
        if set(houses) & KENDRA_HOUSES and not set(houses) & TRIKONA_HOUSES:
            tags.append(
                "kendra lordship requires contextual assessment; some schools note "
                "kendradhipati considerations for natural benefics"
            )
        rules.append(
            _rule(
                rule_id=f"relationship.lordship.{planet.lower()}",
                name=f"{planet} functional house lordships",
                factors=[f"{planet} owns house(s) {', '.join(map(str, houses)) or 'none'}"]
                + tags,
                meaning=(
                    f"{planet}'s traditional functional role is assessed from its "
                    "house lordships and should be read contextually, not as a fixed "
                    "benefic-or-malefic label."
                ),
                reasoning=tags
                or [
                    "No house ownership assigned to this planet in the seven-planet sign-lord scheme; node sign lordships are not assumed."
                ],
                domains=[],
                source=CLASSICAL_RELATIONSHIP_SOURCE,
                limitations=[
                    "Functional benefic/malefic classifications vary by ascendant and lineage.",
                    "A planet owning more than one house can carry mixed significations; strength and associations are not reduced to one label.",
                    *GENERAL_LIMITATIONS,
                ],
            )
        )

    for planet in ("Rahu", "Ketu"):
        rules.append(
            _rule(
                rule_id=f"relationship.lordship.{planet.lower()}",
                name=f"{planet} functional house lordships",
                factors=[f"{planet} sign lordships not assigned"],
                meaning=(
                    f"No functional house lordships are assigned to {planet} in this "
                    "seven-planet sign-lord scheme."
                ),
                reasoning=[
                    "Node sign ownership and functional lordship are disputed across Jyotisha lineages."
                ],
                domains=[],
                source=CLASSICAL_RELATIONSHIP_SOURCE,
                limitations=[
                    "Alternative schools assign sign rulerships to the nodes; those schemes are intentionally not selected here.",
                    *GENERAL_LIMITATIONS,
                ],
            )
        )

    for planet, position in chart.planets.items():
        name = PLANET_NAMES[planet]
        dignity = _dignity(name, position.zodiac_sign)
        if dignity == "own_sign_and_exalted":
            meaning = f"{name} occupies its traditional own and exaltation sign."
        elif dignity == "own_sign":
            meaning = f"{name} occupies one of its traditional own signs."
        elif dignity == "exalted":
            meaning = f"{name} occupies its traditional exaltation sign."
        elif dignity == "debilitated":
            meaning = f"{name} occupies its traditional debilitation sign."
        elif name in {"Rahu", "Ketu"}:
            meaning = (
                "No dignity status is assigned: node exaltation and debilitation "
                "schemes are disputed across traditions."
            )
        else:
            meaning = (
                f"{name} is in {position.zodiac_sign}; this mapping does not assign "
                "own-sign, exaltation, or debilitation dignity there."
            )
        rules.append(
            _rule(
                rule_id=f"relationship.dignity.{planet}",
                name=f"{name} sign dignity",
                factors=[
                    f"{name} in {position.zodiac_sign}",
                    *[
                        f"status: {status}"
                        for status in dignity.split("_and_")
                    ],
                ],
                meaning=meaning,
                reasoning=[f"Dignity is looked up from the sidereal D1 sign: {position.zodiac_sign}."],
                domains=[],
                source=CLASSICAL_RELATIONSHIP_SOURCE,
                limitations=[
                    "This reports sign dignity only; it does not calculate shadbala, avasthas, combustion, or exact exaltation degrees.",
                    "Node dignity schemes are disputed and deliberately not asserted.",
                    *GENERAL_LIMITATIONS,
                ],
            )
        )

    groups: dict[int, list[str]] = {}
    for key, position in chart.planets.items():
        groups.setdefault(position.house, []).append(PLANET_NAMES[key])
    for house, planets in groups.items():
        if len(planets) > 1:
            rules.append(
                _rule(
                    rule_id=f"relationship.conjunction.house_{house}",
                    name=f"Whole-sign conjunction in house {house}",
                    factors=[f"{planet} in house {house}" for planet in planets],
                    meaning=(
                        "Planets sharing a D1 sign are traditionally treated as joined "
                        "in sign; their topics are read together."
                    ),
                    reasoning=[f"{', '.join(planets)} occupy the same whole-sign house {house}."],
                    domains=[],
                    source=CLASSICAL_RELATIONSHIP_SOURCE,
                    limitations=[
                        "This is sign-based conjunction; no degree-based orb or planetary war is assessed.",
                        *GENERAL_LIMITATIONS,
                    ],
                )
            )

    for source_key, source_position in chart.planets.items():
        source_name = PLANET_NAMES[source_key]
        offsets = CLASSICAL_GRAHA_ASPECTS.get(source_name)
        if offsets is None:
            continue
        for offset in offsets:
            target_house = (source_position.house - 1 + offset - 1) % 12 + 1
            occupants = [
                PLANET_NAMES[key]
                for key, position in chart.planets.items()
                if key != source_key and position.house == target_house
            ]
            rules.append(
                _rule(
                    rule_id=(
                        f"relationship.drishti.{source_name.lower()}."
                        f"house_{target_house}"
                    ),
                    name=f"{source_name} graha drishti to house {target_house}",
                    factors=[
                        f"{source_name} in house {source_position.house}",
                        f"classical aspect offset: {offset} houses",
                        f"occupied by: {', '.join(occupants) or 'no other planets'}",
                    ],
                    meaning=(
                        f"{source_name}'s traditional full graha drishti reaches "
                        f"whole-sign house {target_house}."
                    ),
                    reasoning=[
                        f"The {source_name} aspect offset of {offset} houses reaches house {target_house}.",
                    ],
                    domains=[],
                    source=CLASSICAL_RELATIONSHIP_SOURCE,
                    limitations=[
                        "Rahu/Ketu aspects are omitted because accepted schemes differ.",
                        "Aspect strength and degree-based closeness are not calculated.",
                        *GENERAL_LIMITATIONS,
                    ],
                )
            )
    return rules


def _is_connected(first: str, second: str, chart: ChartResponse) -> list[str]:
    return _associated(first, second, chart.planets)


def _yoga_rules(chart: ChartResponse) -> list[InterpretationRule]:
    lords = _house_lords(chart)
    owned = _owned_houses(chart)
    rules: list[InterpretationRule] = []

    for planet, houses in owned.items():
        kendra_houses = sorted(set(houses) & {4, 7, 10})
        trikona_houses = sorted(set(houses) & {5, 9})
        if kendra_houses and trikona_houses:
            rules.append(
                _rule(
                    rule_id=f"yoga.raja.single.{planet.lower()}",
                    name="Single-planet Kendra–trikona Raja Yoga",
                    factors=[
                        f"{planet} owns non-Lagna kendra house(s) {kendra_houses}",
                        f"{planet} owns trikona house(s) {trikona_houses}",
                    ],
                    meaning=(
                        "A single planet owning both a non-Lagna kendra and a trikona "
                        "is treated in traditional Raja Yoga doctrine as a combined "
                        "kendra–trikona lord."
                    ),
                    reasoning=[
                        f"{planet} owns both house groups without requiring a second-planet association."
                    ],
                    domains=[LifeDomain.CAREER, LifeDomain.PERSONALITY],
                    source=CLASSICAL_YOGA_SOURCE,
                    limitations=[
                        "A shared lordship is a yoga condition, not a guaranteed outcome.",
                        "Strength, combustion, dignity, affliction, and dasha activation are not fully assessed.",
                        *GENERAL_LIMITATIONS,
                    ],
                )
            )

    kendra_lords = {
        lords[house]
        for house in KENDRA_HOUSES
        if lords[house].lower() in chart.planets
    }
    trikona_lords = {
        lords[house]
        for house in TRIKONA_HOUSES
        if lords[house].lower() in chart.planets
    }
    for kendra_lord, trikona_lord in combinations(
        sorted(kendra_lords | trikona_lords), 2
    ):
        if not (
            (kendra_lord in kendra_lords and trikona_lord in trikona_lords)
            or (trikona_lord in kendra_lords and kendra_lord in trikona_lords)
        ):
            continue
        connections = _is_connected(kendra_lord, trikona_lord, chart)
        if connections:
            rules.append(
                _rule(
                    rule_id=f"yoga.raja.{kendra_lord.lower()}.{trikona_lord.lower()}",
                    name="Kendra–trikona Raja Yoga association",
                    factors=[
                        f"{kendra_lord} owns kendra house(s) "
                        f"{sorted(set(owned[kendra_lord]) & KENDRA_HOUSES)}",
                        f"{trikona_lord} owns trikona house(s) "
                        f"{sorted(set(owned[trikona_lord]) & TRIKONA_HOUSES)}",
                        *connections,
                    ],
                    meaning=(
                        "Traditional Raja Yoga doctrine associates connected kendra "
                        "and trikona lords with support for authority, responsibility, "
                        "or recognized achievement."
                    ),
                    reasoning=connections,
                    domains=[LifeDomain.CAREER, LifeDomain.PERSONALITY],
                    source=CLASSICAL_YOGA_SOURCE,
                    limitations=[
                        "A yoga name denotes a traditional combination, not a guaranteed outcome.",
                        "Strength, combustion, dignity, affliction, and dasha activation are not fully assessed.",
                        *GENERAL_LIMITATIONS,
                    ],
                )
            )

    accumulation_lords = {lords[2], lords[11]}
    trikona_wealth_lords = {lords[5], lords[9]}
    for first in sorted(accumulation_lords):
        for second in sorted(trikona_wealth_lords - {first}):
            first_topics = sorted(set(owned[first]) & {2, 11})
            second_topics = sorted(set(owned[second]) & {5, 9})
            connections = _is_connected(first, second, chart)
            if connections:
                rules.append(
                    _rule(
                        rule_id=f"yoga.dhana.{first.lower()}.{second.lower()}",
                        name="Dhana Yoga house-lord association",
                        factors=[
                            f"{first} owns accumulation house(s) {first_topics}",
                            f"{second} owns trikona house(s) {second_topics}",
                            *connections,
                        ],
                        meaning=(
                            "This conservative Dhana Yoga check links a 2nd/11th "
                            "house lord with a 5th/9th house lord by association."
                        ),
                        reasoning=connections,
                        domains=[LifeDomain.WEALTH],
                        source=CLASSICAL_YOGA_SOURCE,
                        limitations=[
                            "Only conjunction, classical graha drishti, or sign exchange between the two lord groups is tested.",
                            "It is not a forecast of income, assets, or financial security.",
                            *GENERAL_LIMITATIONS,
                        ],
                    )
                )

    mahapurusha = {
        "Mars": ("Ruchaka", ("Aries", "Scorpio", "Capricorn")),
        "Mercury": ("Bhadra", ("Gemini", "Virgo")),
        "Jupiter": ("Hamsa", ("Sagittarius", "Pisces", "Cancer")),
        "Venus": ("Malavya", ("Taurus", "Libra", "Pisces")),
        "Saturn": ("Sasa", ("Capricorn", "Aquarius", "Libra")),
    }
    for planet, (yoga_name, qualifying_signs) in mahapurusha.items():
        position = _placement(chart, planet)
        if (
            position is not None
            and position.house in KENDRA_HOUSES
            and position.zodiac_sign in qualifying_signs
        ):
            rules.append(
                _rule(
                    rule_id=f"yoga.pancha_mahapurusha.{yoga_name.lower()}",
                    name=f"{yoga_name} Mahapurusha Yoga",
                    factors=[
                        f"{planet} in {position.zodiac_sign}",
                        f"{planet} in kendra house {position.house} from Lagna",
                        "sign condition: own or exaltation sign",
                    ],
                    meaning=(
                        f"{yoga_name} is one of the five Pancha Mahapurusha combinations, "
                        "traditionally formed by a qualifying planet in an own or exaltation "
                        "sign in a kendra from the ascendant."
                    ),
                    reasoning=[
                        f"{planet} is in a qualifying sign and whole-sign kendra {position.house}."
                    ],
                    domains=[LifeDomain.PERSONALITY, LifeDomain.CAREER],
                    source=CLASSICAL_YOGA_SOURCE,
                    limitations=[
                        "The traditional condition is tested in D1 from Lagna; strength and afflictions may modify interpretation.",
                        *GENERAL_LIMITATIONS,
                    ],
                )
            )

    jupiter = _placement(chart, "Jupiter")
    moon = _placement(chart, "Moon")
    if jupiter is not None and moon is not None:
        distance = (jupiter.house - moon.house) % 12 + 1
        if distance in KENDRA_HOUSES:
            rules.append(
                _rule(
                    rule_id="yoga.gaja_kesari",
                    name="Gaja Kesari Yoga",
                    factors=[
                        f"Jupiter in house {jupiter.house}",
                        f"Moon in house {moon.house}",
                        f"Jupiter is {distance} sign(s) from Moon",
                    ],
                    meaning=(
                        "Jupiter in a kendra from the Moon is the commonly used "
                        "Gaja Kesari Yoga condition, traditionally associated with "
                        "learning, reputation, and judgment."
                    ),
                    reasoning=["Jupiter is in a whole-sign kendra counted from the Moon."],
                    domains=[LifeDomain.PERSONALITY, LifeDomain.CAREER],
                    source=CLASSICAL_YOGA_SOURCE,
                    limitations=[
                        "Texts and later schools differ in additional conditions and strength requirements.",
                        "This is a symbolic combination, not a guarantee of status or success.",
                        *GENERAL_LIMITATIONS,
                    ],
                )
            )

    for house in sorted(DUSTHANA_HOUSES):
        planet = lords[house]
        position = _placement(chart, planet)
        if position is not None and position.house in DUSTHANA_HOUSES:
            rules.append(
                _rule(
                    rule_id=f"yoga.vipareeta.{house}.{planet.lower()}",
                    name="Vipareeta Raja Yoga condition",
                    factors=[
                        f"{planet} is lord of dusthana house {house}",
                        f"{planet} occupies dusthana house {position.house}",
                    ],
                    meaning=(
                        "A dusthana lord placed in a dusthana is a condition used in "
                        "Vipareeta Raja Yoga discussions, where difficult circumstances "
                        "may be reframed as opportunities for resilience."
                    ),
                    reasoning=[
                        f"The lord of house {house} occupies dusthana house {position.house}."
                    ],
                    domains=[LifeDomain.PERSONALITY, LifeDomain.CAREER],
                    source=CLASSICAL_YOGA_SOURCE,
                    limitations=[
                        "This flags a broad condition only; association with other dusthana lords and competing influences are not exhaustively assessed.",
                        "No adversity or later success is predicted.",
                        *GENERAL_LIMITATIONS,
                    ],
                )
            )

    for planet, position in chart.planets.items():
        name = PLANET_NAMES[planet]
        if "debilitated" not in _dignity(name, position.zodiac_sign):
            continue
        debility_sign_index = SIGN_INDEX[position.zodiac_sign]
        dispositor = SIGN_LORDS[debility_sign_index]
        exaltation_lord = SIGN_LORDS[
            SIGN_INDEX[EXALTATION_SIGNS[name]]
        ]
        cancellation_factors: list[str] = []
        for candidate, label in (
            (dispositor, "dispositor of debilitation sign"),
            (exaltation_lord, "lord of the planet's exaltation sign"),
        ):
            candidate_position = _placement(chart, candidate)
            if candidate_position is not None and (
                candidate_position.house in KENDRA_HOUSES
                or (moon is not None and (candidate_position.house - moon.house) % 12 + 1 in KENDRA_HOUSES)
            ):
                cancellation_factors.append(
                    f"{label} {candidate} is in a kendra from Lagna or Moon"
                )
        if position.house in KENDRA_HOUSES:
            cancellation_factors.append(
                f"debilitated {name} itself is in a kendra from Lagna"
            )
        if cancellation_factors:
            rules.append(
                _rule(
                    rule_id=f"yoga.neecha_bhanga.{planet}",
                    name="Neecha Bhanga condition",
                    factors=[
                        f"{name} debilitated in {position.zodiac_sign}",
                        *cancellation_factors,
                    ],
                    meaning=(
                        "A listed classical cancellation condition for debility is present; "
                        "Neecha Bhanga is traditionally read as mitigation, not as erasing "
                        "all challenges or guaranteeing a Raja Yoga result."
                    ),
                    reasoning=cancellation_factors,
                    domains=[LifeDomain.PERSONALITY],
                    source=CLASSICAL_YOGA_SOURCE,
                    limitations=[
                        "Neecha Bhanga criteria differ across texts and lineages; this implementation tests a documented subset.",
                        "The separate Neecha Bhanga Raja Yoga judgment requires additional strength and contextual analysis.",
                        *GENERAL_LIMITATIONS,
                    ],
                )
            )
    return rules


def _domain_rules(chart: ChartResponse) -> dict[LifeDomain, InterpretationRule]:
    lords = _house_lords(chart)
    rules: dict[LifeDomain, InterpretationRule] = {}
    for domain, (houses, karakas) in DOMAIN_HOUSES.items():
        factors: list[str] = []
        reasoning: list[str] = []
        for house in houses:
            lord = lords[house]
            position = _placement(chart, lord)
            factors.append(
                f"house {house} lord {lord}"
                + (
                    f" placed in house {position.house} ({position.zodiac_sign})"
                    if position is not None
                    else ""
                )
            )
            reasoning.append(
                f"House {house} is traditionally associated with this domain; its lord is {lord}."
            )
        for planet in karakas:
            position = _placement(chart, planet)
            if position is not None:
                factors.append(
                    f"natural significator {planet} in house {position.house} "
                    f"({position.zodiac_sign}; {_dignity(planet, position.zodiac_sign)})"
                )
        tradition = DOMAIN_TRADITION.get(
            domain, InterpretationTradition.CLASSICAL
        )
        meaning = (
            f"For {domain.value}, classical Jyotisha considers houses "
            f"{', '.join(map(str, houses))}"
            + (
                f" and the natural significators {', '.join(karakas)}."
                if karakas
                else "."
            )
            + " These factors are prompts for contextual reflection, not outcome claims."
        )
        limitations = [
            "This domain summary reports significators and lords only; it does not infer a concrete life event or outcome.",
            "Health content is not medical advice; consult qualified clinicians for health concerns.",
            "Marriage and relationship content does not predict marriage, separation, or another person's choices.",
            "Career and business content does not predict hiring, income, or commercial success.",
            "Children content does not predict fertility or a child's health or future.",
            *GENERAL_LIMITATIONS,
        ]
        rules[domain] = _rule(
            rule_id=f"domain.{domain.value}",
            name=f"{domain.value.title()} significators",
            factors=factors,
            meaning=meaning,
            reasoning=reasoning,
            domains=[domain],
            source=(
                CLASSICAL_BHAVA_SOURCE
                if tradition == InterpretationTradition.CLASSICAL
                else MODERN_DOMAIN_SOURCE
            ),
            limitations=limitations,
            tradition=tradition,
        )
    return rules


def _flatten_periods(periods: list[DashaPeriod]) -> list[DashaPeriod]:
    flattened: list[DashaPeriod] = []
    for period in periods:
        flattened.append(period)
        flattened.extend(_flatten_periods(period.children))
    return flattened


def _dasha_rules(
    chart: ChartResponse,
    sequence: DashaSequence | None,
    as_of: datetime | None,
) -> list[InterpretationRule]:
    if sequence is None:
        return []
    if sequence.chart_id != chart.chart_id:
        raise ValueError("Dasha sequence chart_id must match the supplied chart")
    instant = (as_of or datetime.now(timezone.utc)).astimezone(timezone.utc)
    active = [
        period
        for period in _flatten_periods(sequence.mahadashas)
        if datetime.fromisoformat(period.starts_at.replace("Z", "+00:00"))
        <= instant
        < datetime.fromisoformat(period.ends_at.replace("Z", "+00:00"))
    ]
    active_by_level: dict[str, DashaPeriod] = {}
    for period in active:
        active_by_level[period.level] = period
    if not active_by_level:
        return []

    owned = _owned_houses(chart)
    results: list[InterpretationRule] = []
    for level in ("mahadasha", "antardasha", "pratyantardasha"):
        period = active_by_level.get(level)
        if period is None:
            continue
        planet = period.planet
        position = _placement(chart, planet)
        ruled_houses = owned.get(planet, [])
        factors = [
            f"active {level}: {planet} ({period.starts_at} to {period.ends_at})",
            f"{planet} rules house(s) {ruled_houses}",
        ]
        reasoning = [
            f"The active {level} lord is interpreted from its natal house lordships and D1 placement."
        ]
        domains = [
            domain
            for domain, (houses, karakas) in DOMAIN_HOUSES.items()
            if set(ruled_houses) & set(houses) or planet in karakas
        ]
        if position is not None:
            factors.extend(
                [
                    f"D1 placement: house {position.house}, {position.zodiac_sign}",
                    f"D1 sign dignity: {_dignity(planet, position.zodiac_sign)}",
                ]
            )
        divisions: list[tuple[str, DivisionChart]] = [
            ("D9 Navamsha", chart.d9_navamsa),
        ]
        if set(domains) & {LifeDomain.CAREER, LifeDomain.BUSINESS}:
            divisions.append(("D10 Dashamsha", chart.d10_dashamsa))
        for division_name, division in divisions:
            division_position = next(
                (
                    placement
                    for placement in division.placements
                    if placement.name == planet
                ),
                None,
            )
            if division_position is not None:
                factors.append(
                    f"{division_name}: house {division_position.house}, "
                    f"{division_position.sign}"
                )
        results.append(
            _rule(
                rule_id=f"dasha.{level}.{planet.lower()}",
                name=f"{planet} {level.title()} interpretation factors",
                factors=factors,
                meaning=(
                    f"Traditional Vimshottari interpretation considers {planet}'s "
                    f"period with themes of {PLANETARY_DASHA_THEMES[planet]}, read "
                    "through its natal lordships, D1 placement, and relevant varga "
                    "context. These are interpretive themes, not specific event predictions."
                ),
                reasoning=reasoning,
                domains=domains,
                source=(
                    "BPHS, Vimshottari Dasha and bhava-result sections; chapter numbering "
                    "differs across editions. D9/D10 use traditional corroborative practice."
                ),
                limitations=[
                    "D9 is included as broad corroborative context; D10 is included only when career or business houses/significators are relevant. No varga dignity or yoga is inferred here.",
                    "The Sukshma period is omitted from interpretive summaries to avoid overstating fine-grained timing.",
                    "Dasha periods are traditional timing frameworks, not validated event predictions.",
                    *GENERAL_LIMITATIONS,
                ],
            )
        )
    return results


def interpret_chart(
    chart: ChartResponse,
    *,
    dashas: DashaSequence | None = None,
    as_of: datetime | None = None,
) -> ChartInterpretationResponse:
    return ChartInterpretationResponse(
        chart_id=chart.chart_id,
        astronomical_facts=chart,
        interpretation_notice=(
            "Astronomical positions and house placements are supplied facts from the "
            "calculation engine; rules below are separate traditional interpretations. "
            "They are not scientifically validated predictions. No probabilities are "
            "assigned, and no deterministic death, disease, relationship-breakdown, "
            "or employment predictions are produced."
        ),
        relationship_rules=_relationship_rules(chart),
        yogas=_yoga_rules(chart),
        domains=_domain_rules(chart),
        active_dasha_rules=_dasha_rules(chart, dashas, as_of),
    )

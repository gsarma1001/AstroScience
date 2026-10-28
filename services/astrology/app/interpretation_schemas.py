from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.dasha_schemas import DashaSequence
from app.schemas import ChartResponse


class LifeDomain(StrEnum):
    PERSONALITY = "personality"
    CAREER = "career"
    BUSINESS = "business"
    MARRIAGE = "marriage"
    CHILDREN = "children"
    HEALTH = "health"
    WEALTH = "wealth"
    RELOCATION = "relocation"
    SPIRITUALITY = "spirituality"


class InterpretationTradition(StrEnum):
    CLASSICAL = "classical"
    MODERN_SYNTHESIS = "modern_synthesis"


class InterpretationRule(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    rule_id: str
    rule_name: str
    tradition: InterpretationTradition
    chart_factors_used: list[str]
    traditional_meaning: str
    supporting_reasoning: list[str]
    relevant_life_domains: list[LifeDomain]
    source_reference: str
    limitations_or_conflicting_factors: list[str]


class ChartInterpretationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart: ChartResponse
    dashas: DashaSequence | None = None
    as_of: datetime | None = None

    @model_validator(mode="after")
    def require_complete_chart_positions(self) -> ChartInterpretationRequest:
        expected = {
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
        if set(self.chart.planets) != expected:
            raise ValueError("chart must contain the nine supported planetary positions")
        return self

    @field_validator("as_of")
    @classmethod
    def require_aware_as_of(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("as_of must include a timezone")
        return value


class ChartInterpretationResponse(BaseModel):
    chart_id: UUID
    astronomical_facts: ChartResponse
    interpretation_notice: str
    relationship_rules: list[InterpretationRule]
    yogas: list[InterpretationRule]
    domains: dict[LifeDomain, InterpretationRule]
    active_dasha_rules: list[InterpretationRule]

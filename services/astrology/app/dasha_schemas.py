from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


DashaLevel = Literal[
    "mahadasha",
    "antardasha",
    "pratyantardasha",
    "sukshma",
]


class DashaParent(BaseModel):
    period_id: str
    level: DashaLevel
    planet: str


class DashaPeriod(BaseModel):
    period_id: str
    level: DashaLevel
    planet: str
    starts_at: str
    ends_at: str
    duration_seconds: float
    duration_years: float
    parent_period: DashaParent | None
    children: list[DashaPeriod] = Field(default_factory=list)


DashaPeriod.model_rebuild()


class DashaSequence(BaseModel):
    chart_id: UUID
    moon_sidereal_longitude: float
    birth_nakshatra: str
    nakshatra_lord: str
    elapsed_nakshatra_fraction: float
    balance_at_birth_years: float
    year_length_days: float
    year_length_convention: str
    sequence_starts_at: str
    sequence_ends_at: str
    mahadashas: list[DashaPeriod]

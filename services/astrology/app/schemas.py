from __future__ import annotations

from datetime import date, time
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Ayanamsa(StrEnum):
    LAHIRI = "lahiri"
    RAMAN = "raman"
    KRISHNAMURTI = "krishnamurti"


class NodeType(StrEnum):
    MEAN = "mean"
    TRUE = "true"


class ChartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    birth_date: date
    birth_time: time
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    timezone: Annotated[str, Field(min_length=1, max_length=64)]
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    node_type: NodeType = NodeType.MEAN
    fold: int | None = Field(default=None, ge=0, le=1)

    @field_validator("birth_time")
    @classmethod
    def require_local_wall_time(cls, value: time) -> time:
        if value.tzinfo is not None:
            raise ValueError("birth_time must be a local wall time without an offset")
        return value


class PlanetPosition(BaseModel):
    name: str
    sidereal_longitude: float
    zodiac_sign: str
    degree_in_sign: float
    house: int
    nakshatra: str
    nakshatra_pada: int
    retrograde: bool | None


class ChartHouse(BaseModel):
    number: int
    sign: str
    occupants: list[str]


class DivisionChart(BaseModel):
    division: str
    ascendant_sign: str
    houses: list[ChartHouse]


class ChartProvenance(BaseModel):
    utc_birth_timestamp: str
    latitude: float
    longitude: float
    timezone: str
    ayanamsa: Ayanamsa
    ayanamsa_degrees: float
    node_type: NodeType
    ephemeris_version: str
    ephemeris_source: str
    calculation_engine_version: str


class ChartResponse(BaseModel):
    chart_id: UUID
    provenance: ChartProvenance
    ascendant: PlanetPosition
    planets: dict[str, PlanetPosition]
    moon_rashi: str
    lagna: str
    birth_nakshatra: str
    nakshatra_lord: str
    tithi: dict[str, str | int | float]
    d1_rashi_chart: DivisionChart
    d9_navamsa: DivisionChart
    d10_dashamsa: DivisionChart


class ErrorResponse(BaseModel):
    detail: str

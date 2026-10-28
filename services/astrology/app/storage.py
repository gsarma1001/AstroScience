from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Date, Float, Integer, String, Uuid, create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.schemas import ChartRequest, ChartResponse

DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "nakshatra_charts.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DATABASE.as_posix()}")
_connect_args: dict[str, Any] = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite:") else {}
)
engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class CalculatedChart(Base):
    __tablename__ = "calculated_charts"

    chart_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    utc_birth_timestamp: Mapped[str] = mapped_column(String(40), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    ayanamsa: Mapped[str] = mapped_column(String(32), nullable=False)
    ephemeris_version: Mapped[str] = mapped_column(String(32), nullable=False)
    calculation_engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    result_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )


def create_schema() -> None:
    Base.metadata.create_all(engine)


def persist_chart(request: ChartRequest, result: ChartResponse) -> None:
    provenance = result.provenance
    record = CalculatedChart(
        chart_id=result.chart_id,
        utc_birth_timestamp=provenance.utc_birth_timestamp,
        latitude=request.latitude,
        longitude=request.longitude,
        timezone=request.timezone,
        ayanamsa=provenance.ayanamsa.value,
        ephemeris_version=provenance.ephemeris_version,
        calculation_engine_version=provenance.calculation_engine_version,
        result_json=result.model_dump(mode="json"),
    )
    with SessionLocal.begin() as session:
        session.add(record)

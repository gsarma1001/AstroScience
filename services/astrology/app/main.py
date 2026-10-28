from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.calculations import (
    EphemerisCalculationError,
    InvalidBirthTime,
    calculate_chart,
)
from app.dashas import calculate_vimshottari_sequence
from app.dasha_schemas import DashaSequence
from app.interpretation_schemas import (
    ChartInterpretationRequest,
    ChartInterpretationResponse,
)
from app.interpretations import interpret_chart
from app.schemas import ChartRequest, ChartResponse
from app.storage import create_schema, get_stored_chart, persist_chart

_LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_schema()
    yield


app = FastAPI(
    title="Nakshatra AI Astrology API",
    version="0.1.0",
    description="Deterministic Jyotisha chart calculations using Swiss Ephemeris.",
    lifespan=lifespan,
)
_cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        "NAKSHATRA_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/chart/interpretations",
    response_model=ChartInterpretationResponse,
)
def get_chart_interpretations(
    request: ChartInterpretationRequest,
) -> ChartInterpretationResponse:
    try:
        return interpret_chart(
            request.chart,
            dashas=request.dashas,
            as_of=request.as_of,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post(
    "/api/chart/calculate",
    response_model=ChartResponse,
    status_code=status.HTTP_201_CREATED,
)
def calculate_birth_chart(request: ChartRequest) -> ChartResponse:
    try:
        result = calculate_chart(request)
    except InvalidBirthTime as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EphemerisCalculationError as exc:
        _LOGGER.exception("Chart calculation failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        persist_chart(request, result)
    except SQLAlchemyError as exc:
        _LOGGER.exception("Chart persistence failed")
        raise HTTPException(
            status_code=503,
            detail="Chart could not be stored. Check database configuration and availability.",
        ) from exc
    return result


@app.get("/api/chart/{chart_id}/dashas", response_model=DashaSequence)
def get_chart_dashas(chart_id: UUID) -> DashaSequence:
    try:
        stored_chart = get_stored_chart(chart_id)
    except SQLAlchemyError as exc:
        _LOGGER.exception("Chart lookup failed")
        raise HTTPException(
            status_code=503,
            detail="Chart data could not be loaded. Check database configuration and availability.",
        ) from exc
    if stored_chart is None:
        raise HTTPException(status_code=404, detail="Calculated chart not found")
    try:
        chart = ChartResponse.model_validate(stored_chart)
        moon = chart.planets["moon"]
        return calculate_vimshottari_sequence(
            chart_id=chart.chart_id,
            birth_timestamp=chart.provenance.utc_birth_timestamp,
            moon_sidereal_longitude=moon.sidereal_longitude,
        )
    except (KeyError, ValueError) as exc:
        _LOGGER.exception("Stored chart is missing valid Moon dasha inputs")
        raise HTTPException(
            status_code=500, detail="Stored chart is missing valid dasha calculation data"
        ) from exc

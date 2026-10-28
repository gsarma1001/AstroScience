from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.calculations import (
    EphemerisCalculationError,
    InvalidBirthTime,
    calculate_chart,
)
from app.schemas import ChartRequest, ChartResponse
from app.storage import create_schema, persist_chart

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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

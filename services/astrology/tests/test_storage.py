from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.storage as storage
from app.calculations import calculate_chart
from app.schemas import ChartRequest


def test_chart_provenance_and_result_are_persisted(monkeypatch) -> None:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    storage.Base.metadata.create_all(test_engine)
    test_session = sessionmaker(bind=test_engine, expire_on_commit=False)
    monkeypatch.setattr(storage, "SessionLocal", test_session)

    request = ChartRequest(
        birth_date="1990-01-15",
        birth_time="12:30:00",
        latitude=19.076,
        longitude=72.8777,
        timezone="Asia/Kolkata",
    )
    result = calculate_chart(request)
    storage.persist_chart(request, result)

    with test_session() as session:
        stored = session.scalar(
            select(storage.CalculatedChart).where(
                storage.CalculatedChart.chart_id == result.chart_id
            )
        )

    assert stored is not None
    assert stored.utc_birth_timestamp == "1990-01-15T07:00:00Z"
    assert stored.latitude == request.latitude
    assert stored.longitude == request.longitude
    assert stored.timezone == request.timezone
    assert stored.ayanamsa == "lahiri"
    assert stored.ephemeris_version == result.provenance.ephemeris_version
    assert stored.calculation_engine_version == "0.1.0"
    assert stored.result_json["chart_id"] == str(result.chart_id)

    test_engine.dispose()

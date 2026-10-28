from fastapi.testclient import TestClient

import app.main as main
from app.calculations import calculate_chart
from app.schemas import ChartRequest


def test_calculate_endpoint_returns_chart_and_persists_metadata(monkeypatch) -> None:
    saved = []
    monkeypatch.setattr(main, "create_schema", lambda: None)
    monkeypatch.setattr(main, "persist_chart", lambda request, result: saved.append((request, result)))

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/calculate",
            json={
                "birth_date": "1990-01-15",
                "birth_time": "12:30:00",
                "latitude": 19.076,
                "longitude": 72.8777,
                "timezone": "Asia/Kolkata",
            },
        )

    assert response.status_code == 201
    body = response.json()
    assert body["provenance"]["timezone"] == "Asia/Kolkata"
    assert body["provenance"]["utc_birth_timestamp"] == "1990-01-15T07:00:00Z"
    assert body["provenance"]["ayanamsa"] == "lahiri"
    assert body["provenance"]["ephemeris_source"] in {
        "swiss_ephemeris",
        "moshier_fallback",
    }
    for chart_key in ("d1_rashi_chart", "d9_navamsa", "d10_dashamsa"):
        division_chart = body[chart_key]
        assert len(division_chart["placements"]) == 10
        assert division_chart["placements"][0]["name"] == "Ascendant"
        assert division_chart["placements"][0]["house"] == 1
        assert all(
            0 <= placement["degree_in_sign"] < 30
            for placement in division_chart["placements"]
        )
    assert len(saved) == 1


def test_invalid_timezone_is_reported_as_client_error(monkeypatch) -> None:
    monkeypatch.setattr(main, "create_schema", lambda: None)
    monkeypatch.setattr(main, "persist_chart", lambda request, result: None)

    with TestClient(main.app) as client:
        response = client.post(
            "/api/chart/calculate",
            json={
                "birth_date": "1990-01-15",
                "birth_time": "12:30:00",
                "latitude": 19.076,
                "longitude": 72.8777,
                "timezone": "Not/A-Timezone",
            },
        )

    assert response.status_code == 422
    assert "Unknown IANA timezone" in response.json()["detail"]


def test_dasha_endpoint_returns_complete_sequence_from_stored_chart(monkeypatch) -> None:
    chart = calculate_chart(
        ChartRequest(
            birth_date="2000-01-01",
            birth_time="12:00:00",
            latitude=0,
            longitude=0,
            timezone="UTC",
        )
    )
    monkeypatch.setattr(main, "create_schema", lambda: None)
    monkeypatch.setattr(
        main, "get_stored_chart", lambda chart_id: chart.model_dump(mode="json")
    )

    with TestClient(main.app) as client:
        response = client.get(f"/api/chart/{chart.chart_id}/dashas")

    assert response.status_code == 200
    body = response.json()
    assert body["chart_id"] == str(chart.chart_id)
    assert body["moon_sidereal_longitude"] == chart.planets["moon"].sidereal_longitude
    assert len(body["mahadashas"]) == 9
    maha = body["mahadashas"][0]
    assert len(maha["children"]) == 9
    antara = maha["children"][0]
    assert antara["parent_period"]["period_id"] == maha["period_id"]
    assert len(antara["children"][0]["children"][0]["children"]) == 0
    assert body["year_length_days"] == 365.25


def test_dasha_endpoint_reports_missing_chart(monkeypatch) -> None:
    monkeypatch.setattr(main, "create_schema", lambda: None)
    monkeypatch.setattr(main, "get_stored_chart", lambda chart_id: None)

    with TestClient(main.app) as client:
        response = client.get(
            "/api/chart/00000000-0000-0000-0000-000000000000/dashas"
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculated chart not found"


def test_frontend_origin_can_read_dasha_api() -> None:
    with TestClient(main.app) as client:
        response = client.options(
            "/api/chart/00000000-0000-0000-0000-000000000000/dashas",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

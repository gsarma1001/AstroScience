from fastapi.testclient import TestClient

import app.main as main


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

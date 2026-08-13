from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok_status():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "db_connected" in body


def test_live_returns_ok_without_checking_db():
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

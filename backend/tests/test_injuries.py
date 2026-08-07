import pytest


@pytest.fixture()
def user_id(client):
    return client.post("/users", json={"name": "Injury Test User"}).json()["id"]


def test_create_and_list_injury(client, user_id):
    response = client.post(
        "/injuries",
        json={
            "user_id": user_id,
            "injury_type": "ankle sprain",
            "date_occurred": "2026-07-20",
            "severity": "moderate",
            "recovery_exercises": ["ankle circles", "calf raises"],
            "restrictions": "no running for 2 weeks",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "active"

    list_response = client.get("/injuries", params={"user_id": user_id})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_update_injury_status_to_recovered(client, user_id):
    created = client.post(
        "/injuries",
        json={
            "user_id": user_id,
            "injury_type": "hamstring strain",
            "date_occurred": "2026-06-01",
            "severity": "mild",
        },
    ).json()

    response = client.patch(f"/injuries/{created['id']}", json={"status": "recovered"})
    assert response.status_code == 200
    assert response.json()["status"] == "recovered"

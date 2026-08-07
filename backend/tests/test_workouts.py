import pytest


@pytest.fixture()
def user_id(client):
    return client.post("/users", json={"name": "Coach Test User"}).json()["id"]


def test_create_generic_workout(client, user_id):
    response = client.post(
        "/workouts",
        json={
            "user_id": user_id,
            "date": "2026-08-01",
            "exercise_type": "strength",
            "sets": 4,
            "reps": 8,
            "weight_kg": 60,
            "notes": "Squats",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["exercise_type"] == "strength"
    assert body["football_session"] is None


def test_create_football_workout_with_nested_session(client, user_id):
    response = client.post(
        "/workouts",
        json={
            "user_id": user_id,
            "date": "2026-08-02",
            "exercise_type": "football",
            "duration_minutes": 90,
            "football": {
                "position": "midfielder",
                "match_duration_minutes": 90,
                "intensity": "high",
                "performance_notes": "Good stamina",
                "injuries_flagged": False,
            },
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["football_session"]["position"] == "midfielder"
    assert body["hyrox_session"] is None


def test_create_hyrox_workout_with_nested_session(client, user_id):
    response = client.post(
        "/workouts",
        json={
            "user_id": user_id,
            "date": "2026-08-03",
            "exercise_type": "hyrox",
            "hyrox": {
                "ski_erg_seconds": 240,
                "sled_push_seconds": 90,
                "wall_balls_reps": 100,
            },
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["hyrox_session"]["sled_push_seconds"] == 90


def test_create_workout_for_unknown_user_returns_404(client):
    response = client.post(
        "/workouts",
        json={"user_id": 999999, "date": "2026-08-01", "exercise_type": "cardio"},
    )
    assert response.status_code == 404


def test_list_workouts_filters_by_exercise_type_and_date_range(client, user_id):
    client.post(
        "/workouts",
        json={"user_id": user_id, "date": "2026-07-01", "exercise_type": "running"},
    )
    client.post(
        "/workouts",
        json={"user_id": user_id, "date": "2026-08-01", "exercise_type": "running"},
    )
    client.post(
        "/workouts",
        json={"user_id": user_id, "date": "2026-08-02", "exercise_type": "strength"},
    )

    response = client.get(
        "/workouts",
        params={
            "user_id": user_id,
            "exercise_type": "running",
            "date_from": "2026-07-15",
        },
    )
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["date"] == "2026-08-01"

def test_create_and_get_user(client):
    response = client.post(
        "/users",
        json={
            "name": "Wesley",
            "age": 30,
            "height_cm": 178,
            "weight_kg": 75,
            "goals": ["gain muscle", "improve hyrox sled push"],
            "sports_played": ["football", "hyrox"],
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Wesley"
    assert created["sports_played"] == ["football", "hyrox"]

    get_response = client.get(f"/users/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Wesley"


def test_get_missing_user_returns_404(client):
    response = client.get("/users/999999")
    assert response.status_code == 404


def test_update_user_patches_only_provided_fields(client):
    created = client.post("/users", json={"name": "Alex", "age": 25}).json()

    response = client.patch(f"/users/{created['id']}", json={"age": 26})
    assert response.status_code == 200
    body = response.json()
    assert body["age"] == 26
    assert body["name"] == "Alex"


def test_delete_user(client):
    created = client.post("/users", json={"name": "Temp"}).json()

    response = client.delete(f"/users/{created['id']}")
    assert response.status_code == 204

    assert client.get(f"/users/{created['id']}").status_code == 404

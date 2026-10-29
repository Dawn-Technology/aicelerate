from fastapi.testclient import TestClient

from app.main import app, store

client = TestClient(app)


def setup_function() -> None:
    store._customers.clear()


def test_create_and_get_customer() -> None:
    created = client.post(
        "/customers",
        json={"id": 1, "name": "Acme", "email": "ops@acme.test", "city": "Utrecht"},
    )
    assert created.status_code == 201

    fetched = client.get("/customers/1")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Acme"


def test_missing_customer_is_404() -> None:
    assert client.get("/customers/99").status_code == 404

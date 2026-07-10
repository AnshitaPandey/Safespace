from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_me_requires_auth():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403  # no Authorization header supplied


def test_register_rejects_short_password():
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "short"},
    )
    assert response.status_code == 422  # Pydantic min_length=8 validation


def test_login_wrong_shape_rejected():
    response = client.post("/api/v1/auth/login", json={"email": "not-an-email"})
    assert response.status_code == 422

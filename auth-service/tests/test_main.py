import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with patch("psycopg2.connect", return_value=MagicMock()):
    from app.main import app
    from app import database, auth


@pytest.fixture
def client():
    return TestClient(app)


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Auth Service running"}


def test_register_user(client):
    with patch.object(database, "get_user_by_username", return_value=None), \
         patch.object(database, "create_user"):
        resp = client.post("/register", json={"username": "testuser", "password": "testpass123"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "User registered successfully"

    with patch.object(database, "get_user_by_username", return_value={"id": 1, "username": "testuser"}):
        resp = client.post("/register", json={"username": "testuser", "password": "testpass123"})
    assert resp.status_code == 400
    assert "Username already exists" in resp.json()["detail"]


def test_login_user(client):
    hashed = auth.hash_password("testpass123")
    fake_user = {"id": 1, "username": "testuser", "password_hash": hashed, "role": "user"}

    with patch.object(database, "get_user_by_username", return_value=fake_user):
        resp = client.post("/login", json={"username": "testuser", "password": "testpass123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    payload = auth.verify_jwt(token)
    assert payload["username"] == "testuser"
    assert "user_id" in payload
    assert payload["role"] == "user"

    with patch.object(database, "get_user_by_username", return_value=fake_user):
        resp = client.post("/login", json={"username": "testuser", "password": "wrongpass"})
    assert resp.status_code == 400
    assert "Invalid username or password" in resp.json()["detail"]

    with patch.object(database, "get_user_by_username", return_value=None):
        resp = client.post("/login", json={"username": "noone", "password": "nopass"})
    assert resp.status_code == 400
    assert "Invalid username or password" in resp.json()["detail"]

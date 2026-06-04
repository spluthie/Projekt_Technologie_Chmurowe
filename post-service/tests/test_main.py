import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with patch("psycopg2.connect", return_value=MagicMock()):
    from app.main import app
    from app import database, auth


FAKE_POST = {
    "id": 1,
    "user_id": 1,
    "username": "testuser",
    "content": "Hello World!",
    "created_at": "2024-01-01T00:00:00",
}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_header():
    payload = {
        "user_id": 1,
        "username": "testuser",
        "role": "user",
        "exp": datetime.utcnow() + timedelta(minutes=60),
    }
    token = jwt.encode(payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
    return {"authorization": f"Bearer {token}"}


def test_create_post(client, auth_header):
    with patch.object(database, "create_post") as mock_create:
        resp = client.post("/posts", json={"content": "Hello World!"}, headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post created"
    mock_create.assert_called_once()


def test_read_posts(client):
    with patch.object(database, "get_posts", return_value=[FAKE_POST]):
        resp = client.get("/posts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1
    assert resp.json()[0]["content"] == "Hello World!"


def test_read_single_post(client):
    with patch.object(database, "get_post", return_value=FAKE_POST):
        resp = client.get("/posts/1")
    assert resp.status_code == 200
    assert resp.json()["content"] == "Hello World!"


def test_update_post(client, auth_header):
    with patch.object(database, "get_post", return_value=FAKE_POST), \
         patch.object(database, "update_post") as mock_update:
        resp = client.put("/posts/1", json={"content": "Updated Content"}, headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post updated"
    mock_update.assert_called_once()


def test_delete_post(client, auth_header):
    with patch.object(database, "get_post", return_value=FAKE_POST), \
         patch.object(database, "delete_post") as mock_delete:
        resp = client.delete("/posts/1", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post deleted"
    mock_delete.assert_called_once()

    with patch.object(database, "get_post", return_value=None):
        resp = client.get("/posts/1")
    assert resp.status_code == 404

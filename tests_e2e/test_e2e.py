import sys
import os
import pytest
import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import jwt

os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load auth-service in isolation
sys.path.insert(0, os.path.join(BASE_DIR, "../auth-service"))
with patch("psycopg2.connect", return_value=MagicMock()):
    import app.main as _auth_main
    import app.database as auth_database
    import app.auth as auth_lib
    auth_app = _auth_main.app

# Clear app.* from module cache before loading post-service
for _key in list(sys.modules):
    if _key == "app" or _key.startswith("app."):
        del sys.modules[_key]
sys.path.pop(0)

# Load post-service in isolation
sys.path.insert(0, os.path.join(BASE_DIR, "../post-service"))
with patch("psycopg2.connect", return_value=MagicMock()):
    import app.main as _post_main
    import app.database as post_database
    post_app = _post_main.app

for _key in list(sys.modules):
    if _key == "app" or _key.startswith("app."):
        del sys.modules[_key]
sys.path.pop(0)

auth_client = TestClient(auth_app)
post_client = TestClient(post_app)

FAKE_POST = {
    "id": 1,
    "user_id": 1,
    "username": "e2euser",
    "content": "Hello E2E",
    "created_at": "2024-01-01T00:00:00",
}


@pytest.fixture
def registered_user():
    hashed = auth_lib.hash_password("password123")
    return {"id": 1, "username": "e2euser", "password_hash": hashed, "role": "user"}


@pytest.fixture
def user_token():
    payload = {
        "user_id": 1,
        "username": "e2euser",
        "role": "user",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
    }
    token = jwt.encode(payload, auth_lib.SECRET_KEY, algorithm=auth_lib.ALGORITHM)
    return f"Bearer {token}"


def test_register_and_login(registered_user):
    with patch.object(auth_database, "get_user_by_username", return_value=None), \
         patch.object(auth_database, "create_user"):
        resp = auth_client.post("/register", json={"username": "e2euser", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "User registered successfully"

    with patch.object(auth_database, "get_user_by_username", return_value=registered_user):
        resp = auth_client.post("/login", json={"username": "e2euser", "password": "password123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    payload = auth_lib.verify_jwt(token)
    assert payload["username"] == "e2euser"


def test_token_from_auth_works_in_post_service(registered_user):
    # Get real token from auth-service login
    with patch.object(auth_database, "get_user_by_username", return_value=registered_user):
        resp = auth_client.post("/login", json={"username": "e2euser", "password": "password123"})
    token = resp.json()["access_token"]

    # Use that token to create a post in post-service
    with patch.object(post_database, "create_post") as mock_create:
        resp = post_client.post(
            "/posts",
            json={"content": "Hello E2E"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post created"
    mock_create.assert_called_once()


def test_create_post(user_token):
    with patch.object(post_database, "create_post") as mock_create:
        resp = post_client.post("/posts", json={"content": "Hello E2E"}, headers={"Authorization": user_token})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post created"
    mock_create.assert_called_once()


def test_read_posts():
    with patch.object(post_database, "get_posts", return_value=[FAKE_POST]):
        resp = post_client.get("/posts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 1
    assert resp.json()[0]["content"] == "Hello E2E"


def test_update_and_delete_post(user_token):
    with patch.object(post_database, "get_post", return_value=FAKE_POST), \
         patch.object(post_database, "update_post") as mock_update:
        resp = post_client.put("/posts/1", json={"content": "Updated!"}, headers={"Authorization": user_token})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post updated"
    mock_update.assert_called_once()

    with patch.object(post_database, "get_post", return_value=FAKE_POST), \
         patch.object(post_database, "delete_post") as mock_delete:
        resp = post_client.delete("/posts/1", headers={"Authorization": user_token})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post deleted"
    mock_delete.assert_called_once()

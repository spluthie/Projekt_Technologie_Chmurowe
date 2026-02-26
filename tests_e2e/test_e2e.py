# tests_e2e/test_e2e.py
import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add service folders to sys.path manually (because of hyphens)
sys.path.append(os.path.join(os.path.dirname(__file__), "../auth-service"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../post-service"))

# Now we can import main.py from each service
from app.main import app as auth_app
from app.main import app as post_app
from app import auth as auth_lib  # for JWT secret if needed

auth_client = TestClient(auth_app)
post_client = TestClient(post_app)


@pytest.fixture
def user_token():
    # Create a fake token for testing post-service
    payload = {
        "user_id": 1,
        "username": "testuser",
        "role": "user",
        "exp": __import__("datetime").datetime.utcnow() + __import__("datetime").timedelta(minutes=60)
    }
    import jwt
    token = jwt.encode(payload, auth_lib.SECRET_KEY, algorithm=auth_lib.ALGORITHM)
    return f"Bearer {token}"


def test_register_and_login():
    # Register user
    response = auth_client.post("/register", json={"username": "e2euser", "password": "password123"})
    assert response.status_code in [200, 400]  # 400 if already exists

    # Login
    response = auth_client.post("/login", json={"username": "e2euser", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_create_post(user_token):
    response = post_client.post("/posts", json={"content": "Hello E2E"}, headers={"Authorization": user_token})
    assert response.status_code == 200
    assert response.json()["message"] == "Post created"


def test_read_posts(user_token):
    response = post_client.get("/posts", headers={"Authorization": user_token})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_and_delete_post(user_token):
    # Create post first
    response = post_client.post("/posts", json={"content": "Update Me"}, headers={"Authorization": user_token})
    assert response.status_code == 200

    # Read posts to get id
    response = post_client.get("/posts", headers={"Authorization": user_token})
    post_id = response.json()[0]["id"]

    # Update post
    response = post_client.put(f"/posts/{post_id}", json={"content": "Updated!"}, headers={"Authorization": user_token})
    assert response.status_code == 200
    assert response.json()["message"] == "Post updated"

    # Delete post
    response = post_client.delete(f"/posts/{post_id}", headers={"Authorization": user_token})
    assert response.status_code == 200
    assert response.json()["message"] == "Post deleted"
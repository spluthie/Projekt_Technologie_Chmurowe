# post-service/tests/test_e2e.py
import sys
from pathlib import Path

# -----------------------------
# Add service folders to Python path
# -----------------------------
ROOT_DIR = Path(__file__).parent.parent.parent  # points to repo root
sys.path.append(str(ROOT_DIR / "post-service"))
sys.path.append(str(ROOT_DIR / "auth-service"))

# Now imports work
import pytest
from fastapi.testclient import TestClient
from app.main import app as post_app
from app import database as post_db
from datetime import datetime, timedelta
import jwt
from app import auth as post_auth

from auth_service.app.main import app as auth_app
from auth_service.app import database as auth_db, auth as auth_utils

# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture(scope="module")
def auth_client():
    # Use in-memory sqlite for testing
    auth_db.DB_FILE = ":memory:"
    auth_db.create_tables()
    return TestClient(auth_app)

@pytest.fixture(scope="module")
def post_client():
    post_db.DB_FILE = ":memory:"
    post_db.create_tables()
    return TestClient(post_app)

@pytest.fixture
def user_credentials():
    return {"username": "e2euser", "password": "testpass123"}

@pytest.fixture
def token(auth_client, user_credentials):
    # Register user
    auth_client.post("/register", json=user_credentials)
    # Login user
    resp = auth_client.post("/login", json=user_credentials)
    return f"Bearer {resp.json()['access_token']}"

# -----------------------------
# E2E Tests
# -----------------------------

def test_full_user_flow(auth_client, post_client, user_credentials):
    # 1. Register user (optional, already done in token fixture)
    resp = auth_client.post("/register", json={"username": "newuser", "password": "pass123"})
    assert resp.status_code in [200, 400]  # 400 if already exists

    # 2. Login user
    resp = auth_client.post("/login", json={"username": "newuser", "password": "pass123"})
    assert resp.status_code == 200
    access_token = resp.json()["access_token"]
    headers = {"authorization": f"Bearer {access_token}"}

    # 3. Create post
    post_data = {"content": "Hello E2E!"}
    resp = post_client.post("/posts", json=post_data, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post created"

    # 4. Read posts
    resp = post_client.get("/posts")
    assert resp.status_code == 200
    posts = resp.json()
    assert any(p["content"] == "Hello E2E!" for p in posts)
    post_id = posts[0]["id"]

    # 5. Update post
    updated_data = {"content": "Updated E2E"}
    resp = post_client.put(f"/posts/{post_id}", json=updated_data, headers=headers)
    assert resp.status_code == 200
    resp = post_client.get(f"/posts/{post_id}")
    assert resp.json()["content"] == "Updated E2E"

    # 6. Delete post
    resp = post_client.delete(f"/posts/{post_id}", headers=headers)
    assert resp.status_code == 200
    resp = post_client.get(f"/posts/{post_id}")
    assert resp.status_code == 404
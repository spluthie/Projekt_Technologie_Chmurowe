# auth-service/tests/test_main.py
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Ensure we can import app modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app import database, auth

# Use a temporary DB for tests
@pytest.fixture(scope="module")
def client():
    # Create temp DB file
    db_fd, db_path = tempfile.mkstemp()
    database.DB_FILE = db_path
    database.create_tables()
    yield TestClient(app)
    os.close(db_fd)
    os.unlink(db_path)  # remove temp file after tests

@pytest.fixture
def new_user():
    return {"username": "testuser", "password": "testpass123"}

def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Auth Service running"}

def test_register_user(client, new_user):
    resp = client.post("/register", json=new_user)
    assert resp.status_code == 200
    assert resp.json()["message"] == "User registered successfully"

    # Duplicate registration should fail
    resp2 = client.post("/register", json=new_user)
    assert resp2.status_code == 400
    assert "Username already exists" in resp2.json()["detail"]

def test_login_user(client, new_user):
    # Login with correct credentials
    resp = client.post("/login", json=new_user)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    token = data["access_token"]
    payload = auth.verify_jwt(token)
    assert payload["username"] == new_user["username"]
    assert "user_id" in payload
    assert payload["role"] == "user"

    # Login with wrong password
    resp2 = client.post("/login", json={"username": new_user["username"], "password": "wrongpass"})
    assert resp2.status_code == 400
    assert "Invalid username or password" in resp2.json()["detail"]

    # Login with non-existent user
    resp3 = client.post("/login", json={"username": "noone", "password": "nopass"})
    assert resp3.status_code == 400
    assert "Invalid username or password" in resp3.json()["detail"]
# auth-service/tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import database, auth

# Use TestClient to make HTTP requests to the FastAPI app
client = TestClient(app)


# --- Setup / Teardown helpers ---
@pytest.fixture(autouse=True)
def clear_db():
    """Clear database before each test"""
    database.clear_all_users()  # you need to implement this helper in your DB module
    yield


# --- Tests ---

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Auth Service running"}


def test_register_user():
    response = client.post("/register", json={
        "username": "alice",
        "password": "secret123"
    })
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}

    # Attempt to register same username again
    response2 = client.post("/register", json={
        "username": "alice",
        "password": "anotherpass"
    })
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Username already exists"


def test_login_user_success():
    # First register user
    client.post("/register", json={"username": "bob", "password": "mypassword"})
    
    # Login
    response = client.post("/login", json={"username": "bob", "password": "mypassword"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # Optional: decode token to check payload (if using PyJWT)
    payload = auth.decode_jwt(data["access_token"])
    assert payload["username"] == "bob"


def test_login_user_fail_wrong_password():
    # Register user
    client.post("/register", json={"username": "carol", "password": "pass123"})
    
    # Wrong password
    response = client.post("/login", json={"username": "carol", "password": "wrongpass"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid username or password"


def test_login_user_fail_nonexistent():
    response = client.post("/login", json={"username": "nonexistent", "password": "abc"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid username or password"
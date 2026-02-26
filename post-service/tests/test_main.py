# post-service/tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import database, auth

client = TestClient(app)

# --- Setup / Teardown ---
@pytest.fixture(autouse=True)
def setup_users_and_clear_db():
    """Clear posts and create a test user"""
    database.clear_all_posts()  # implement this in your database.py
    database.clear_all_users()
    # Create test user and get JWT
    database.create_user("testuser", auth.hash_password("password"))
    user = database.get_user_by_username("testuser")
    token = auth.create_jwt(user["id"], user["username"], user["role"])
    yield {"user": user, "token": token}


# --- Helper ---
def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# --- Tests ---
def test_create_post(setup_users_and_clear_db):
    token = setup_users_and_clear_db["token"]
    response = client.post("/posts", json={"content": "Hello World"}, headers=auth_header(token))
    assert response.status_code == 200
    assert response.json()["message"] == "Post created"


def test_read_posts(setup_users_and_clear_db):
    token = setup_users_and_clear_db["token"]
    # create 2 posts
    client.post("/posts", json={"content": "Post 1"}, headers=auth_header(token))
    client.post("/posts", json={"content": "Post 2"}, headers=auth_header(token))

    response = client.get("/posts")
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) == 2
    assert posts[0]["content"] == "Post 1"


def test_read_single_post(setup_users_and_clear_db):
    token = setup_users_and_clear_db["token"]
    client.post("/posts", json={"content": "Single Post"}, headers=auth_header(token))
    posts = client.get("/posts").json()
    post_id = posts[0]["id"]

    response = client.get(f"/posts/{post_id}")
    assert response.status_code == 200
    assert response.json()["content"] == "Single Post"

    # Nonexistent post
    response2 = client.get("/posts/9999")
    assert response2.status_code == 404


def test_update_post(setup_users_and_clear_db):
    token = setup_users_and_clear_db["token"]
    client.post("/posts", json={"content": "Old"}, headers=auth_header(token))
    post_id = client.get("/posts").json()[0]["id"]

    response = client.put(f"/posts/{post_id}", json={"content": "Updated"}, headers=auth_header(token))
    assert response.status_code == 200
    assert response.json()["message"] == "Post updated"

    # Another user cannot edit
    database.create_user("other", auth.hash_password("pass"))
    other_user = database.get_user_by_username("other")
    other_token = auth.create_jwt(other_user["id"], other_user["username"], other_user["role"])
    response2 = client.put(f"/posts/{post_id}", json={"content": "Hack"}, headers=auth_header(other_token))
    assert response2.status_code == 403


def test_delete_post(setup_users_and_clear_db):
    token = setup_users_and_clear_db["token"]
    client.post("/posts", json={"content": "To delete"}, headers=auth_header(token))
    post_id = client.get("/posts").json()[0]["id"]

    response = client.delete(f"/posts/{post_id}", headers=auth_header(token))
    assert response.status_code == 200
    assert response.json()["message"] == "Post deleted"

    # Another user cannot delete
    client.post("/posts", json={"content": "Another"}, headers=auth_header(token))
    post_id2 = client.get("/posts").json()[0]["id"]
    database.create_user("other", auth.hash_password("pass"))
    other_user = database.get_user_by_username("other")
    other_token = auth.create_jwt(other_user["id"], other_user["username"], other_user["role"])
    response2 = client.delete(f"/posts/{post_id2}", headers=auth_header(other_token))
    assert response2.status_code == 403
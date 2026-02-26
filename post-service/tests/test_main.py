# post-service/tests/test_main.py
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta

# allow imports from app
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app import database, auth

# --------------------------
# Fixtures
# --------------------------

# Use a temporary DB for testing
@pytest.fixture(scope="module")
def client():
    db_fd, db_path = tempfile.mkstemp()
    database.DB_FILE = db_path
    database.create_tables()
    yield TestClient(app)
    os.close(db_fd)
    os.unlink(db_path)

# Fake user token fixture
@pytest.fixture
def fake_user_token():
    payload = {
        "user_id": 1,
        "username": "testuser",
        "role": "user",
        "exp": datetime.utcnow() + timedelta(minutes=60)
    }
    token = jwt.encode(payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
    return f"Bearer {token}"

@pytest.fixture
def new_post():
    return {"content": "Hello World!"}

# --------------------------
# Tests
# --------------------------

def test_create_post(client, fake_user_token, new_post):
    resp = client.post("/posts", json=new_post, headers={"authorization": fake_user_token})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post created"

def test_read_posts(client, fake_user_token, new_post):
    client.post("/posts", json=new_post, headers={"authorization": fake_user_token})
    resp = client.get("/posts")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["content"] == new_post["content"]

def test_read_single_post(client, fake_user_token, new_post):
    client.post("/posts", json=new_post, headers={"authorization": fake_user_token})
    posts = client.get("/posts").json()
    post_id = posts[0]["id"]
    resp = client.get(f"/posts/{post_id}")
    assert resp.status_code == 200
    assert resp.json()["content"] == new_post["content"]

def test_update_post(client, fake_user_token, new_post):
    client.post("/posts", json=new_post, headers={"authorization": fake_user_token})
    posts = client.get("/posts").json()
    post_id = posts[0]["id"]
    updated_content = {"content": "Updated Content"}
    resp = client.put(f"/posts/{post_id}", json=updated_content, headers={"authorization": fake_user_token})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post updated"
    resp2 = client.get(f"/posts/{post_id}")
    assert resp2.json()["content"] == "Updated Content"

def test_delete_post(client, fake_user_token, new_post):
    client.post("/posts", json=new_post, headers={"authorization": fake_user_token})
    posts = client.get("/posts").json()
    post_id = posts[0]["id"]
    resp = client.delete(f"/posts/{post_id}", headers={"authorization": fake_user_token})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Post deleted"
    resp2 = client.get(f"/posts/{post_id}")
    assert resp2.status_code == 404
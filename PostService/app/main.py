# app/main.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from app import database, auth

database.create_tables()
app = FastAPI(title="Post Service")

class PostCreate(BaseModel):
    content: str

class PostUpdate(BaseModel):
    content: str

# Helper to extract user info from token
def get_user_from_token(authorization: str):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        token = authorization.split(" ")[1]  # "Bearer <token>"
        payload = auth.verify_jwt(token)
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/posts")
def create_post(post: PostCreate, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    database.create_post(user['user_id'], user['username'], post.content)
    return {"message": "Post created"}

@app.get("/posts")
def read_posts(limit: int = 10, offset: int = 0):
    posts = database.get_posts(limit, offset)
    return [dict(p) for p in posts]

@app.get("/posts/{post_id}")
def read_post(post_id: int):
    post = database.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return dict(post)

@app.put("/posts/{post_id}")
def update_post(post_id: int, post: PostUpdate, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    existing = database.get_post(post_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    database.update_post(post_id, post.content)
    return {"message": "Post updated"}

@app.delete("/posts/{post_id}")
def delete_post(post_id: int, authorization: str = Header(None)):
    user = get_user_from_token(authorization)
    existing = database.get_post(post_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing["user_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    database.delete_post(post_id)
    return {"message": "Post deleted"}
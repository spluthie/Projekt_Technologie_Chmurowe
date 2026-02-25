# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app import database, auth

# Initialize DB tables
database.create_tables()

app = FastAPI(title="Auth Service")

# Request schemas
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Routes
@app.get("/")
def root():
    return {"message": "Auth Service running"}

@app.post("/register")
def register(user: UserRegister):
    if database.get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = auth.hash_password(user.password)
    database.create_user(user.username, hashed_pw)
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    db_user = database.get_user_by_username(user.username)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    if not auth.verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    token = auth.create_jwt(db_user["id"], db_user["username"], db_user["role"])
    return {"access_token": token}
# app/models.py
from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: str = "user"
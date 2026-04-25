# models/user.py
from pydantic import BaseModel
from typing import Optional


class RegisterRequest(BaseModel):
    nickname: str
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
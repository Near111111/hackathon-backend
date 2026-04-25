# services/user_service.py
from db.database import get_db
from bson import ObjectId
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "fallback_secret_change_this")
JWT_EXPIRY_DAYS = 7


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _generate_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


async def register_user(nickname: str, username: str, password: str) -> dict:
    db = get_db()

    existing = await db["users"].find_one({"username": username.strip().lower()})
    if existing:
        raise ValueError("Username already taken.")

    hashed = _hash_password(password)

    user = {
        "nickname": nickname.strip(),
        "username": username.strip().lower(),
        "password": hashed,
        "created_at": datetime.utcnow(),
    }

    result = await db["users"].insert_one(user)
    user_id = str(result.inserted_id)
    token = _generate_token(user_id)

    return {
        "user_id": user_id,
        "nickname": user["nickname"],
        "username": user["username"],
        "token": token,
    }


async def login_user(username: str, password: str) -> dict:
    db = get_db()

    user = await db["users"].find_one({"username": username.strip().lower()})
    if not user:
        raise ValueError("Invalid username or password.")

    if not _verify_password(password, user["password"]):
        raise ValueError("Invalid username or password.")

    user_id = str(user["_id"])
    token = _generate_token(user_id)

    return {
        "user_id": user_id,
        "nickname": user["nickname"],
        "username": user["username"],
        "token": token,
    }


async def get_user_by_id(user_id: str) -> dict | None:
    db = get_db()
    try:
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    if not user:
        return None

    user = _serialize(user)
    user.pop("password", None)
    return user
# db/database.py

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set in environment variables.")
if not DB_NAME:
    raise ValueError("DB_NAME is not set in environment variables.")

client = AsyncIOMotorClient(MONGODB_URI, maxPoolSize=10, minPoolSize=2)
db = client[DB_NAME]

def get_db():
    return db
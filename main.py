# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import logs, motivational
from routes.posts import router as posts_router
from db.database import get_db, client
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs.router)
app.include_router(motivational.router)
app.include_router(posts_router)


@app.on_event("startup")
async def startup():
    logger.info("Starting up StressMap API...")
    db = get_db()

    # Create indexes for faster queries
    await db["posts"].create_index([("created_at", -1)])
    await db["posts"].create_index("user_id")
    await db["posts"].create_index("hidden_by")
    await db["comments"].create_index("post_id")
    await db["comments"].create_index([("created_at", 1)])
    await db["logs"].create_index([("created_at", -1)])

    logger.info("Database indexes created successfully.")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down StressMap API...")
    client.close()


@app.get("/")
def root():
    return {"message": "StressMap API running!"}


@app.get("/health")
def health():
    return {"status": "ok"}
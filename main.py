# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import logs, motivational
from routes.posts import router as posts_router
from routes.users import router as users_router
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
app.include_router(users_router)


@app.on_event("startup")
async def startup():
    db = get_db()
    try:
        await db["posts"].create_index([("created_at", -1)])
        await db["posts"].create_index("user_id")
        await db["posts"].create_index("hidden_by")
        await db["comments"].create_index("post_id")
        await db["comments"].create_index([("created_at", 1)])
        await db["logs"].create_index([("created_at", -1)])
        await db["users"].create_index("username", unique=True)
        logger.info("Indexes created.")
    except Exception as e:
        logger.warning(f"Could not create indexes: {e}")


@app.on_event("shutdown")
async def shutdown():
    client.close()


@app.get("/")
def root():
    return {"message": "StressMap API running!"}


@app.get("/health")
def health():
    return {"status": "ok"}
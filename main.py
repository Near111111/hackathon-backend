# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import logs, motivational  # <-- add this
from routes.posts import router as posts_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs.router)
app.include_router(motivational.router)  # <-- add this
app.include_router(posts_router)  # <-- add this

@app.get("/")
def root():
    return {"message": "StressMap API running!"}
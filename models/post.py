# models/post.py

from pydantic import BaseModel
from typing import Optional

class CreatePostRequest(BaseModel):
    content: str

class UpdatePostRequest(BaseModel):
    content: str

class CreateCommentRequest(BaseModel):
    content: str

class UpdateCommentRequest(BaseModel):
    content: str

class HidePostRequest(BaseModel):
    hidden: bool  # True = hide, False = unhide
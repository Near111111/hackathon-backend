# services/post_service.py

from db.database import get_db
from bson import ObjectId
from datetime import datetime
import logging
from services.moderation_service import moderate_content

logger = logging.getLogger(__name__)


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


# ─── POSTS ────────────────────────────────────────────────────────────────────

async def create_post(user_id: str, content: str) -> dict:
    db = get_db()

    # ML moderation check (sync, no await needed)
    label = moderate_content(content)
    if label == "harassment":
        raise ValueError("Your post was flagged for harassment and cannot be published.")

    post = {
        "user_id": user_id,
        "content": content,
        "moderation_label": label,
        "likes": [],
        "comment_count": 0,
        "hidden_by": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db["posts"].insert_one(post)
    post["_id"] = str(result.inserted_id)
    return post


async def get_all_posts(skip: int = 0, limit: int = 10) -> list:
    db = get_db()
    cursor = db["posts"].find().sort("created_at", -1).skip(skip).limit(limit)
    posts = []
    async for post in cursor:
        posts.append(_serialize(post))
    return posts


async def get_post_by_id(post_id: str) -> dict | None:
    db = get_db()
    try:
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    except Exception:
        return None
    return _serialize(post) if post else None


async def update_post(post_id: str, user_id: str, content: str) -> dict | None:
    db = get_db()
    try:
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    except Exception:
        return None

    if not post:
        return None
    if post["user_id"] != user_id:
        raise PermissionError("You can only edit your own posts.")

    await db["posts"].update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"content": content, "updated_at": datetime.utcnow()}}
    )
    return await get_post_by_id(post_id)


async def delete_post(post_id: str, user_id: str) -> bool:
    db = get_db()
    try:
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    except Exception:
        return False

    if not post:
        return False
    if post["user_id"] != user_id:
        raise PermissionError("You can only delete your own posts.")

    await db["posts"].delete_one({"_id": ObjectId(post_id)})
    await db["comments"].delete_many({"post_id": post_id})  # cascade delete
    return True


async def toggle_like_post(post_id: str, user_id: str) -> dict | None:
    db = get_db()
    try:
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    except Exception:
        return None

    if not post:
        return None

    if user_id in post["likes"]:
        await db["posts"].update_one({"_id": ObjectId(post_id)}, {"$pull": {"likes": user_id}})
    else:
        await db["posts"].update_one({"_id": ObjectId(post_id)}, {"$push": {"likes": user_id}})

    return await get_post_by_id(post_id)


# ─── COMMENTS ─────────────────────────────────────────────────────────────────

async def create_comment(post_id: str, user_id: str, content: str) -> dict | None:
    db = get_db()
    try:
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    except Exception:
        return None

    if not post:
        return None

    comment = {
        "post_id": post_id,
        "user_id": user_id,
        "content": content,
        "likes": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = await db["comments"].insert_one(comment)
    comment["_id"] = str(result.inserted_id)

    await db["posts"].update_one({"_id": ObjectId(post_id)}, {"$inc": {"comment_count": 1}})

    return comment


async def get_comments_by_post(post_id: str, skip: int = 0, limit: int = 10) -> list:
    db = get_db()
    cursor = db["comments"].find({"post_id": post_id}).sort("created_at", 1).skip(skip).limit(limit)
    comments = []
    async for comment in cursor:
        comments.append(_serialize(comment))
    return comments


async def update_comment(comment_id: str, user_id: str, content: str) -> dict | None:
    db = get_db()
    try:
        comment = await db["comments"].find_one({"_id": ObjectId(comment_id)})
    except Exception:
        return None

    if not comment:
        return None
    if comment["user_id"] != user_id:
        raise PermissionError("You can only edit your own comments.")

    await db["comments"].update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"content": content, "updated_at": datetime.utcnow()}}
    )
    comment["content"] = content
    comment["_id"] = str(comment["_id"])
    return comment


async def delete_comment(comment_id: str, user_id: str) -> bool:
    db = get_db()
    try:
        comment = await db["comments"].find_one({"_id": ObjectId(comment_id)})
    except Exception:
        return False

    if not comment:
        return False
    if comment["user_id"] != user_id:
        raise PermissionError("You can only delete your own comments.")

    await db["comments"].delete_one({"_id": ObjectId(comment_id)})
    await db["posts"].update_one(
        {"_id": ObjectId(comment["post_id"])},
        {"$inc": {"comment_count": -1}}
    )
    return True


async def toggle_like_comment(comment_id: str, user_id: str) -> dict | None:
    db = get_db()
    try:
        comment = await db["comments"].find_one({"_id": ObjectId(comment_id)})
    except Exception:
        return None

    if not comment:
        return None

    if user_id in comment["likes"]:
        await db["comments"].update_one({"_id": ObjectId(comment_id)}, {"$pull": {"likes": user_id}})
    else:
        await db["comments"].update_one({"_id": ObjectId(comment_id)}, {"$push": {"likes": user_id}})

    comment = await db["comments"].find_one({"_id": ObjectId(comment_id)})
    return _serialize(comment)

async def toggle_hide_post(post_id: str, user_id: str) -> dict:
    db = get_db()
    try:
        post = await db["posts"].find_one({"_id": ObjectId(post_id)})
    except Exception:
        return None

    if not post:
        return None

    # hidden_by is a list of user_ids who hid this post
    if user_id in post.get("hidden_by", []):
        await db["posts"].update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"hidden_by": user_id}}
        )
        action = "unhidden"
    else:
        await db["posts"].update_one(
            {"_id": ObjectId(post_id)},
            {"$push": {"hidden_by": user_id}}
        )
        action = "hidden"

    post = await get_post_by_id(post_id)
    return {"post": post, "action": action}


async def get_all_posts(skip: int = 0, limit: int = 10, user_id: str = None) -> list:
    db = get_db()
    
    # Filter out posts hidden by this user
    query = {}
    if user_id:
        query["hidden_by"] = {"$nin": [user_id]}

    cursor = db["posts"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    posts = []
    async for post in cursor:
        posts.append(_serialize(post))
    return posts
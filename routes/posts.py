# routes/posts.py

from fastapi import APIRouter, HTTPException, Query
from models.post import CreatePostRequest, UpdatePostRequest, CreateCommentRequest, UpdateCommentRequest
from services import post_service

router = APIRouter(prefix="/posts", tags=["Posts"])


# ─── POSTS ────────────────────────────────────────────────────────────────────

@router.post("/")
async def create_post(body: CreatePostRequest, user_id: str = Query(...)):
    post = await post_service.create_post(user_id=user_id, content=body.content)
    return {"success": True, "data": post}


@router.get("/")
async def get_all_posts(skip: int = 0, limit: int = 10, user_id: str = Query(None)):
    posts = await post_service.get_all_posts(skip=skip, limit=limit, user_id=user_id)
    return {"success": True, "data": posts}


@router.get("/{post_id}")
async def get_post(post_id: str):
    post = await post_service.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {"success": True, "data": post}


@router.put("/{post_id}")
async def update_post(post_id: str, body: UpdatePostRequest, user_id: str = Query(...)):
    try:
        post = await post_service.update_post(post_id=post_id, user_id=user_id, content=body.content)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {"success": True, "data": post}


@router.delete("/{post_id}")
async def delete_post(post_id: str, user_id: str = Query(...)):
    try:
        deleted = await post_service.delete_post(post_id=post_id, user_id=user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {"success": True, "message": "Post deleted successfully."}


@router.post("/{post_id}/like")
async def like_post(post_id: str, user_id: str = Query(...)):
    post = await post_service.toggle_like_post(post_id=post_id, user_id=user_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {"success": True, "data": post}


# ─── COMMENTS ─────────────────────────────────────────────────────────────────

@router.post("/{post_id}/comments")
async def create_comment(post_id: str, body: CreateCommentRequest, user_id: str = Query(...)):
    comment = await post_service.create_comment(post_id=post_id, user_id=user_id, content=body.content)
    if not comment:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {"success": True, "data": comment}


@router.get("/{post_id}/comments")
async def get_comments(post_id: str, skip: int = 0, limit: int = 10):
    comments = await post_service.get_comments_by_post(post_id=post_id, skip=skip, limit=limit)
    return {"success": True, "data": comments}


@router.put("/comments/{comment_id}")
async def update_comment(comment_id: str, body: UpdateCommentRequest, user_id: str = Query(...)):
    try:
        comment = await post_service.update_comment(comment_id=comment_id, user_id=user_id, content=body.content)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    return {"success": True, "data": comment}


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: str, user_id: str = Query(...)):
    try:
        deleted = await post_service.delete_comment(comment_id=comment_id, user_id=user_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Comment not found.")
    return {"success": True, "message": "Comment deleted successfully."}


@router.post("/comments/{comment_id}/like")
async def like_comment(comment_id: str, user_id: str = Query(...)):
    comment = await post_service.toggle_like_comment(comment_id=comment_id, user_id=user_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    return {"success": True, "data": comment}

@router.post("/{post_id}/hide")
async def hide_post(post_id: str, user_id: str = Query(...)):
    result = await post_service.toggle_hide_post(post_id=post_id, user_id=user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {
        "success": True,
        "message": f"Post {result['action']} successfully.",
        "data": result["post"]
    }
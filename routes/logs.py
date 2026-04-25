from fastapi import APIRouter, HTTPException
from models.schemas import DailyLog, LogResponse
from db.database import get_db
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("/", response_model=LogResponse)
async def create_log(log: DailyLog):
    try:
        db = get_db()
        
        log_entry = {
            "stress_level": log.stress_level,
            "sleep_hours": log.sleep_hours,
            "skipped_breakfast": log.skipped_breakfast,
            "food_quality": log.food_quality,
            "activity": log.activity,
            "notes": log.notes,
            "created_at": datetime.utcnow()
        }

        result = await db["logs"].insert_one(log_entry)
        log_entry["_id"] = str(result.inserted_id)  # convert ObjectId to string

        return LogResponse(
            success=True,
            message="Log saved!",
            data=log_entry
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_logs(limit: int = 5):
    try:
        db = get_db()
        
        cursor = db["logs"].find().sort("created_at", -1).limit(limit)
        logs = []
        async for log in cursor:
            log["_id"] = str(log["_id"])  # convert ObjectId to string
            logs.append(log)

        return {
            "success": True,
            "count": len(logs),
            "data": logs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{log_id}")
async def delete_log(log_id: str):
    try:
        db = get_db()
        
        result = await db["logs"].delete_one({"_id": ObjectId(log_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Log not found")
            
        return {"success": True, "message": f"Log {log_id} deleted"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
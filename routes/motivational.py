# routes/motivational.py

from fastapi import APIRouter, HTTPException
from services.ai_service import generate_motivational_quote

router = APIRouter(prefix="/motivational", tags=["motivational"])


@router.get("/")
async def get_motivational_quote():
    """
    Randomly picks a log and generates a motivational quote using Gemini AI.
    """
    try:
        result = await generate_motivational_quote()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
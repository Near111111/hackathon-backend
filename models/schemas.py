# models/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, Literal

class DailyLog(BaseModel):
    stress_level: int = Field(..., ge=1, le=10, description="1 = walang stress, 10 = max stress")
    sleep_hours: float = Field(..., ge=0, le=24)
    skipped_breakfast: bool = False
    food_quality: Literal["good", "okay", "bad"] = "okay"
    activity: Literal["none", "light", "moderate", "heavy"] = "none"
    notes: Optional[str] = None

class LogResponse(BaseModel):
    success: bool
    message: str
    data: dict
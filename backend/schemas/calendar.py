from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CalendarCreate(BaseModel):
    """Schema for creating a calendar"""
    user_id: int
    calendar_name: str
    google_calendar_id: Optional[str] = None


class CalendarResponse(BaseModel):
    """Schema for calendar response"""
    calendar_id: int
    user_id: int
    calendar_name: str
    google_calendar_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

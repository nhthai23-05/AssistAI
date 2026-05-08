from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CalendarCreate(BaseModel):
    """Schema for creating a calendar"""
    user_id: int = Field(..., description="User ID")
    calendar_name: str = Field(..., min_length=1, max_length=255, description="Calendar name")
    google_calendar_id: Optional[str] = Field(None, description="Google Calendar ID (email format)")
    is_primary: bool = Field(False, description="Whether this is the primary calendar")


class CalendarUpdate(BaseModel):
    """Schema for updating a calendar"""
    calendar_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_primary: Optional[bool] = None


class CalendarResponse(BaseModel):
    """Schema for calendar response"""
    calendar_id: int
    user_id: int
    calendar_name: str
    google_calendar_id: Optional[str] = None
    is_primary: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

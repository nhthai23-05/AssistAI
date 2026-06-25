from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
import zoneinfo

_VALID_TIMEZONES = zoneinfo.available_timezones()


class EventCreate(BaseModel):
    """Schema for creating an event via smart action or direct API"""
    session_id: Optional[int] = Field(None, description="Associated session ID")
    summary: str = Field(..., min_length=1, max_length=255, description="Event title")
    start_datetime: datetime = Field(..., description="Event start time (ISO 8601)")
    end_datetime: datetime = Field(..., description="Event end time (ISO 8601)")
    description: Optional[str] = Field(None, max_length=2000, description="Event description")
    location: Optional[str] = Field(None, max_length=500, description="Event location")
    attendees: Optional[List[EmailStr]] = Field(None, description="Email addresses of attendees")
    recurrence: Optional[List[str]] = Field(None, description="Recurrence rules (RRULE format)")
    timezone: Optional[str] = Field("Asia/Ho_Chi_Minh", description="IANA timezone name")

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_datetime <= self.start_datetime:
            raise ValueError("end_datetime phải sau start_datetime")
        return self

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, v):
        if v and v not in _VALID_TIMEZONES:
            raise ValueError(f"'{v}' không phải IANA timezone hợp lệ")
        return v


class EventUpdate(BaseModel):
    """Schema for updating an existing event"""
    summary: Optional[str] = Field(None, min_length=1, max_length=255)
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    description: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=500)
    attendees: Optional[List[EmailStr]] = None
    recurrence: Optional[dict] = None


class EventResponse(BaseModel):
    """Schema for event response from API"""
    event_id: str = Field(..., description="Google Calendar event ID")
    calendar_id: str = Field(..., description="Google Calendar ID")
    summary: str
    start_datetime: datetime
    end_datetime: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None
    recurrence: Optional[dict] = None
    timezone: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Schema for listing events"""
    events: List[EventResponse] = Field(default_factory=list)
    total_count: int
    date_range: dict = Field(..., description="Date range of events (start and end)")
    timezone: Optional[str] = None


class SmartEventAction(BaseModel):
    """Schema for smart event action response"""
    action: str = Field(..., description="Action type: 'create', 'update', or 'delete'")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score of action detection")
    reasoning: str = Field(..., description="Explanation of why this action was detected")
    target_event: Optional[EventResponse] = None  # For update/delete
    event_details: Optional[EventCreate] = None  # For create
    error: Optional[str] = None

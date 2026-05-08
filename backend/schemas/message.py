from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """Schema for creating a message"""
    session_id: int = Field(..., description="Session ID this message belongs to")
    role: str = Field(
        ..., 
        pattern="^(user|assistant|system)$",
        description="Message role: 'user', 'assistant', or 'system'"
    )
    content: str = Field(..., min_length=1, max_length=50000, description="Message content")


class MessageUpdate(BaseModel):
    """Schema for updating a message"""
    content: Optional[str] = Field(None, min_length=1, max_length=50000)


class MessageResponse(BaseModel):
    """Schema for message response"""
    message_id: int
    session_id: int
    role: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

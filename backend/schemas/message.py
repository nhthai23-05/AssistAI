from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """Schema for creating a message"""
    session_id: int
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)


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

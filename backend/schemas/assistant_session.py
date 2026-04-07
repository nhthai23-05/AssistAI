from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AssistantSessionCreate(BaseModel):
    """Schema for creating an assistant session"""
    user_id: int
    workspace_id: int
    title: Optional[str] = None


class AssistantSessionUpdate(BaseModel):
    """Schema for updating an assistant session"""
    title: Optional[str] = None
    status: Optional[str] = None


class AssistantSessionResponse(BaseModel):
    """Schema for assistant session response"""
    session_id: int
    user_id: int
    workspace_id: int
    title: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

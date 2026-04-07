from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ToolCallCreate(BaseModel):
    """Schema for creating a tool call"""
    session_id: int
    tool_name: str
    arguments: dict


class ToolCallResponse(BaseModel):
    """Schema for tool call response"""
    call_id: int
    session_id: int
    tool_name: str
    arguments: dict
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

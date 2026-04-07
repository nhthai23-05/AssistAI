from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ToolResultCreate(BaseModel):
    """Schema for creating a tool result"""
    tool_call_id: int
    result_data: dict
    error_message: Optional[str] = None


class ToolResultResponse(BaseModel):
    """Schema for tool result response"""
    result_id: int
    tool_call_id: int
    result_data: dict
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

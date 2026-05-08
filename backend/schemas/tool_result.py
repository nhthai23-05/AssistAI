from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ToolResultCreate(BaseModel):
    """Schema for creating a tool call result"""
    tool_call_id: int = Field(..., description="ID of the tool call")
    success: bool = Field(True, description="Whether tool execution was successful")
    result: Optional[dict] = Field(None, description="Result data from tool execution (JSON)")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")


class ToolResultResponse(BaseModel):
    """Schema for tool result response"""
    tool_result_id: int
    tool_call_id: int
    success: bool
    result: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolCallWithResult(BaseModel):
    """Schema for tool call with its result(s)"""
    call_id: int
    session_id: int
    tool_name: str
    arguments: dict
    status: str
    results: list[ToolResultResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

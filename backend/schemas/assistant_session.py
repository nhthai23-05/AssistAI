from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AssistantSessionCreate(BaseModel):
    """Schema for creating an assistant session"""
    user_id: int = Field(..., description="User ID")
    workspace_id: int = Field(..., description="Workspace ID")
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Session title")


class AssistantSessionUpdate(BaseModel):
    """Schema for updating an assistant session"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(
        None, 
        pattern="^(active|completed|failed|cancelled)$",
        description="Session status"
    )


class AssistantSessionResponse(BaseModel):
    """Schema for assistant session response"""
    session_id: int
    user_id: int
    workspace_id: int
    title: Optional[str] = None
    status: str
    message_count: int = Field(0, description="Total messages in session")
    total_tokens_used: int = Field(0, description="Total tokens used in session")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssistantSessionDetail(BaseModel):
    """Detailed session with recent messages"""
    session_id: int
    user_id: int
    workspace_id: int
    title: Optional[str] = None
    status: str
    message_count: int
    total_tokens_used: int
    last_message_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

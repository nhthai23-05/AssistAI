from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WorkspaceCreate(BaseModel):
    """Schema for creating a workspace"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None


class WorkspaceResponse(BaseModel):
    """Schema for workspace response"""
    workspace_id: int
    owner_user_id: int
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

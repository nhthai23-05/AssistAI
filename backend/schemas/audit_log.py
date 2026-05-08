from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry"""
    workspace_id: int = Field(..., description="Workspace ID where action occurred")
    user_id: Optional[int] = Field(None, description="User ID who performed action")
    action: str = Field(
        ..., 
        description="Action performed: 'create', 'read', 'update', 'delete', 'auth_login', etc"
    )
    description: Optional[str] = Field(None, max_length=1000, description="Description of action")
    resource_type: str = Field(
        ..., 
        description="Resource type: 'user', 'calendar', 'event', 'message', 'session', etc"
    )
    resource_id: Optional[int] = Field(None, description="ID of affected resource")
    changes: Optional[dict] = Field(None, description="Before/after changes (for updates)")


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    audit_log_id: int
    workspace_id: int
    user_id: Optional[int] = None
    action: str
    description: Optional[str] = None
    resource_type: str
    resource_id: Optional[int] = None
    changes: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    log_id: int
    workspace_id: int
    user_id: Optional[int]
    action: str
    description: Optional[str]
    resource_type: str
    resource_id: int
    created_at: datetime

    class Config:
        from_attributes = True

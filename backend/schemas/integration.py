from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class IntegrationCreate(BaseModel):
    """Schema for creating an integration"""
    workspace_id: int
    service_name: str
    configuration: Optional[dict] = None


class IntegrationResponse(BaseModel):
    """Schema for integration response"""
    integration_id: int
    workspace_id: int
    service_name: str
    configuration: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

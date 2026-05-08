from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IntegrationCreate(BaseModel):
    """Schema for creating an integration"""
    workspace_id: int = Field(..., description="Workspace ID")
    service_name: str = Field(
        ..., 
        description="Integration service: 'google_calendar', 'google_sheets', 'outlook', 'github', etc"
    )
    is_active: bool = Field(True, description="Whether integration is active")
    configuration: Optional[dict] = Field(None, description="Service-specific configuration")


class IntegrationUpdate(BaseModel):
    """Schema for updating an integration"""
    is_active: Optional[bool] = None
    configuration: Optional[dict] = Field(None, description="Updated configuration")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class IntegrationResponse(BaseModel):
    """Schema for integration response"""
    integration_id: int
    workspace_id: int
    service_name: str
    is_active: bool
    configuration: Optional[dict] = None
    metadata: Optional[dict] = None
    last_synced: Optional[datetime] = Field(None, description="Last synchronization time")
    sync_status: Optional[str] = Field(None, description="Status of last sync: 'success', 'failed', 'pending'")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

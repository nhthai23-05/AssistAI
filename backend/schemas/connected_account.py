from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class ConnectedAccountCreate(BaseModel):
    """Schema for creating a connected account"""
    user_id: int = Field(..., description="User ID")
    service_provider: str = Field(..., description="Provider name: 'google', 'outlook', etc")
    account_email: EmailStr = Field(..., description="Account email address")
    is_primary: bool = Field(False, description="Whether this is primary account for provider")


class ConnectedAccountUpdate(BaseModel):
    """Schema for updating a connected account"""
    account_email: Optional[EmailStr] = None
    is_primary: Optional[bool] = None


class ConnectedAccountResponse(BaseModel):
    """Schema for connected account response"""
    connected_account_id: int
    user_id: int
    service_provider: str
    account_email: str
    is_primary: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

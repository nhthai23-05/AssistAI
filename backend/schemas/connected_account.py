from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ConnectedAccountCreate(BaseModel):
    """Schema for creating a connected account"""
    user_id: int
    service_provider: str
    account_email: str
    oauth_token_id: Optional[int] = None


class ConnectedAccountResponse(BaseModel):
    """Schema for connected account response"""
    account_id: int
    user_id: int
    service_provider: str
    account_email: str
    oauth_token_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

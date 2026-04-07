from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OAuthTokenResponse(BaseModel):
    """Schema for OAuth token response"""
    token_id: int
    connected_account_id: int
    access_token: str
    refresh_token: Optional[str]
    token_expiry: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

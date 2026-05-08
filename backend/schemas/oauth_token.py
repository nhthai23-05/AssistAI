from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OAuthTokenCreate(BaseModel):
    """Schema for creating OAuth token"""
    connected_account_id: int = Field(..., description="Associated connected account ID")
    access_token: str = Field(..., description="OAuth access token (will be encrypted)")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token (will be encrypted)")
    token_type: str = Field("Bearer", description="Token type (usually Bearer)")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")
    scope: Optional[str] = Field(None, description="OAuth scopes (space-separated)")


class OAuthTokenResponse(BaseModel):
    """Schema for OAuth token response - tokens are NEVER returned plaintext to client"""
    oauth_token_id: int
    connected_account_id: int
    token_type: str
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    is_expired: bool = Field(..., description="Whether token has expired")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OAuthTokenRefresh(BaseModel):
    """Schema for refreshing OAuth token"""
    oauth_token_id: int
    new_access_token: str = Field(..., description="New access token (encrypted)")
    expires_at: Optional[datetime] = Field(None, description="New expiration time")
    scope: Optional[str] = None

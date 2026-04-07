from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    user_id: int
    email: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

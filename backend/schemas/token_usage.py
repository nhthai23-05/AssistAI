from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TokenUsageResponse(BaseModel):
    """Schema for token usage response"""
    usage_id: int
    session_id: int
    usage_type: str
    amount: int
    meta_data: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

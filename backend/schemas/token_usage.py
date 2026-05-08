from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TokenUsageCreate(BaseModel):
    """Schema for recording token usage"""
    session_id: int = Field(..., description="Session ID")
    usage_type: str = Field(
        ...,
        description="Type of token usage: 'input', 'output', 'total'"
    )
    amount: int = Field(..., gt=0, description="Number of tokens used")
    model: Optional[str] = Field(None, description="AI model used (e.g., 'gpt-4o-mini')")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class TokenUsageResponse(BaseModel):
    """Schema for token usage response"""
    usage_id: int
    session_id: int
    usage_type: str
    amount: int
    model: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenUsageSummary(BaseModel):
    """Summary of token usage for a session"""
    session_id: int
    total_tokens: int
    input_tokens: int = 0
    output_tokens: int = 0
    by_model: dict = Field(default_factory=dict, description="Breakdown by model")

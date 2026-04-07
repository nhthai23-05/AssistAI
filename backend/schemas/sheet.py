from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SheetCreate(BaseModel):
    """Schema for creating a sheet"""
    workspace_id: int
    sheet_name: str
    google_sheet_id: Optional[str] = None


class SheetResponse(BaseModel):
    """Schema for sheet response"""
    sheet_id: int
    workspace_id: int
    sheet_name: str
    google_sheet_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

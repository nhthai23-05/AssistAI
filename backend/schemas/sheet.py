from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SheetCreate(BaseModel):
    """Schema for creating/linking a Google Sheet"""
    workspace_id: int = Field(..., description="Workspace ID")
    sheet_name: str = Field(..., min_length=1, max_length=255, description="Sheet name")
    google_sheet_id: str = Field(..., description="Google Sheet ID (from URL)")
    tab_names: Optional[List[str]] = Field(None, description="Tab names to sync")


class SheetUpdate(BaseModel):
    """Schema for updating a sheet reference"""
    sheet_name: Optional[str] = Field(None, min_length=1, max_length=255)
    tab_names: Optional[List[str]] = None
    is_active: Optional[bool] = None


class SheetData(BaseModel):
    """Schema for sheet data rows"""
    headers: List[str] = Field(..., description="Column headers")
    rows: List[List[str]] = Field(..., description="Sheet data rows")
    row_count: int


class SheetReadRequest(BaseModel):
    """Schema for reading from a sheet"""
    sheet_id: int = Field(..., description="Sheet ID")
    tab_name: Optional[str] = Field(None, description="Specific tab to read (optional)")
    range: Optional[str] = Field(None, description="Cell range (A1:B10 format)")


class SheetWriteRequest(BaseModel):
    """Schema for writing to a sheet"""
    sheet_id: int = Field(..., description="Sheet ID")
    tab_name: str = Field(..., description="Tab name to write to")
    append: bool = Field(False, description="Append or overwrite")
    data: SheetData = Field(..., description="Data to write")


class SheetResponse(BaseModel):
    """Schema for sheet response"""
    sheet_id: int
    workspace_id: int
    sheet_name: str
    google_sheet_id: str
    tab_names: Optional[List[str]] = None
    is_active: bool = True
    last_synced: Optional[datetime] = None
    sync_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

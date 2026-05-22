"""Sheets Router - Handles Google Sheets expense endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from config.database import get_db
from config.config import settings
from services.sheets_service import get_categories, append_expense, read_expenses
from services.auth_service import has_valid_token
from schemas.sheets_ops import (
    ExpenseCreate,
    ExpenseRow,
    ExpenseCreateResponse,
    CategoryListResponse,
)
from exceptions import NoValidTokenError
from typing import List

router = APIRouter(tags=["sheets"])


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Return distinct category values from the Danh mục column."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    categories = get_categories(db, user_id, resolved_sheet_id)
    return CategoryListResponse(categories=categories)


@router.post("/expenses", response_model=ExpenseCreateResponse, status_code=201)
async def create_expense(
    request: ExpenseCreate,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Append one expense row to the sheet."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    result = append_expense(
        db=db,
        user_id=user_id,
        sheet_id=resolved_sheet_id,
        date=request.date,
        amount=request.amount,
        description=request.description,
        category=request.category,
    )
    return ExpenseCreateResponse(
        success=True,
        row_number=result.get("row_number"),
        data=ExpenseRow(**result),
    )


@router.get("/expenses", response_model=List[ExpenseRow])
async def list_expenses(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    limit: int = Query(50, description="Max rows to return", ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return the last N expense rows from the sheet."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    rows = read_expenses(db, user_id, resolved_sheet_id, limit)
    return [ExpenseRow(**r) for r in rows]

"""Sheets Router - Handles Google Sheets expense endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from config.database import get_db
from config.config import settings
from services.sheets_service import get_categories, append_expense, read_expenses, get_summary_data, delete_expense, update_expense, update_balance, update_budget, add_category, delete_category
from services.auth_service import has_valid_token
from schemas.sheets_ops import (
    ExpenseCreate,
    ExpenseRow,
    ExpenseCreateResponse,
    CategoryListResponse,
    SummaryDataResponse,
    UpdateBalanceRequest,
    UpdateBudgetRequest,
    ManageCategoryRequest,
    SuccessResponse,
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


@router.get("/summary", response_model=SummaryDataResponse)
async def get_summary(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Return summary data: opening_balance, closing_balance, total_expenses, total_income."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    summary = get_summary_data(db, user_id, resolved_sheet_id)
    return SummaryDataResponse(**summary)


@router.delete("/expenses/{row_number}", response_model=SuccessResponse, status_code=200)
async def delete_expense_row(
    row_number: int,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Delete an expense row by row number."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    delete_expense(db, user_id, resolved_sheet_id, row_number)
    return SuccessResponse(success=True)


@router.put("/expenses/{row_number}", response_model=ExpenseRow, status_code=200)
async def update_expense_row(
    row_number: int,
    request: ExpenseCreate,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Update an expense row by row number."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    result = update_expense(
        db=db,
        user_id=user_id,
        sheet_id=resolved_sheet_id,
        row_number=row_number,
        date=request.date,
        amount=request.amount,
        description=request.description,
        category=request.category,
    )
    return ExpenseRow(**result)


@router.put("/balance", response_model=UpdateBalanceRequest, status_code=200)
async def update_balance_endpoint(
    request: UpdateBalanceRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Update opening and/or closing balance."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    result = update_balance(
        db=db,
        user_id=user_id,
        sheet_id=resolved_sheet_id,
        opening_balance=request.opening_balance,
        closing_balance=request.closing_balance,
    )
    return UpdateBalanceRequest(**result)


@router.put("/budget", response_model=UpdateBudgetRequest, status_code=200)
async def update_budget_endpoint(
    request: UpdateBudgetRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Update budget for a category."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    result = update_budget(
        db=db,
        user_id=user_id,
        sheet_id=resolved_sheet_id,
        category=request.category,
        budget_amount=request.budget_amount,
        is_income=request.is_income,
    )
    return UpdateBudgetRequest(**result)


@router.post("/categories", response_model=ManageCategoryRequest, status_code=201)
async def add_category_endpoint(
    request: ManageCategoryRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Add a new category."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    result = add_category(
        db=db,
        user_id=user_id,
        sheet_id=resolved_sheet_id,
        category=request.category,
        is_income=request.is_income,
    )
    return ManageCategoryRequest(**result)


@router.delete("/categories", response_model=SuccessResponse, status_code=200)
async def delete_category_endpoint(
    request: ManageCategoryRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to GOOGLE_SHEET_ID env)"),
    db: Session = Depends(get_db),
):
    """Delete a category."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    resolved_sheet_id = sheet_id or settings.google_sheet_id
    delete_category(
        db=db,
        user_id=user_id,
        sheet_id=resolved_sheet_id,
        category=request.category,
        is_income=request.is_income,
    )
    return SuccessResponse(success=True)

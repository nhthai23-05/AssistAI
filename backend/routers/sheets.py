"""Sheets Router - Handles Google Sheets expense endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from config.database import get_db
from services.sheets_service import (
    get_categories, get_income_categories,
    append_expense, read_expenses, get_summary_data,
    delete_expense, update_expense, update_balance, update_budget,
    add_category, delete_category,
    read_income_transactions, append_income, update_income,
    get_user_sheet_id, set_user_sheet_id, get_budgets, clear_transactions,
)
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
    BudgetListResponse,
    BudgetItem,
    NewMonthRequest,
    NewMonthResponse,
    SheetConfigResponse,
)
from exceptions import NoValidTokenError
from typing import List

router = APIRouter(tags=["sheets"])


def _resolve(sheet_id_param, db, user_id):
    """Return sheet_id: explicit param → user DB record → .env fallback."""
    return sheet_id_param or get_user_sheet_id(db, user_id)


@router.get("/sheet-id", response_model=SheetConfigResponse)
async def get_sheet_config(
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db),
):
    """Return the current Google Sheet ID configured for this user."""
    sid = get_user_sheet_id(db, user_id)
    return SheetConfigResponse(
        sheet_id=sid or None,
        sheet_url=f"https://docs.google.com/spreadsheets/d/{sid}/edit" if sid else None,
    )


@router.get("/budgets", response_model=BudgetListResponse)
async def list_budgets(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Return per-category planned budgets from the Tóm tắt sheet."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    result = get_budgets(db, user_id, sid)
    return BudgetListResponse(
        expense=[BudgetItem(**b) for b in result["expense"]],
        income=[BudgetItem(**b) for b in result["income"]],
    )


@router.post("/new-month", response_model=NewMonthResponse)
async def start_new_month(
    request: NewMonthRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db),
):
    """
    Switch to a new month's Google Sheet:
    1. Read closing_balance from current sheet.
    2. Write it as opening_balance in the new sheet.
    3. Clear all transaction rows in the new sheet (keeps headers + budgets).
    4. Save new_sheet_id to user DB record.
    """
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    old_sid = get_user_sheet_id(db, user_id)
    new_sid = request.new_sheet_id.strip()

    old_summary = get_summary_data(db, user_id, old_sid)
    closing_balance = old_summary.get("closing_balance", 0.0)

    update_balance(db, user_id, new_sid, opening_balance=closing_balance)
    clear_transactions(db, user_id, new_sid)
    set_user_sheet_id(db, user_id, new_sid)

    return NewMonthResponse(
        success=True,
        new_sheet_id=new_sid,
        opening_balance=closing_balance,
        sheet_url=f"https://docs.google.com/spreadsheets/d/{new_sid}/edit",
    )


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Return distinct category values from the Danh mục column."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    categories = get_categories(db, user_id, sid)
    return CategoryListResponse(categories=categories)


@router.get("/income-categories", response_model=CategoryListResponse)
async def list_income_categories(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Return income category values from the Tóm tắt sheet (H28:H44)."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    categories = get_income_categories(db, user_id, sid)
    return CategoryListResponse(categories=categories)


@router.post("/expenses", response_model=ExpenseCreateResponse, status_code=201)
async def create_expense(
    request: ExpenseCreate,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Append one expense row to the sheet."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    result = append_expense(
        db=db, user_id=user_id, sheet_id=sid,
        date=request.date, amount=request.amount,
        description=request.description, category=request.category,
    )
    return ExpenseCreateResponse(success=True, row_number=result.get("row_number"), data=ExpenseRow(**result))


@router.get("/expenses", response_model=List[ExpenseRow])
async def list_expenses(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    limit: int = Query(50, description="Max rows to return", ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return the last N expense rows from the sheet."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    rows = read_expenses(db, user_id, sid, limit)
    return [ExpenseRow(**r) for r in rows]


@router.get("/summary", response_model=SummaryDataResponse)
async def get_summary(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Return summary data: opening_balance, closing_balance, total_expenses, total_income."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    summary = get_summary_data(db, user_id, sid)
    if sid:
        summary["sheet_url"] = f"https://docs.google.com/spreadsheets/d/{sid}/edit"
    return SummaryDataResponse(**summary)


@router.delete("/expenses/{row_number}", response_model=SuccessResponse, status_code=200)
async def delete_expense_row(
    row_number: int,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Delete an expense row by row number."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    delete_expense(db, user_id, sid, row_number)
    return SuccessResponse(success=True)


@router.put("/expenses/{row_number}", response_model=ExpenseRow, status_code=200)
async def update_expense_row(
    row_number: int,
    request: ExpenseCreate,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Update an expense row by row number."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    result = update_expense(
        db=db, user_id=user_id, sheet_id=sid, row_number=row_number,
        date=request.date, amount=request.amount,
        description=request.description, category=request.category,
    )
    return ExpenseRow(**result)


@router.put("/balance", response_model=UpdateBalanceRequest, status_code=200)
async def update_balance_endpoint(
    request: UpdateBalanceRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Update opening and/or closing balance."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    result = update_balance(
        db=db, user_id=user_id, sheet_id=sid,
        opening_balance=request.opening_balance,
        closing_balance=request.closing_balance,
    )
    return UpdateBalanceRequest(**result)


@router.put("/budget", response_model=UpdateBudgetRequest, status_code=200)
async def update_budget_endpoint(
    request: UpdateBudgetRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Update budget for a category."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    result = update_budget(
        db=db, user_id=user_id, sheet_id=sid,
        category=request.category, budget_amount=request.budget_amount,
        is_income=request.is_income,
    )
    return UpdateBudgetRequest(**result)


@router.get("/income-transactions", response_model=List[ExpenseRow])
async def list_income_transactions(
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    limit: int = Query(50, description="Max rows to return", ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return the last N income rows from the Giao dịch sheet (columns G:J)."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    rows = read_income_transactions(db, user_id, sid, limit)
    return [ExpenseRow(**r) for r in rows]


@router.post("/income", response_model=ExpenseCreateResponse, status_code=201)
async def create_income(
    request: ExpenseCreate,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Append one income row to the Giao dịch sheet (columns G:J)."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    result = append_income(
        db=db, user_id=user_id, sheet_id=sid,
        date=request.date, amount=request.amount,
        description=request.description, category=request.category,
    )
    return ExpenseCreateResponse(success=True, row_number=result.get("row_number"), data=ExpenseRow(**result))


@router.put("/income/{row_number}", response_model=ExpenseRow, status_code=200)
async def update_income_row(
    row_number: int,
    request: ExpenseCreate,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Update an income row in the Giao dịch sheet (columns G:J)."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    result = update_income(
        db=db, user_id=user_id, sheet_id=sid, row_number=row_number,
        date=request.date, amount=request.amount,
        description=request.description, category=request.category,
    )
    return ExpenseRow(**result)


@router.delete("/income/{row_number}", response_model=SuccessResponse, status_code=200)
async def delete_income_row(
    row_number: int,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Delete an income row by row number."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    delete_expense(db, user_id, sid, row_number)
    return SuccessResponse(success=True)


@router.post("/categories", response_model=ManageCategoryRequest, status_code=201)
async def add_category_endpoint(
    request: ManageCategoryRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Add a new category."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    result = add_category(db=db, user_id=user_id, sheet_id=sid,
                          category=request.category, is_income=request.is_income)
    return ManageCategoryRequest(**result)


@router.delete("/categories", response_model=SuccessResponse, status_code=200)
async def delete_category_endpoint(
    request: ManageCategoryRequest,
    user_id: int = Query(..., description="User ID", gt=0),
    sheet_id: str = Query(None, description="Google Sheet ID (defaults to user setting)"),
    db: Session = Depends(get_db),
):
    """Delete a category."""
    if not has_valid_token(db, user_id):
        raise NoValidTokenError(user_id)

    sid = _resolve(sheet_id, db, user_id)
    delete_category(db=db, user_id=user_id, sheet_id=sid,
                    category=request.category, is_income=request.is_income)
    return SuccessResponse(success=True)

from pydantic import BaseModel, Field
from typing import List, Optional


class ExpenseCreate(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format", pattern=r"^\d{4}-\d{2}-\d{2}$")
    amount: float = Field(..., gt=0, description="Amount (VND)")
    description: str = Field(..., min_length=1, max_length=500, description="Expense description")
    category: str = Field(..., min_length=1, max_length=100, description="Category (must match dropdown)")


class ExpenseRow(BaseModel):
    date: str
    amount: float
    description: str
    category: str
    row_number: Optional[int] = None


class CategoryListResponse(BaseModel):
    categories: List[str]


class ExpenseCreateResponse(BaseModel):
    success: bool
    row_number: Optional[int]
    data: ExpenseRow


class SummaryDataResponse(BaseModel):
    opening_balance: float = Field(..., description="Số dư đầu kỳ (from L8)")
    closing_balance: float = Field(..., description="Số dư cuối kỳ (from D17)")
    total_expenses: float = Field(..., description="Tổng chi phí thực tế")
    total_income: float = Field(..., description="Tổng thu nhập thực tế")


class UpdateBalanceRequest(BaseModel):
    opening_balance: Optional[float] = Field(None, description="New opening balance")
    closing_balance: Optional[float] = Field(None, description="New closing balance")


class UpdateBudgetRequest(BaseModel):
    category: str = Field(..., description="Category name")
    budget_amount: float = Field(..., gt=0, description="New budget amount")
    is_income: bool = Field(False, description="True for income, False for expense")


class ManageCategoryRequest(BaseModel):
    category: str = Field(..., description="Category name")
    is_income: bool = Field(False, description="True for income, False for expense")


class SuccessResponse(BaseModel):
    success: bool = True

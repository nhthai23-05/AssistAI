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

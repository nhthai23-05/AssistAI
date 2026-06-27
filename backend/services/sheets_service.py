"""Google Sheets Service"""
import re
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from services.auth_service import get_credentials_for_user
from exceptions import GoogleSheetsError, NoOAuthTokenError
from config.config import settings


def get_sheet_service(db: Session, user_id: int):
    """
    Authenticate and return Sheets API service for user.

    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If service creation fails
    """
    try:
        creds = get_credentials_for_user(db, user_id)
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise GoogleSheetsError(f"Token refresh failed: {str(e)}")
        return build("sheets", "v4", credentials=creds)
    except NoOAuthTokenError:
        raise
    except GoogleSheetsError:
        raise
    except Exception as e:
        raise GoogleSheetsError(f"Failed to create Sheets service: {str(e)}")


def _get_sheet_by_name(service, sheet_id: str, sheet_name: str) -> Optional[str]:
    """
    Get sheet title by matching name (case-insensitive).
    Returns the first matching sheet name, or None if not found.
    """
    try:
        meta = service.spreadsheets().get(
            spreadsheetId=sheet_id,
            fields="sheets.properties.title",
        ).execute()
        sheets = [s["properties"]["title"] for s in meta.get("sheets", [])]
        # Try exact match first, then case-insensitive
        for s in sheets:
            if s == sheet_name:
                return s
        for s in sheets:
            if s.lower() == sheet_name.lower():
                return s
        return None
    except HttpError as e:
        raise GoogleSheetsError(f"Cannot access spreadsheet: {str(e)}")


def _parse_amount(value: str) -> float:
    """
    Parse amount string in Vietnamese format.
    Examples: "27.000 ₫", "27000", "27.000 đ", "1.600.000,00 ₫"
    """
    if not value:
        return 0.0
    try:
        # Remove currency symbols
        v = str(value).replace("₫", "").replace("đ", "").strip()
        # Handle Vietnamese decimal separator (comma) and thousand separator (dot)
        # If has comma, it's decimal separator
        if "," in v:
            v = v.replace(".", "").replace(",", ".")
        else:
            # Otherwise remove dots (thousand separators)
            v = v.replace(".", "")
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _normalize_date_format(date_str: str) -> str:
    """
    Convert date from DD/MM/YYYY to YYYY-MM-DD format.
    Example: "01/05/2020" → "2020-05-01"
    """
    if not date_str:
        return ""
    try:
        parts = str(date_str).strip().split("/")
        if len(parts) == 3:
            day, month, year = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return date_str
    except Exception:
        return date_str


def get_income_categories(db: Session, user_id: int, sheet_id: str) -> List[str]:
    """
    Return income category list from "Tóm tắt" sheet, range H28:H44.
    H = category names, J = planned, K = actual.
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Tóm tắt")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!H28:H44",
        ).execute()

        values = result.get("values", [])
        categories = []
        for row in values:
            if row and len(row) > 0:
                cat = str(row[0]).strip()
                if cat:
                    categories.append(cat)

        return categories

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to get income categories: {str(e)}")


def read_income_transactions(
    db: Session,
    user_id: int,
    sheet_id: str,
    limit: int = 50,
) -> List[Dict]:
    """
    Return the last `limit` income rows from the "Giao dịch" sheet.
    Income columns: G=date (DD/MM/YYYY), H=amount, I=description, J=category.
    Reads from row 5 onwards.
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Giao dịch")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!G5:J",
        ).execute()

        values = result.get("values", [])
        total = len(values)
        rows = []

        start_idx = max(0, total - limit)
        for idx, row in enumerate(values[start_idx:], start=start_idx + 5):
            if not row or all(not str(cell).strip() for cell in row if cell):
                continue

            date_raw = row[0] if len(row) > 0 else ""

            if not str(date_raw).strip():
                continue

            date = _normalize_date_format(date_raw)

            amount = row[1] if len(row) > 1 else ""
            description = row[2] if len(row) > 2 else ""
            category = row[3] if len(row) > 3 else ""

            amount = _parse_amount(amount)

            rows.append({
                "date": date,
                "amount": amount,
                "description": description.strip(),
                "category": category.strip(),
                "row_number": idx,
            })

        return rows

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to read income transactions: {str(e)}")


def append_income(
    db: Session,
    user_id: int,
    sheet_id: str,
    date: str,
    amount: float,
    description: str,
    category: str,
) -> Dict:
    """
    Append one income row to the "Giao dịch" sheet, columns G:J.
    G=date, H=amount, I=description, J=category.
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Giao dịch")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        amount_display = f"{amount:,.0f}".replace(",", ".")

        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!G5:J",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [[date, amount_display + " ₫", description, category]]},
        ).execute()

        row_number: Optional[int] = None
        updated_range = result.get("updates", {}).get("updatedRange", "")
        match = re.search(r":J(\d+)", updated_range)
        if match:
            row_number = int(match.group(1))

        return {
            "date": date,
            "amount": amount,
            "description": description,
            "category": category,
            "row_number": row_number,
        }

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to append income: {str(e)}")


def update_income(
    db: Session,
    user_id: int,
    sheet_id: str,
    row_number: int,
    date: str,
    amount: float,
    description: str,
    category: str,
) -> Dict:
    """
    Update an income row in the "Giao dịch" sheet, columns G:J.
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Giao dịch")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        amount_display = f"{amount:,.0f}".replace(",", ".")

        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!G{row_number}:J{row_number}",
            valueInputOption="USER_ENTERED",
            body={"values": [[date, amount_display + " ₫", description, category]]},
        ).execute()

        return {
            "date": date,
            "amount": amount,
            "description": description,
            "category": category,
            "row_number": row_number,
        }

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to update income: {str(e)}")


def get_categories(db: Session, user_id: int, sheet_id: str) -> List[str]:
    """
    Return category list from "Tóm tắt" sheet, range B28:B41.
    These are the dropdown options for the "Giao dịch" sheet.

    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Tóm tắt")
        if not sheet_name:
            # Fallback to first sheet if "Tóm tắt" not found
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        # Read from B28:B41 (category list from Summary sheet)
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!B28:B41",
        ).execute()

        values = result.get("values", [])
        categories = []
        for row in values:
            if row and len(row) > 0:
                cat = str(row[0]).strip()
                if cat:  # Skip empty cells
                    categories.append(cat)

        return categories

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to get categories: {str(e)}")



def read_expenses(
    db: Session,
    user_id: int,
    sheet_id: str,
    limit: int = 50,
) -> List[Dict]:
    """
    Return the last `limit` expense rows from the "Giao dịch" sheet.
    Reads starting from row 5 and handles column offset.

    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        
        sheet_name = _get_sheet_by_name(service, sheet_id, "Giao dịch")
        if not sheet_name:
            # Fallback to first sheet if "Giao dịch" not found
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        # Read from row 5 onwards (accounting for possible empty first column)
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A5:E",
        ).execute()

        values = result.get("values", [])
        
        total = len(values)
        rows = []
        
        # Get last `limit` rows
        start_idx = max(0, total - limit)
        for idx, row in enumerate(values[start_idx:], start=start_idx + 5):
            # Skip completely empty rows
            if not row or all(not str(cell).strip() for cell in row if cell):
                continue
                
            # Determine which columns have data (may be offset by 1)
            if len(row) > 0 and not str(row[0]).strip() and len(row) > 1 and str(row[1]).strip():
                # Data starts from column B (index 1)
                date = row[1] if len(row) > 1 else ""
                amount = row[2] if len(row) > 2 else ""
                description = row[3] if len(row) > 3 else ""
                category = row[4] if len(row) > 4 else ""
            else:
                # Normal case: data in columns A-D
                date = row[0] if len(row) > 0 else ""
                amount = row[1] if len(row) > 1 else ""
                description = row[2] if len(row) > 2 else ""
                category = row[3] if len(row) > 3 else ""
            
            # Skip if no date
            if not str(date).strip():
                continue
            
            # Normalize date format from DD/MM/YYYY to YYYY-MM-DD
            date = _normalize_date_format(date)
            
            # Parse amount (handle Vietnamese format)
            amount = _parse_amount(amount)
            
            rows.append({
                "date": date,
                "amount": amount,
                "description": description.strip(),
                "category": category.strip(),
                "row_number": idx,
            })

        return rows

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to read expenses: {str(e)}")


def append_expense(
    db: Session,
    user_id: int,
    sheet_id: str,
    date: str,
    amount: float,
    description: str,
    category: str,
) -> Dict:
    """
    Append one expense row to the "Giao dịch" sheet.
    Appends to columns accounting for possible empty first column.

    Returns:
        Dict with date, amount, description, category, row_number

    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Giao dịch")
        if not sheet_name:
            # Fallback to first sheet if "Giao dịch" not found
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        # Format amount for display (with thousand separator and currency)
        amount_display = f"{amount:,.0f}".replace(",", ".")

        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!B:E",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [[date, amount_display + " ₫", description, category]]},
        ).execute()

        row_number: Optional[int] = None
        updated_range = result.get("updates", {}).get("updatedRange", "")
        match = re.search(r":E(\d+)", updated_range)
        if match:
            row_number = int(match.group(1))

        return {
            "date": date,
            "amount": amount,
            "description": description,
            "category": category,
            "row_number": row_number,
        }

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to append expense: {str(e)}")


def get_summary_data(db: Session, user_id: int, sheet_id: str) -> Dict:
    """
    Return summary data from "Tóm tắt" sheet:
    - opening_balance: L8
    - closing_balance: D17
    - total_expenses: Sum of expenses from Chi phí section (column E, rows 26-40)
    - total_income: Sum of income from Thu nhập section (column J, rows 26-33)

    Returns:
        Dict with keys: opening_balance, closing_balance, total_expenses, total_income
        All values are floats

    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Tóm tắt")
        if not sheet_name:
            # Fallback to first sheet
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        # Read all needed cells at once
        # L8: opening balance
        # D17: closing balance
        # E26:E40: expenses (actual values)
        # K28:K44: income (actual values)
        ranges = [
            f"{sheet_name}!L8",       # opening_balance
            f"{sheet_name}!D17",      # closing_balance
            f"{sheet_name}!E26:E40",  # expenses (column E = Thực tế)
            f"{sheet_name}!K28:K44",  # income (column K = Thực tế)
        ]

        result = service.spreadsheets().values().batchGet(
            spreadsheetId=sheet_id,
            ranges=ranges,
        ).execute()

        value_ranges = result.get("valueRanges", [])
        
        # Parse opening balance (L8)
        opening_balance = 0.0
        if len(value_ranges) > 0 and value_ranges[0].get("values"):
            opening_balance = _parse_amount(value_ranges[0]["values"][0][0])

        # Parse closing balance (D17)
        closing_balance = 0.0
        if len(value_ranges) > 1 and value_ranges[1].get("values"):
            closing_balance = _parse_amount(value_ranges[1]["values"][0][0])

        # Sum expenses (column E, rows 26-40)
        total_expenses = 0.0
        if len(value_ranges) > 2:
            for row in value_ranges[2].get("values", []):
                if row and len(row) > 0:
                    amt = _parse_amount(row[0])
                    if amt > 0:
                        total_expenses += amt

        # Sum income (column J, rows 26-33)
        total_income = 0.0
        if len(value_ranges) > 3:
            for row in value_ranges[3].get("values", []):
                if row and len(row) > 0:
                    amt = _parse_amount(row[0])
                    if amt > 0:
                        total_income += amt

        return {
            "opening_balance": opening_balance,
            "closing_balance": closing_balance,
            "total_expenses": total_expenses,
            "total_income": total_income,
        }

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to get summary data: {str(e)}")


def delete_expense(db: Session, user_id: int, sheet_id: str, row_number: int) -> bool:
    """
    Delete an expense row from the "Giao dịch" sheet.
    
    Args:
        row_number: The row number to delete (1-based)
    
    Returns:
        True if deleted successfully
    
    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Giao dịch")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        # Get sheet ID (numeric)
        meta = service.spreadsheets().get(
            spreadsheetId=sheet_id,
            fields="sheets.properties",
        ).execute()
        sheet_id_numeric = None
        for sheet in meta.get("sheets", []):
            if sheet["properties"]["title"] == sheet_name:
                sheet_id_numeric = sheet["properties"]["sheetId"]
                break

        if sheet_id_numeric is None:
            raise GoogleSheetsError("Could not find sheet ID")

        # Delete row
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id_numeric,
                                "dimension": "ROWS",
                                "startIndex": row_number - 1,
                                "endIndex": row_number,
                            }
                        }
                    }
                ]
            },
        ).execute()

        return True

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to delete expense: {str(e)}")


def update_expense(
    db: Session,
    user_id: int,
    sheet_id: str,
    row_number: int,
    date: str,
    amount: float,
    description: str,
    category: str,
) -> Dict:
    """
    Update an expense row in the "Giao dịch" sheet.
    
    Args:
        row_number: The row number to update (1-based)
    
    Returns:
        Dict with updated expense data
    
    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Giao dịch")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        # Format amount for display
        amount_display = f"{amount:,.0f}".replace(",", ".")

        # Update the row (B:E columns — column A is always empty)
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!B{row_number}:E{row_number}",
            valueInputOption="USER_ENTERED",
            body={"values": [[date, amount_display + " ₫", description, category]]},
        ).execute()

        return {
            "date": date,
            "amount": amount,
            "description": description,
            "category": category,
            "row_number": row_number,
        }

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to update expense: {str(e)}")


def update_balance(
    db: Session,
    user_id: int,
    sheet_id: str,
    opening_balance: Optional[float] = None,
    closing_balance: Optional[float] = None,
) -> Dict:
    """
    Update opening and/or closing balance in "Tóm tắt" sheet.
    
    Args:
        opening_balance: New opening balance (L8), optional
        closing_balance: New closing balance (D17), optional
    
    Returns:
        Dict with updated balances
    
    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Tóm tắt")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        updates = []
        
        if opening_balance is not None:
            updates.append({
                "range": f"{sheet_name}!L8",
                "values": [[opening_balance]],
            })
        
        if closing_balance is not None:
            updates.append({
                "range": f"{sheet_name}!D17",
                "values": [[closing_balance]],
            })

        if updates:
            service.spreadsheets().values().batchUpdate(
                spreadsheetId=sheet_id,
                body={"data": updates, "valueInputOption": "USER_ENTERED"},
            ).execute()

        return {
            "opening_balance": opening_balance,
            "closing_balance": closing_balance,
        }

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to update balance: {str(e)}")


def update_budget(
    db: Session,
    user_id: int,
    sheet_id: str,
    category: str,
    budget_amount: float,
    is_income: bool = False,
) -> Dict:
    """
    Update budget for a category in "Tóm tắt" sheet.
    
    Args:
        category: Category name
        budget_amount: New budget amount
        is_income: True for income budget (K), False for expense budget (D)
    
    Returns:
        Dict with updated category and budget
    
    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Tóm tắt")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        # Read the category list to find the row
        if is_income:
            # Income categories in H28:H44; planned budget in column J
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!H28:H44",
            ).execute()
            start_row = 28
            col = "J"
        else:
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!B26:B40",
            ).execute()
            start_row = 26
            col = "D"

        values = result.get("values", [])
        
        # Find category row
        row_offset = None
        for idx, row in enumerate(values):
            if row and len(row) > 0 and str(row[0]).strip() == category:
                row_offset = idx
                break

        if row_offset is None:
            raise GoogleSheetsError(f"Category '{category}' not found")

        target_row = start_row + row_offset
        
        # Update budget
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!{col}{target_row}",
            valueInputOption="USER_ENTERED",
            body={"values": [[budget_amount]]},
        ).execute()

        return {
            "category": category,
            "budget_amount": budget_amount,
            "is_income": is_income,
        }

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to update budget: {str(e)}")


def add_category(
    db: Session,
    user_id: int,
    sheet_id: str,
    category: str,
    is_income: bool = False,
) -> Dict:
    """
    Add a new category to the category list in "Tóm tắt" sheet.
    
    Args:
        category: New category name
        is_income: True for income category, False for expense category
    
    Returns:
        Dict with added category
    
    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Tóm tắt")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        if is_income:
            # Income categories: H28:H44. Find first empty row.
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!H28:H44",
            ).execute()
            values = result.get("values", [])
            for idx, row in enumerate(values):
                if not row or not str(row[0]).strip():
                    target_row = 28 + idx
                    break
            else:
                target_row = 28 + len(values)
            col = "H"
        else:
            # Find first empty row in B26:B40
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!B26:B40",
            ).execute()
            values = result.get("values", [])
            for idx, row in enumerate(values):
                if not row or not str(row[0]).strip():
                    target_row = 26 + idx
                    break
            else:
                target_row = 26 + len(values)
            col = "B"

        # Add category
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!{col}{target_row}",
            valueInputOption="USER_ENTERED",
            body={"values": [[category]]},
        ).execute()

        return {
            "category": category,
            "is_income": is_income,
            "row": target_row,
        }

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to add category: {str(e)}")


def get_user_sheet_id(db: Session, user_id: int) -> str:
    """
    Return the Google Sheet ID for user.
    Priority: user.google_sheet_id in DB → settings.google_sheet_id from .env
    """
    from models.user import User
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.google_sheet_id:
        return user.google_sheet_id
    return settings.google_sheet_id


def set_user_sheet_id(db: Session, user_id: int, sheet_id: str) -> None:
    """Persist a new Google Sheet ID for user in DB."""
    from models.user import User
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise GoogleSheetsError(f"User {user_id} not found")
    user.google_sheet_id = sheet_id
    db.commit()


def get_budgets(db: Session, user_id: int, sheet_id: str) -> Dict:
    """
    Read category names + planned amounts from "Tóm tắt" sheet.
    Expense: B26:D41 (col B = name, col D = planned).
    Income:  H28:J44 (col H = name, col J = planned).
    Returns {"expense": [{name, planned}], "income": [{name, planned}]}
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Tóm tắt")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id, fields="sheets.properties.title"
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        result = service.spreadsheets().values().batchGet(
            spreadsheetId=sheet_id,
            ranges=[
                f"{sheet_name}!B26:D41",
                f"{sheet_name}!H28:K44",
            ],
        ).execute()

        value_ranges = result.get("valueRanges", [])

        expense_budgets = []
        for row in value_ranges[0].get("values", []) if value_ranges else []:
            name = str(row[0]).strip() if len(row) > 0 else ""
            planned = _parse_amount(row[2]) if len(row) > 2 else 0.0
            if name:
                expense_budgets.append({"name": name, "planned": planned})

        income_budgets = []
        for row in value_ranges[1].get("values", []) if len(value_ranges) > 1 else []:
            name = str(row[0]).strip() if len(row) > 0 else ""
            planned = _parse_amount(row[2]) if len(row) > 2 else 0.0
            actual = _parse_amount(row[3]) if len(row) > 3 else 0.0
            if name:
                income_budgets.append({"name": name, "planned": planned, "actual": actual})

        return {"expense": expense_budgets, "income": income_budgets}

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to get budgets: {str(e)}")


def clear_transactions(db: Session, user_id: int, sheet_id: str) -> None:
    """
    Clear all transaction rows (row 5 onwards) in the "Giao dịch" sheet.
    Clears expense columns B:E and income columns G:J, keeps headers.
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Giao dịch")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id, fields="sheets.properties.title"
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        service.spreadsheets().values().batchClear(
            spreadsheetId=sheet_id,
            body={"ranges": [f"{sheet_name}!B5:E", f"{sheet_name}!G5:J"]},
        ).execute()

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to clear transactions: {str(e)}")


def delete_category(
    db: Session,
    user_id: int,
    sheet_id: str,
    category: str,
    is_income: bool = False,
) -> bool:
    """
    Delete a category from the category list in "Tóm tắt" sheet.
    
    Args:
        category: Category name to delete
        is_income: True for income category, False for expense category
    
    Returns:
        True if deleted successfully
    
    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_sheet_by_name(service, sheet_id, "Tóm tắt")
        if not sheet_name:
            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets.properties.title",
            ).execute()
            sheet_name = meta["sheets"][0]["properties"]["title"]

        if is_income:
            # Income categories: H28:H44
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!H28:H44",
            ).execute()
            start_row = 28
            col = "H"
        else:
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{sheet_name}!B26:B40",
            ).execute()
            start_row = 26
            col = "B"

        values = result.get("values", [])

        # Find category row
        row_offset = None
        for idx, row in enumerate(values):
            if row and len(row) > 0 and str(row[0]).strip() == category:
                row_offset = idx
                break

        if row_offset is None:
            raise GoogleSheetsError(f"Category '{category}' not found")

        # Clear the cell (set to empty)
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!{col}{start_row + row_offset}",
            valueInputOption="USER_ENTERED",
            body={"values": [[""]]},
        ).execute()

        return True

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to delete category: {str(e)}")

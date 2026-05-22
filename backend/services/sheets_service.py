"""Google Sheets Service"""
import re
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from services.auth_service import get_credentials_for_user
from exceptions import GoogleSheetsError, NoOAuthTokenError


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


def _get_first_sheet_name(service, sheet_id: str) -> str:
    """Return the title of the first sheet tab."""
    try:
        meta = service.spreadsheets().get(
            spreadsheetId=sheet_id,
            fields="sheets.properties.title",
        ).execute()
        return meta["sheets"][0]["properties"]["title"]
    except HttpError as e:
        raise GoogleSheetsError(f"Cannot access spreadsheet: {str(e)}")


def get_categories(db: Session, user_id: int, sheet_id: str) -> List[str]:
    """
    Return distinct non-empty values from the Danh mục column (column D).

    Reads rows D2:D downward and deduplicates while preserving order.

    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_first_sheet_name(service, sheet_id)

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!D2:D",
        ).execute()

        values = result.get("values", [])
        seen: dict = {}
        for row in values:
            if row and row[0].strip():
                seen.setdefault(row[0].strip(), None)

        return list(seen.keys())

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to get categories: {str(e)}")


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
    Append one expense row to the sheet (columns A–D: Ngày, Số tiền, Mô tả, Danh mục).

    Returns:
        Dict with date, amount, description, category, row_number

    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_first_sheet_name(service, sheet_id)

        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A:D",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [[date, amount, description, category]]},
        ).execute()

        row_number: Optional[int] = None
        updated_range = result.get("updates", {}).get("updatedRange", "")
        match = re.search(r":D(\d+)", updated_range)
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


def read_expenses(
    db: Session,
    user_id: int,
    sheet_id: str,
    limit: int = 50,
) -> List[Dict]:
    """
    Return the last `limit` expense rows from the sheet.

    Raises:
        NoOAuthTokenError: If user has no valid OAuth token
        GoogleSheetsError: If Sheets API call fails
    """
    try:
        service = get_sheet_service(db, user_id)
        sheet_name = _get_first_sheet_name(service, sheet_id)

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A2:D",
        ).execute()

        values = result.get("values", [])
        total = len(values)
        rows = []
        for i, row in enumerate(values[-limit:], start=total - min(limit, total) + 2):
            rows.append({
                "date": row[0] if len(row) > 0 else "",
                "amount": float(row[1]) if len(row) > 1 and row[1] else 0.0,
                "description": row[2] if len(row) > 2 else "",
                "category": row[3] if len(row) > 3 else "",
                "row_number": i,
            })

        return rows

    except (NoOAuthTokenError, GoogleSheetsError):
        raise
    except HttpError as e:
        raise GoogleSheetsError(f"Sheets API error: {str(e)}")
    except Exception as e:
        raise GoogleSheetsError(f"Failed to read expenses: {str(e)}")

"""
Database operation exceptions
"""

from typing import Optional, Dict
from .base import AssistAIException


class DatabaseError(AssistAIException):
    """Database operation failed"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            status_code=500
        )


class TransactionError(DatabaseError):
    """Database transaction failed"""
    def __init__(self, message: str = "Transaction failed"):
        super().__init__(message=message)


class ResourceNotFoundError(AssistAIException):
    """Base resource not found error"""
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[int] = None,
        identifier: Optional[str] = None
    ):
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        if identifier:
            details["identifier"] = identifier
        
        message = f"{resource_type.capitalize()} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        elif identifier:
            message += f" ({identifier})"
        
        super().__init__(
            message=message,
            error_code=f"{resource_type.upper()}_NOT_FOUND",
            details=details,
            status_code=404
        )


class UserNotFoundError(ResourceNotFoundError):
    """User with given ID/email not found"""
    def __init__(self, user_id: Optional[int] = None, email: Optional[str] = None):
        super().__init__(
            resource_type="user",
            resource_id=user_id,
            identifier=email
        )


class SessionNotFoundError(ResourceNotFoundError):
    """Chat session not found"""
    def __init__(self, session_id: int):
        super().__init__(resource_type="session", resource_id=session_id)


class WorkspaceNotFoundError(ResourceNotFoundError):
    """Workspace not found"""
    def __init__(self, workspace_id: int):
        super().__init__(resource_type="workspace", resource_id=workspace_id)


class CalendarNotFoundError(ResourceNotFoundError):
    """Calendar not found"""
    def __init__(self, calendar_id: int):
        super().__init__(resource_type="calendar", resource_id=calendar_id)


class EventNotFoundError(ResourceNotFoundError):
    """Calendar event not found"""
    def __init__(self, event_id: str):
        super().__init__(resource_type="event", identifier=event_id)


class MessageNotFoundError(ResourceNotFoundError):
    """Message not found"""
    def __init__(self, message_id: int):
        super().__init__(resource_type="message", resource_id=message_id)


class ConnectedAccountNotFoundError(ResourceNotFoundError):
    """Connected account not found"""
    def __init__(self, account_id: int):
        super().__init__(resource_type="connected_account", resource_id=account_id)


class SheetNotFoundError(ResourceNotFoundError):
    """Google Sheet not found"""
    def __init__(self, sheet_id: int):
        super().__init__(resource_type="sheet", resource_id=sheet_id)


class IntegrationNotFoundError(ResourceNotFoundError):
    """Integration not found"""
    def __init__(self, integration_id: int):
        super().__init__(resource_type="integration", resource_id=integration_id)


class DuplicateResourceError(AssistAIException):
    """Resource already exists (duplicate key violation)"""
    def __init__(
        self,
        resource_type: str,
        identifier: Optional[str] = None,
        message: Optional[str] = None
    ):
        details = {"resource_type": resource_type}
        if identifier:
            details["identifier"] = identifier
        
        if message:
            msg = message
        else:
            msg = f"{resource_type.capitalize()} already exists"
            if identifier:
                msg += f" ({identifier})"
        
        super().__init__(
            message=msg,
            error_code=f"{resource_type.upper()}_DUPLICATE",
            details=details,
            status_code=409
        )

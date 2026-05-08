"""
External service exceptions (Google APIs, OpenAI, etc.)
"""

from typing import Optional, Dict
from .base import AssistAIException


class ExternalServiceError(AssistAIException):
    """Error calling external service (Google API, OpenAI, etc.)"""
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: int = 503
    ):
        super().__init__(
            message=f"{service_name} error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name},
            status_code=status_code
        )


class GoogleCalendarError(ExternalServiceError):
    """Error from Google Calendar API"""
    def __init__(self, message: str):
        super().__init__(service_name="Google Calendar", message=message)


class GoogleSheetsError(ExternalServiceError):
    """Error from Google Sheets API"""
    def __init__(self, message: str):
        super().__init__(service_name="Google Sheets", message=message)


class GoogleOAuthError(ExternalServiceError):
    """Error during Google OAuth flow"""
    def __init__(self, message: str):
        super().__init__(service_name="Google OAuth", message=message)


class OpenAIError(ExternalServiceError):
    """Error from OpenAI API"""
    def __init__(self, message: str):
        super().__init__(service_name="OpenAI", message=message)


class EventConflictError(AssistAIException):
    """Calendar event conflict (time overlap or duplicate)"""
    def __init__(
        self,
        event_id: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        if message is None:
            message = "Event time conflicts with existing event"
        
        if details is None:
            details = {}
        
        if event_id:
            details["event_id"] = event_id
        
        super().__init__(
            message=message,
            error_code="EVENT_CONFLICT",
            details=details,
            status_code=409
        )

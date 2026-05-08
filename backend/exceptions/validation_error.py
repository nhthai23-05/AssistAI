"""
Validation error for input validation
"""

from typing import Optional, Dict
from .base import AssistAIException


class ValidationError(AssistAIException):
    """Input validation failed"""
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        if details is None:
            details = {}
        
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=400
        )

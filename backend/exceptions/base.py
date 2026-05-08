"""
Base exception class for all AssistAI exceptions
"""

from typing import Optional, Dict, Any


class AssistAIException(Exception):
    """
    Base exception for all AssistAI custom exceptions
    
    All exceptions should inherit from this to be properly handled by the exception handlers
    """
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

    def __repr__(self):
        return f"<{self.__class__.__name__}(error_code={self.error_code}, message={self.message})>"

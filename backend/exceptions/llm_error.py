"""
LLM (Large Language Model) processing exceptions
"""

from typing import Optional, Dict
from .base import AssistAIException


class ProcessingError(AssistAIException):
    """Error during data processing"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            details=details,
            status_code=422
        )


class LLMProcessingError(ProcessingError):
    """Error processing AI request or response"""
    def __init__(self, message: str):
        super().__init__(message=f"AI processing failed: {message}")


class JSONParseError(ProcessingError):
    """Failed to parse JSON response from LLM"""
    def __init__(self, message: str = "Failed to parse JSON"):
        super().__init__(message=message)


class EventParsingError(ProcessingError):
    """Failed to parse event details from natural language"""
    def __init__(self, message: str):
        super().__init__(message=f"Failed to parse event: {message}")


class ActionDetectionError(ProcessingError):
    """Failed to detect action from user request"""
    def __init__(self, message: str = "Unable to determine action from request"):
        super().__init__(message=message)

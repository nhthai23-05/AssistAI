from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ErrorResponse(BaseModel):
    """Standard error response for all API endpoints"""
    error_code: str = Field(
        ..., 
        description="Machine-readable error code (e.g., 'USER_NOT_FOUND', 'AUTH_FAILED')"
    )
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(
        None, 
        description="Additional error details (field names, validation errors, etc)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="ISO 8601 timestamp of error"
    )
    path: Optional[str] = Field(None, description="API endpoint path that caused error")
    request_id: Optional[str] = Field(
        None, 
        description="Unique request ID for tracing/logging"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "SESSION_NOT_FOUND",
                "message": "Session with ID 123 not found",
                "details": {"session_id": 123},
                "timestamp": "2026-05-06T10:30:00Z",
                "path": "/api/chat/message",
                "request_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6"
            }
        }


class ValidationErrorDetail(BaseModel):
    """Detail for validation error"""
    field: str = Field(..., description="Field that failed validation")
    value: Optional[str] = Field(None, description="Invalid value")
    error: str = Field(..., description="Validation error message")


class ValidationErrorResponse(ErrorResponse):
    """Error response for validation failures"""
    details: list[ValidationErrorDetail] = Field(
        ..., 
        description="List of validation errors by field"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [
                    {
                        "field": "email",
                        "value": "invalid-email",
                        "error": "Invalid email format"
                    }
                ],
                "timestamp": "2026-05-06T10:30:00Z",
                "path": "/api/users/create",
                "request_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6"
            }
        }

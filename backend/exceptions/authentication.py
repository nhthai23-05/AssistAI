"""
Authentication and authorization exceptions
"""

from typing import Optional, Dict
from .base import AssistAIException


class AuthenticationError(AssistAIException):
    """Base authentication error - use for unknown auth issues"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="AUTH_FAILED",
            details=details,
            status_code=401
        )


class InvalidCredentialsError(AuthenticationError):
    """User provided invalid credentials (wrong password, invalid token, etc.)"""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message)


class InvalidEmailError(AuthenticationError):
    """Email format is invalid"""
    def __init__(self, email: str):
        # Call parent's parent to override error_code
        AssistAIException.__init__(
            self,
            message=f"Invalid email format: {email}",
            error_code="INVALID_EMAIL",
            details={"email": email},
            status_code=401
        )


class TokenExpiredError(AuthenticationError):
    """OAuth token has expired"""
    def __init__(self, token_id: Optional[int] = None):
        super().__init__(
            message="OAuth token has expired",
            details={"token_id": token_id} if token_id else {}
        )


class TokenRefreshFailedError(AuthenticationError):
    """Failed to refresh OAuth token"""
    def __init__(self, provider: str, reason: str = ""):
        super().__init__(
            message=f"Failed to refresh {provider} token: {reason}",
            details={"provider": provider}
        )


class NoValidTokenError(AuthenticationError):
    """User has no valid token for requested operation"""
    def __init__(self, user_id: int, provider: str = ""):
        super().__init__(
            message=f"No valid token found for user {user_id}" + (f" with provider {provider}" if provider else ""),
            details={"user_id": user_id, "provider": provider}
        )


class PermissionDeniedError(AssistAIException):
    """User doesn't have permission to perform action"""
    def __init__(self, message: str = "Permission denied", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            error_code="PERMISSION_DENIED",
            details=details,
            status_code=403
        )


class NoOAuthTokenError(AssistAIException):
    """User hasn't connected OAuth account"""
    def __init__(self, provider: str = "Google"):
        super().__init__(
            message=f"No {provider} account connected. Please authorize first.",
            error_code="NO_OAUTH_TOKEN",
            details={"provider": provider},
            status_code=400
        )

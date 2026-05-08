# Base classes
from .base import AssistAIException

# Authentication & Authorization
from .authentication import (
    AuthenticationError,
    InvalidCredentialsError,
    InvalidEmailError,
    TokenExpiredError,
    TokenRefreshFailedError,
    NoValidTokenError,
    PermissionDeniedError,
    NoOAuthTokenError,
)

# Database & Resources
from .database_error import (
    DatabaseError,
    TransactionError,
    UserNotFoundError,
    SessionNotFoundError,
    WorkspaceNotFoundError,
    CalendarNotFoundError,
    EventNotFoundError,
    MessageNotFoundError,
    ConnectedAccountNotFoundError,
    SheetNotFoundError,
    IntegrationNotFoundError,
    DuplicateResourceError,
)

# External Services
from .external_service_error import (
    ExternalServiceError,
    GoogleCalendarError,
    GoogleSheetsError,
    GoogleOAuthError,
    OpenAIError,
    EventConflictError,
)

# LLM Processing
from .llm_error import (
    LLMProcessingError,
    JSONParseError,
    EventParsingError,
    ActionDetectionError,
)

# Validation
from .validation_error import ValidationError

# Error utilities
from .error_codes import (
    get_status_code_for_error,
    ERROR_CODE_TO_STATUS,
)

# Handlers
from .handlers import (
    register_exception_handlers,
    general_exception_handler,
)

__all__ = [
    # Base
    "AssistAIException",
    
    # Authentication & Authorization
    "AuthenticationError",
    "InvalidCredentialsError",
    "InvalidEmailError",
    "TokenExpiredError",
    "TokenRefreshFailedError",
    "NoValidTokenError",
    "PermissionDeniedError",
    "NoOAuthTokenError",
    
    # Database & Resources
    "DatabaseError",
    "TransactionError",
    "UserNotFoundError",
    "SessionNotFoundError",
    "WorkspaceNotFoundError",
    "CalendarNotFoundError",
    "EventNotFoundError",
    "MessageNotFoundError",
    "ConnectedAccountNotFoundError",
    "SheetNotFoundError",
    "IntegrationNotFoundError",
    "DuplicateResourceError",
    
    # External Services
    "ExternalServiceError",
    "GoogleCalendarError",
    "GoogleSheetsError",
    "GoogleOAuthError",
    "OpenAIError",
    "EventConflictError",
    
    # LLM Processing
    "LLMProcessingError",
    "JSONParseError",
    "EventParsingError",
    "ActionDetectionError",
    
    # Validation
    "ValidationError",
    
    # Handlers
    "register_exception_handlers",
    "general_exception_handler",
    
    # Utilities
    "get_status_code_for_error",
    "ERROR_CODE_TO_STATUS",
]

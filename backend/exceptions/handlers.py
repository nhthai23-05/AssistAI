"""
FastAPI exception handlers - converts custom exceptions to ErrorResponse schemas
Should be registered in server.py with app.add_exception_handler()
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
from uuid import uuid4
from schemas.error import ErrorResponse
import logging

logger = logging.getLogger(__name__)

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions
    
    Catches any exception not handled by specific handlers
    Logs full traceback for debugging
    Returns generic INTERNAL_ERROR response
    """
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    
    # Log the full exception with traceback
    logger.exception(
        f"Unhandled Exception: {type(exc).__name__}",
        extra={
            "request_id": request_id,
            "path": str(request.url.path),
            "method": request.method
        }
    )
    
    # Build response (don't expose internal details to client)
    response_data = {
        "error_code": "INTERNAL_ERROR",
        "message": "An unexpected error occurred",
        "details": None,
        "timestamp": datetime.now().isoformat(),
        "path": str(request.url.path),
        "request_id": request_id
    }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI app
    
    Usage in server.py:
        from exceptions.handlers import register_exception_handlers
        
        app = FastAPI()
        register_exception_handlers(app)
    """
    app.add_exception_handler(Exception, general_exception_handler)

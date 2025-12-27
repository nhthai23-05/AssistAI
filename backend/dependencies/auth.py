from fastapi import HTTPException
from services.auth_service import has_valid_token

def require_auth():
    """Dependency để check authentication"""
    if not has_valid_token():
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Not authenticated",
                "message": "Please login with Google first",
                "login_url": "/api/auth/login"
            }
        )
    return True

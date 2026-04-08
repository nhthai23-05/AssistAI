from fastapi import HTTPException, Query
from sqlalchemy.orm import Session
from config.database import get_db
from services.auth_service import has_valid_token
from typing import Tuple

def require_auth_with_user(user_id: int = Query(...), db: Session = ...) -> Tuple[int, Session]:
    """
    Dependency để check authentication
    
    Args:
        user_id: User ID từ query parameter
        db: Database session
        
    Returns:
        Tuple of (user_id, db_session)
    """
    if not has_valid_token(db, user_id):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Not authenticated",
                "message": "Please login with Google first or token expired",
                "login_url": "/api/auth/login"
            }
        )
    return (user_id, db)

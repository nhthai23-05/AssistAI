from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from services.auth_service import (
    get_oauth_url,
    handle_oauth_callback,
    has_valid_token,
    logout as auth_logout
)

router = APIRouter()

@router.get("/status")
async def auth_status():
    """Check xem user đã login chưa"""
    is_authenticated = has_valid_token()
    return {
        "authenticated": is_authenticated,
        "message": "Logged in" if is_authenticated else "Not logged in"
    }

@router.get("/login")
async def login():
    """Bước 1: Tạo OAuth URL và redirect user đến Google"""
    auth_url = get_oauth_url()
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def auth_callback(code: str):
    """Bước 2: Google redirect về đây với code, lưu token"""
    try:
        handle_oauth_callback(code)
        
        html_content = """
        <html>
            <head><title>Login Successful</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>✅ Login Successful!</h1>
                <p>You can close this window and return to the app.</p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.post("/logout")
async def logout():
    """Logout: Xóa token"""
    auth_logout()
    return {"message": "Logged out successfully"}

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from config.config import settings
from config.database import get_db
from sqlalchemy.orm import Session
from services.auth_service import (
    handle_oauth_callback,
    has_valid_token,
    logout as auth_logout
)
from utils.oauth_utils import generate_pkce_pair, generate_authorization_url, validate_state
from utils.encryption import encrypt_data, decrypt_data
from pydantic import BaseModel

router = APIRouter()


class LogoutRequest(BaseModel):
    user_id: int


@router.get("/status")
async def auth_status(user_id: int = Query(...), db: Session = Depends(get_db)):
    """Check xem user đã login chưa"""
    try:
        is_authenticated = has_valid_token(db, user_id)
        return {
            "authenticated": is_authenticated,
            "user_id": user_id,
            "message": "Logged in" if is_authenticated else "Not logged in"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/login")
async def login():
    """Bước 1: Tạo OAuth URL với PKCE và redirect user đến Google"""
    try:
        # Generate PKCE parameters
        state, code_verifier, code_challenge = generate_pkce_pair()
        
        # Create authorization URL
        auth_url = generate_authorization_url(
            client_id=settings.google_client_id,
            redirect_uri=settings.google_redirect_uri,
            scopes=settings.google_scopes_list,
            state=state,
            code_challenge=code_challenge
        )
        
        # Encrypt and set HTTP-Only Cookie with PKCE data
        pkce_data = f"{state}|{code_verifier}"
        encrypted_pkce = encrypt_data(pkce_data)
        
        response = RedirectResponse(url=auth_url)
        response.set_cookie(
            key="pkce_state",
            value=encrypted_pkce,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=600  # 10 minutes expiry
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate login: {str(e)}")


@router.get("/callback")
async def auth_callback(code: str, state: str = Query(...), request: Request = None, db: Session = Depends(get_db)):
    """Bước 2: Google redirect về đây với code, exchange token"""
    try:
        # Get encrypted PKCE data from cookie
        encrypted_pkce = request.cookies.get("pkce_state")
        if not encrypted_pkce:
            html_content = """
            <html>
                <head><title>Login Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Login Failed</h1>
                    <p>Session expired. Please try login again.</p>
                </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=400)
        
        # Decrypt PKCE data
        try:
            pkce_data = decrypt_data(encrypted_pkce)
            session_state, code_verifier = pkce_data.split("|")
        except Exception as e:
            print(f"❌ Failed to decrypt PKCE data: {e}")
            html_content = """
            <html>
                <head><title>Login Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Login Failed</h1>
                    <p>Invalid session. Please try login again.</p>
                </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=400)
        
        # Validate state (CSRF protection)
        if not validate_state(state, session_state):
            print(f"❌ State mismatch: received {state}, expected {session_state}")
            html_content = """
            <html>
                <head><title>Login Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Login Failed</h1>
                    <p>Invalid state parameter (CSRF attack suspected).</p>
                </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=400)
        
        # Exchange code for token using code_verifier
        result = handle_oauth_callback(code, code_verifier, db)
        
        if not result:
            html_content = """
            <html>
                <head><title>Login Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Login Failed</h1>
                    <p>Failed to authenticate with Google. Please try again.</p>
                </body>
            </html>
            """
            return HTMLResponse(content=html_content, status_code=400)
        
        # Return success page with user_id encoded in URL
        user_id = result['user_id']
        html_content = f"""
        <html>
            <head><title>Login Successful</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>✅ Login Successful!</h1>
                <p>User ID: <strong>{user_id}</strong></p>
                <p>You can close this window and return to the app.</p>
                <script>
                    // Optionally pass user_id back to parent window
                    if (window.opener) {{
                        window.opener.postMessage({{type: 'auth_success', user_id: {user_id}}}, '*');
                    }}
                </script>
            </body>
        </html>
        """
        
        response = HTMLResponse(content=html_content)
        # Delete PKCE cookie after successful authentication
        response.delete_cookie("pkce_state")
        return response
    
    except Exception as e:
        print(f"❌ Callback error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.post("/logout")
async def logout(request: LogoutRequest, db: Session = Depends(get_db)):
    """Logout: Xóa token"""
    try:
        auth_logout(db, request.user_id)
        return {"message": "Logged out successfully", "user_id": request.user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


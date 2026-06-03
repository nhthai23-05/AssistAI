"""Authentication Router - Handles OAuth login/logout"""
from fastapi import APIRouter, Depends, Query, Request
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
from schemas.user import UserResponse
from exceptions import (
    GoogleOAuthError,
    InvalidEmailError,
    NoValidTokenError,
)

router = APIRouter()


@router.get("/status")
async def auth_status(
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db)
) -> dict:
    """
    Check authentication status for user
    
    - **user_id**: User ID (required)
    
    Returns:
        - **authenticated**: Boolean indicating if user is authenticated
        - **user_id**: User ID
    """
    is_authenticated = has_valid_token(db, user_id)
    return {
        "authenticated": is_authenticated,
        "user_id": user_id
    }


@router.get("/login")
async def login() -> RedirectResponse:
    """
    Step 1: Initiate OAuth login
    Generates PKCE parameters and redirects to Google authorization
    """
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
            secure=False,  # HTTP-safe for localhost; set True in production with HTTPS
            samesite="lax",
            max_age=600  # 10 minutes expiry
        )
        
        return response
    
    except Exception as e:
        raise GoogleOAuthError(f"Failed to initiate login: {str(e)}")


@router.get("/callback")
async def auth_callback(
    code: str,
    state: str = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Step 2: OAuth callback handler
    Exchanges authorization code for access token
    
    - **code**: Authorization code from Google (required)
    - **state**: State parameter for CSRF protection (required)
    """
    try:
        # Get encrypted PKCE data from cookie
        encrypted_pkce = request.cookies.get("pkce_state")
        if not encrypted_pkce:
            return HTMLResponse(
                content="""
                <html>
                    <head><title>Login Failed</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>❌ Login Failed</h1>
                        <p>Session expired. Please try login again.</p>
                    </body>
                </html>
                """,
                status_code=400
            )
        
        # Decrypt PKCE data
        try:
            pkce_data = decrypt_data(encrypted_pkce)
            session_state, code_verifier = pkce_data.split("|")
        except Exception:
            return HTMLResponse(
                content="""
                <html>
                    <head><title>Login Failed</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>❌ Login Failed</h1>
                        <p>Invalid session. Please try login again.</p>
                    </body>
                </html>
                """,
                status_code=400
            )
        
        # Validate state (CSRF protection)
        if not validate_state(state, session_state):
            return HTMLResponse(
                content="""
                <html>
                    <head><title>Login Failed</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>❌ Login Failed</h1>
                        <p>Invalid state parameter (CSRF attack suspected).</p>
                    </body>
                </html>
                """,
                status_code=400
            )
        
        # Exchange code for token using code_verifier
        try:
            result = handle_oauth_callback(code, code_verifier, db)
        except (GoogleOAuthError, InvalidEmailError) as e:
            return HTMLResponse(
                content=f"""
                <html>
                    <head><title>Login Failed</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>❌ Login Failed</h1>
                        <p>{str(e)}</p>
                    </body>
                </html>
                """,
                status_code=400
            )
        
        # Return success page with user_id
        user_id = result['user_id']
        email = result['email']
        
        html_content = f"""
        <html>
            <head>
                <title>Login Successful</title>
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; }}
                    .success {{ color: green; }}
                </style>
            </head>
            <body>
                <h1 class="success">✅ Login Successful!</h1>
                <p>Email: <strong>{email}</strong></p>
                <p>User ID: <strong>{user_id}</strong></p>
                <p>You can close this window and return to the app.</p>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage(
                            {{type: 'auth_success', user_id: {user_id}, email: '{email}'}},
                            '*'
                        );
                        window.close();
                    }}
                </script>
            </body>
        </html>
        """
        
        response = HTMLResponse(content=html_content)
        response.delete_cookie("pkce_state")
        return response
    
    except Exception as e:
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Login Failed</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Login Failed</h1>
                    <p>Authentication error: {str(e)}</p>
                </body>
            </html>
            """,
            status_code=500
        )


@router.post("/logout")
async def logout(
    user_id: int = Query(..., description="User ID", gt=0),
    db: Session = Depends(get_db)
) -> dict:
    """
    Logout user - delete OAuth token
    
    - **user_id**: User ID to logout (required)
    """
    success = auth_logout(db, user_id)
    return {
        "success": success,
        "message": "Logged out successfully" if success else "Logout failed",
        "user_id": user_id
    }


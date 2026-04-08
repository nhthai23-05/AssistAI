from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from pathlib import Path
import json
import requests
from config.config import settings
from sqlalchemy.orm import Session
from services.user_service import UserService
from services.oauth_token_service import OAuthTokenService
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta

CONFIG_PATH = Path(__file__).parent.parent / "config"
SCOPES = settings.google_scopes_list


def _exchange_code_for_token(code: str, code_verifier: str) -> Optional[Dict]:
    """
    Exchange authorization code for access token using PKCE
    
    Args:
        code: Authorization code from Google
        code_verifier: PKCE code verifier
        
    Returns:
        Dict with token data, or None if failed
    """
    try:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    except Exception as e:
        print(f"❌ Failed to exchange code for token: {e}")
        return None


def _get_google_user_info(access_token: str) -> Optional[Dict]:
    """
    Get user info from Google using access token
    
    Args:
        access_token: Google access token
        
    Returns:
        Dict with 'email' and 'name', or None if failed
    """
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        data = response.json()
        return {
            'email': data.get('email'),
            'name': data.get('name', data.get('email', 'User'))
        }
    except Exception as e:
        print(f"❌ Failed to get Google user info: {e}")
        return None


def handle_oauth_callback(code: str, code_verifier: str, db: Session) -> Optional[Dict]:
    """
    Xử lý callback từ Google
    - Exchange code để lấy credentials (với PKCE code_verifier)
    - Lấy user info từ Google
    - Tạo/update User trong DB
    - Lưu token vào DB (encrypted)
    
    Args:
        code: Authorization code từ Google
        code_verifier: PKCE code verifier
        db: Database session
        
    Returns:
        Dict with user_id and email, or None if failed
    """
    try:
        # Exchange authorization code for token (with PKCE)
        token_data = _exchange_code_for_token(code, code_verifier)
        if not token_data or "access_token" not in token_data:
            print("❌ Failed to exchange code for token")
            return None
        
        # Create credentials object from token data
        credentials = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=SCOPES
        )
        
        # Lấy user info từ Google
        user_info = _get_google_user_info(credentials.token)
        if not user_info or not user_info.get('email'):
            print("❌ Failed to get user email from Google")
            return None
        
        # Tạo hoặc update User trong DB
        existing_user = UserService.get_user(db, user_info['email'])
        if existing_user:
            user = existing_user
            is_created = False
        else:
            user = UserService.create_user(db, user_info['email'], user_info['name'])
            is_created = True
        
        # Calculate access token expiry
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        
        # Lưu token vào DB (encrypted)
        OAuthTokenService.save_token(
            db=db,
            user_id=user.user_id,
            provider="google",
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scope=" ".join(SCOPES),
            account_email=user_info['email']
        )
        
        print(f"✅ User {user_info['email']} authenticated successfully (ID: {user.user_id})")
        
        return {
            'user_id': user.user_id,
            'email': user.email,
            'name': user.name
        }
        
    except Exception as e:
        print(f"❌ OAuth callback failed: {e}")
        return None


def get_credentials_for_user(db: Session, user_id: int) -> Optional[Credentials]:
    """
    Load credentials từ DB (decrypted)
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Google Credentials object, or None if not found/malformed
    """
    token_data = OAuthTokenService.get_decrypted_credentials(db, user_id)
    
    if not token_data:
        print(f"❌ No token found for user {user_id}")
        return None
    
    try:
        credentials = Credentials(
            token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=token_data['scope'].split() if token_data.get('scope') else SCOPES
        )
        
        return credentials
        
    except Exception as e:
        print(f"❌ Error creating credentials object for user {user_id}: {e}")
        return None


def has_valid_token(db: Session, user_id: int) -> bool:
    """
    Check if user has valid token
    - Token exists
    - Not expired (or can refresh)
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if valid token exists
    """
    try:
        credentials = get_credentials_for_user(db, user_id)
        
        if not credentials:
            return False
        
        # Check if expired
        if credentials.expired:
            # Try to refresh
            if credentials.refresh_token:
                try:
                    print("⏳ Token expired, refreshing...")
                    credentials.refresh(Request())
                    
                    # Update token in DB with new access token
                    expires_at = None
                    if credentials.expiry:
                        expires_at = credentials.expiry
                    
                    OAuthTokenService.update_token_expiry(
                        db=db,
                        user_id=user_id,
                        new_access_token=credentials.token,
                        expires_at=expires_at
                    )
                    
                    print("✅ Token refreshed successfully")
                    return True
                    
                except Exception as refresh_error:
                    print(f"❌ Token refresh failed: {refresh_error}")
                    return False
            else:
                print("❌ Token expired and no refresh_token available")
                return False
        
        # Token still valid
        return True
        
    except Exception as e:
        print(f"❌ Error checking token for user {user_id}: {e}")
        return False


def logout(db: Session, user_id: int) -> bool:
    """
    Logout user - delete token
    
    Args:
        db: Database session
        user_id: User ID to logout
        
    Returns:
        True if successful
    """
    try:
        OAuthTokenService.delete_token(db, user_id)
        print(f"✅ User {user_id} logged out")
        return True
    except Exception as e:
        print(f"❌ Logout failed for user {user_id}: {e}")
        return False
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
from exceptions import (
    GoogleOAuthError,
    InvalidEmailError,
    NoOAuthTokenError,
    TokenExpiredError,
    TokenRefreshFailedError,
    NoValidTokenError,
)

CONFIG_PATH = Path(__file__).parent.parent / "config"
SCOPES = settings.google_scopes_list


def _exchange_code_for_token(code: str, code_verifier: str) -> Dict:
    """
    Exchange authorization code for access token using PKCE
    
    Args:
        code: Authorization code from Google
        code_verifier: PKCE code verifier
        
    Returns:
        Dict with token data
        
    Raises:
        GoogleOAuthError: If token exchange fails
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
        
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        raise GoogleOAuthError(f"Failed to exchange authorization code: {str(e)}")
    except Exception as e:
        raise GoogleOAuthError(f"Unexpected error during token exchange: {str(e)}")


def _get_google_user_info(access_token: str) -> Dict:
    """
    Get user info from Google using access token
    
    Args:
        access_token: Google access token
        
    Returns:
        Dict with 'email' and 'name'
        
    Raises:
        GoogleOAuthError: If user info retrieval fails
        InvalidEmailError: If email is invalid
    """
    try:
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        email = data.get('email')
        if not email or '@' not in email:
            raise InvalidEmailError(email or "")
        
        return {
            'email': email,
            'name': data.get('name', email.split('@')[0])
        }
    
    except InvalidEmailError:
        raise
    except requests.exceptions.RequestException as e:
        raise GoogleOAuthError(f"Failed to get user info from Google: {str(e)}")
    except Exception as e:
        raise GoogleOAuthError(f"Unexpected error getting user info: {str(e)}")


def handle_oauth_callback(code: str, code_verifier: str, db: Session) -> Dict:
    """
    Handle OAuth callback from Google
    - Exchange code to get credentials (with PKCE code_verifier)
    - Get user info from Google
    - Create/update User in DB
    - Save encrypted token to DB
    
    Args:
        code: Authorization code from Google
        code_verifier: PKCE code verifier
        db: Database session
        
    Returns:
        Dict with user_id, email, and name
        
    Raises:
        GoogleOAuthError: If OAuth process fails
        InvalidEmailError: If email is invalid
    """
    try:
        # Exchange authorization code for token (with PKCE)
        token_data = _exchange_code_for_token(code, code_verifier)
        
        if "access_token" not in token_data:
            raise GoogleOAuthError("No access token in response")
        
        # Create credentials object from token data
        credentials = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=SCOPES
        )
        
        # Get user info from Google
        user_info = _get_google_user_info(credentials.token)
        
        # Create or get User in DB
        existing_user = UserService.get_user(db, user_info['email'])
        if existing_user:
            user = existing_user
        else:
            user = UserService.create_user(db, user_info['email'], user_info['name'])
        
        # Calculate access token expiry
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        
        # Save encrypted token to DB
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
        
        return {
            'user_id': user.user_id,
            'email': user.email,
            'name': user.name
        }
        
    except (GoogleOAuthError, InvalidEmailError):
        raise
    except Exception as e:
        raise GoogleOAuthError(f"OAuth callback failed: {str(e)}")


def get_credentials_for_user(db: Session, user_id: int) -> Optional[Credentials]:
    """
    Load credentials from DB (decrypted)
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Google Credentials object, or None if not found
        
    Raises:
        NoOAuthTokenError: If user has no valid token
    """
    try:
        token_data = OAuthTokenService.get_decrypted_credentials(db, user_id)
        
        if not token_data:
            raise NoOAuthTokenError("Google")
        
        credentials = Credentials(
            token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=token_data['scope'].split() if token_data.get('scope') else SCOPES
        )
        
        return credentials
        
    except NoOAuthTokenError:
        raise
    except Exception as e:
        raise NoOAuthTokenError(f"Failed to load credentials: {str(e)}")


def has_valid_token(db: Session, user_id: int) -> bool:
    """
    Check if user has valid token
    - Token exists
    - Not expired (or can refresh)
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if valid token exists, False otherwise
    """
    try:
        credentials = get_credentials_for_user(db, user_id)
        
        # Check if expired
        if credentials.expired:
            # Try to refresh
            if credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                    
                    # Update token in DB with new access token
                    expires_at = credentials.expiry if hasattr(credentials, 'expiry') else None
                    
                    OAuthTokenService.update_token_expiry(
                        db=db,
                        user_id=user_id,
                        new_access_token=credentials.token,
                        expires_at=expires_at
                    )
                    
                    return True
                    
                except Exception as refresh_error:
                    return False
            else:
                return False
        
        # Token still valid
        return True
        
    except:
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
        return True
    except Exception as e:
        return False
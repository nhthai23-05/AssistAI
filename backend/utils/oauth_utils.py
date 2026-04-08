"""OAuth 2.0 PKCE utilities for secure authorization flow"""
import secrets
import base64
import hashlib
from typing import Tuple, Dict, Optional
from urllib.parse import urlencode


def generate_pkce_pair() -> Tuple[str, str, str]:
    """
    Generate PKCE (Proof Key for Code Exchange) parameters
    
    Returns:
        Tuple of (state, code_verifier, code_challenge)
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Generate code_verifier (43-128 characters of unreserved characters)
    code_verifier = secrets.token_urlsafe(32)
    
    # Generate code_challenge from verifier using S256 method
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    
    return state, code_verifier, code_challenge


def generate_authorization_url(
    client_id: str,
    redirect_uri: str,
    scopes: list,
    state: str,
    code_challenge: str
) -> str:
    """
    Generate Google OAuth authorization URL with PKCE
    
    Args:
        client_id: Google OAuth client ID
        redirect_uri: Redirect URI registered with Google
        scopes: List of OAuth scopes
        state: State parameter for CSRF protection
        code_challenge: Code challenge for PKCE
        
    Returns:
        Full authorization URL
    """
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "consent"
    }
    
    return f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"


def validate_state(received_state: str, session_state: str) -> bool:
    """
    Validate state parameter from callback (CSRF protection)
    
    Args:
        received_state: State from callback URL
        session_state: State stored in session/cookie
        
    Returns:
        True if states match
    """
    return secrets.compare_digest(received_state, session_state)

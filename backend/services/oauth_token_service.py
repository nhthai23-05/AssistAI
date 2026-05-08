"""OAuth Token Management Service - Handles token storage and retrieval from database"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.oauth_token import OAuthToken
from models.connected_account import ConnectedAccount
from utils.encryption import encrypt_data, decrypt_data
from google.oauth2.credentials import Credentials
from typing import Optional, Dict
from exceptions import (
    NoOAuthTokenError,
    DatabaseError,
)


class OAuthTokenService:
    """Service for managing OAuth tokens in database"""
    
    @staticmethod
    def save_token(
        db: Session,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        scope: Optional[str] = None,
        account_email: Optional[str] = None
    ) -> OAuthToken:
        """
        Save or update OAuth token in database (encrypted)
        
        Since we don't support multiple tokens per user:
        - Delete existing token for this user/provider
        - Create new one
        
        Args:
            db: Database session
            user_id: User ID
            provider: Provider name (e.g., 'google', 'outlook')
            access_token: Access token string (required)
            refresh_token: Refresh token (optional)
            expires_at: Token expiration datetime (optional)
            scope: Token scopes (optional)
            account_email: Account email from provider (optional)
            
        Returns:
            Created/Updated OAuthToken
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Find existing ConnectedAccount for this user/provider
            connected_account = db.query(ConnectedAccount).filter(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == provider
            ).first()
            
            # Delete old token if exists
            if connected_account:
                db.query(OAuthToken).filter(
                    OAuthToken.connected_account_id == connected_account.connected_account_id
                ).delete()
            else:
                # Create new ConnectedAccount
                connected_account = ConnectedAccount(
                    user_id=user_id,
                    provider=provider,
                    account_email=account_email or "",
                    is_primary=True
                )
                db.add(connected_account)
                db.flush()
            
            # Update account email if provided
            if account_email:
                connected_account.account_email = account_email
            
            # Create new encrypted token
            oauth_token = OAuthToken(
                connected_account_id=connected_account.connected_account_id,
                access_token=encrypt_data(access_token),
                refresh_token=encrypt_data(refresh_token) if refresh_token else None,
                expires_at=expires_at,
                scope=scope
            )
            
            db.add(oauth_token)
            db.commit()
            db.refresh(oauth_token)
            
            return oauth_token
            
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to save OAuth token: {str(e)}")
    
    @staticmethod
    def get_token(
        db: Session,
        user_id: int,
        provider: str = "google"
    ) -> Optional[OAuthToken]:
        """
        Get OAuth token for user
        
        Args:
            db: Database session
            user_id: User ID
            provider: Provider name (default: 'google')
            
        Returns:
            OAuthToken or None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            connected_account = db.query(ConnectedAccount).filter(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == provider
            ).first()
            
            if not connected_account:
                return None
            
            oauth_token = db.query(OAuthToken).filter(
                OAuthToken.connected_account_id == connected_account.connected_account_id
            ).first()
            
            return oauth_token
            
        except Exception as e:
            raise DatabaseError(f"Failed to get OAuth token: {str(e)}")
    
    @staticmethod
    def get_decrypted_credentials(
        db: Session,
        user_id: int,
        provider: str = "google"
    ) -> Optional[Dict]:
        """
        Get decrypted token data for user
        
        Args:
            db: Database session
            user_id: User ID
            provider: Provider name (default: 'google')
            
        Returns:
            Dict with decrypted tokens: {'access_token', 'refresh_token', 'expires_at', 'scope'}
            None if not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            oauth_token = OAuthTokenService.get_token(db, user_id, provider)
            
            if not oauth_token:
                return None
            
            return {
                'access_token': decrypt_data(oauth_token.access_token),
                'refresh_token': decrypt_data(oauth_token.refresh_token) if oauth_token.refresh_token else None,
                'expires_at': oauth_token.expires_at,
                'scope': oauth_token.scope
            }
            
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to decrypt credentials: {str(e)}")
    
    @staticmethod
    def update_token_expiry(
        db: Session,
        user_id: int,
        new_access_token: str,
        expires_at: Optional[datetime] = None,
        provider: str = "google"
    ) -> OAuthToken:
        """
        Update token after refresh (when access token changes)
        
        Args:
            db: Database session
            user_id: User ID
            new_access_token: New access token
            expires_at: New expiration time
            provider: Provider name
            
        Returns:
            Updated OAuthToken
            
        Raises:
            NoOAuthTokenError: If token not found
            DatabaseError: If database operation fails
        """
        try:
            oauth_token = OAuthTokenService.get_token(db, user_id, provider)
            
            if not oauth_token:
                raise NoOAuthTokenError(provider)
            
            oauth_token.access_token = encrypt_data(new_access_token)
            if expires_at:
                oauth_token.expires_at = expires_at
            
            db.commit()
            db.refresh(oauth_token)
            
            return oauth_token
            
        except NoOAuthTokenError:
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to update token expiry: {str(e)}")
    
    @staticmethod
    def token_exists(
        db: Session,
        user_id: int,
        provider: str = "google"
    ) -> bool:
        """
        Check if valid token exists for user
        
        Args:
            db: Database session
            user_id: User ID
            provider: Provider name
            
        Returns:
            True if token exists, False otherwise
        """
        try:
            oauth_token = OAuthTokenService.get_token(db, user_id, provider)
            return oauth_token is not None
        except:
            return False
    
    @staticmethod
    def delete_token(
        db: Session,
        user_id: int,
        provider: str = "google"
    ) -> bool:
        """
        Delete token for user (logout)
        
        Args:
            db: Database session
            user_id: User ID
            provider: Provider name
            
        Returns:
            True if successful, False if token not found
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            connected_account = db.query(ConnectedAccount).filter(
                ConnectedAccount.user_id == user_id,
                ConnectedAccount.provider == provider
            ).first()
            
            if not connected_account:
                return False
            
            db.query(OAuthToken).filter(
                OAuthToken.connected_account_id == connected_account.connected_account_id
            ).delete()
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to delete token: {str(e)}")

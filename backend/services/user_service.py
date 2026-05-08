"""User Management Service"""
from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserResponse
from typing import Optional, List
from exceptions import UserNotFoundError, DuplicateResourceError, DatabaseError


class UserService:
    """Service for managing users"""
    
    @staticmethod
    def get_user(db: Session, email: str) -> Optional[User]:
        """
        Get user by email
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User if found, None otherwise
        """
        try:
            return db.query(User).filter(User.email == email).first()
        except Exception as e:
            raise DatabaseError(f"Failed to get user: {str(e)}")
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            UserNotFoundError: If user not found
        """
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserNotFoundError(user_id=user_id)
            return user
        except UserNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to get user by ID: {str(e)}")
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User:
        """
        Get user by email (strict - raises error if not found)
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User object
            
        Raises:
            UserNotFoundError: If user not found
        """
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise UserNotFoundError(user_id=0, identifier=email)
            return user
        except UserNotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to get user by email: {str(e)}")
    
    @staticmethod
    def create_user(db: Session, email: str, name: str) -> User:
        """
        Create new user
        
        Args:
            db: Database session
            email: User email
            name: User name
            
        Returns:
            Created User
            
        Raises:
            DuplicateResourceError: If user already exists
            DatabaseError: If database operation fails
        """
        try:
            # Check if user already exists
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                raise DuplicateResourceError("User", email)
            
            user = User(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        except DuplicateResourceError:
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to create user: {str(e)}")
    
    @staticmethod
    def update_user(db: Session, user_id: int, name: Optional[str] = None) -> User:
        """
        Update user information
        
        Args:
            db: Database session
            user_id: User ID
            name: New name (optional)
            
        Returns:
            Updated User
            
        Raises:
            UserNotFoundError: If user not found
            DatabaseError: If database operation fails
        """
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserNotFoundError(user_id=user_id)
            
            if name:
                user.name = name
            
            db.commit()
            db.refresh(user)
            return user
            
        except UserNotFoundError:
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to update user: {str(e)}")
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """
        Delete user by ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if successful
            
        Raises:
            UserNotFoundError: If user not found
            DatabaseError: If database operation fails
        """
        try:
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise UserNotFoundError(user_id=user_id)
            
            db.delete(user)
            db.commit()
            return True
            
        except UserNotFoundError:
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseError(f"Failed to delete user: {str(e)}")
    
    @staticmethod
    def list_users(db: Session, limit: int = 100, offset: int = 0) -> List[User]:
        """
        List all users with pagination
        
        Args:
            db: Database session
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of User objects
            
        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return db.query(User).limit(limit).offset(offset).all()
        except Exception as e:
            raise DatabaseError(f"Failed to list users: {str(e)}")

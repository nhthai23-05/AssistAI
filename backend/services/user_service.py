"""User Management Service"""
from sqlalchemy.orm import Session
from models.user import User
from typing import Optional, Tuple


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
        return db.query(User).filter(User.email == email).first()
    
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
        """
        user = User(email=email, name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.user_id == user_id).first()

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.models.base import Base, TimestampMixin
import enum


class User(TimestampMixin, Base):
    """User model"""
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Relationships
    calendars = relationship("Calendar", back_populates="user", cascade="all, delete-orphan")
    connected_accounts = relationship("ConnectedAccount", back_populates="user", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", foreign_keys="Workspace.owner_user_id", back_populates="owner", cascade="all, delete-orphan")
    assistant_sessions = relationship("AssistantSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email}, name={self.name})>"

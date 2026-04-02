from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.models.base import Base, TimestampMixin
import enum


class SessionStatus(str, enum.Enum):
    """Session status enum"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssistantSession(TimestampMixin, Base):
    """Assistant session model - represents a conversation session"""
    __tablename__ = "assistant_session"

    session_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspace.workspace_id"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    
    # Relationships
    user = relationship("User", back_populates="assistant_sessions")
    workspace = relationship("Workspace", back_populates="assistant_sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    tool_calls = relationship("ToolCall", back_populates="session", cascade="all, delete-orphan")
    town_usages = relationship("TownUsage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AssistantSession(id={self.session_id}, user_id={self.user_id}, workspace_id={self.workspace_id})>"

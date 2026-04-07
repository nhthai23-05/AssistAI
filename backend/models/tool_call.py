from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from models.base import Base, TimestampMixin
import enum


class ToolCallStatus(str, enum.Enum):
    """Tool call status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolCall(TimestampMixin, Base):
    """Tool call model - represents a function call made by the assistant"""
    __tablename__ = "tool_call"

    tool_call_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assistant_session.session_id"), nullable=False, index=True)
    tool_name = Column(String(255), nullable=False)
    arguments = Column(JSON, nullable=True)
    status = Column(Enum(ToolCallStatus), default=ToolCallStatus.PENDING)
    
    # Relationships
    session = relationship("AssistantSession", back_populates="tool_calls")
    tool_results = relationship("ToolResult", back_populates="tool_call", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ToolCall(id={self.tool_call_id}, session_id={self.session_id}, tool={self.tool_name})>"

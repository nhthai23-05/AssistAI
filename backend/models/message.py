from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin
import enum


class MessageRole(str, enum.Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(TimestampMixin, Base):
    """Message model - represents a message in a session"""
    __tablename__ = "message"

    message_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assistant_session.session_id"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Relationships
    session = relationship("AssistantSession", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.message_id}, session_id={self.session_id}, role={self.role})>"

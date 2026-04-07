from sqlalchemy import Column, Integer, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from models.base import Base, TimestampMixin


class ToolResult(TimestampMixin, Base):
    """Tool result model - represents the result of a tool call"""
    __tablename__ = "tool_result"

    tool_result_id = Column(Integer, primary_key=True, index=True)
    tool_call_id = Column(Integer, ForeignKey("tool_call.tool_call_id"), nullable=False, index=True)
    success = Column(Boolean, default=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    tool_call = relationship("ToolCall", back_populates="tool_results")

    def __repr__(self):
        return f"<ToolResult(id={self.tool_result_id}, tool_call_id={self.tool_call_id}, success={self.success})>"

from sqlalchemy import Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from models.base import Base, TimestampMixin


class TokenUsage(TimestampMixin, Base):
    """Token usage model - tracks API token/resource usage"""
    __tablename__ = "token_usage"

    usage_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assistant_session.session_id"), nullable=False, index=True)
    usage_type = Column(String(100), nullable=False)  # e.g., "api_calls", "tokens", "storage"
    amount = Column(Integer, nullable=False)
    meta_data = Column(Text, nullable=True)
    
    # Relationships
    session = relationship("AssistantSession", back_populates="token_usages")

    def __repr__(self):
        return f"<TokenUsage(id={self.usage_id}, session_id={self.session_id}, type={self.usage_type})>"

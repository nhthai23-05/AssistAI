from sqlalchemy import Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin


class TownUsage(TimestampMixin, Base):
    """Town usage model - tracks API/resource usage"""
    __tablename__ = "town_usage"

    usage_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("assistant_session.session_id"), nullable=False, index=True)
    usage_type = Column(String(100), nullable=False)  # e.g., "api_calls", "tokens", "storage"
    amount = Column(Integer, nullable=False)
    metadata = Column(Text, nullable=True)
    
    # Relationships
    session = relationship("AssistantSession", back_populates="town_usages")

    def __repr__(self):
        return f"<TownUsage(id={self.usage_id}, session_id={self.session_id}, type={self.usage_type})>"

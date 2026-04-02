from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin


class Integration(TimestampMixin, Base):
    """Integration model - represents external service integrations"""
    __tablename__ = "integration"

    integration_id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspace.workspace_id"), nullable=False, index=True)
    service_name = Column(String(100), nullable=False)  # e.g., "gmail", "calendar", "sheets"
    service_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="integrations")

    def __repr__(self):
        return f"<Integration(id={self.integration_id}, workspace_id={self.workspace_id}, service={self.service_name})>"

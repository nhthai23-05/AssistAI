from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin


class Calendar(TimestampMixin, Base):
    """Calendar model - represents a calendar from connected account"""
    __tablename__ = "calendar"

    calendar_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    calendar_name = Column(String(255), nullable=False)
    calendar_provider_id = Column(String(255), nullable=True)  # e.g., Google Calendar ID
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="calendars")

    def __repr__(self):
        return f"<Calendar(id={self.calendar_id}, user_id={self.user_id}, name={self.calendar_name})>"

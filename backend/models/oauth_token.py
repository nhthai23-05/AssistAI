from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.models.base import Base, TimestampMixin


class OAuthToken(TimestampMixin, Base):
    """OAuth token storage"""
    __tablename__ = "oauth_token"

    oauth_token_id = Column(Integer, primary_key=True, index=True)
    connected_account_id = Column(Integer, ForeignKey("connected_account.connected_account_id"), nullable=False, index=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(50), default="Bearer")
    expires_at = Column(DateTime, nullable=True)
    scope = Column(Text, nullable=True)
    
    # Relationships
    connected_account = relationship("ConnectedAccount", back_populates="oauth_tokens")

    def __repr__(self):
        return f"<OAuthToken(id={self.oauth_token_id}, account_id={self.connected_account_id})>"

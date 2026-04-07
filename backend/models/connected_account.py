from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import Base, TimestampMixin


class ConnectedAccount(TimestampMixin, Base):
    """Connected account for OAuth/integrations"""
    __tablename__ = "connected_account"

    connected_account_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    provider = Column(String(100), nullable=False)  # e.g., "google", "outlook"
    account_email = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="connected_accounts")
    oauth_tokens = relationship("OAuthToken", back_populates="connected_account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ConnectedAccount(id={self.connected_account_id}, user_id={self.user_id}, provider={self.provider})>"

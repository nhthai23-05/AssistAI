from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from models.base import Base, TimestampMixin
import enum


class WorkspaceStatus(str, enum.Enum):
    """Workspace status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Workspace(TimestampMixin, Base):
    """Workspace model - represents a collaborative space"""
    __tablename__ = "workspace"

    workspace_id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(WorkspaceStatus), default=WorkspaceStatus.ACTIVE)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_user_id], back_populates="workspaces")
    sheets = relationship("Sheet", back_populates="workspace", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="workspace", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="workspace", cascade="all, delete-orphan")
    assistant_sessions = relationship("AssistantSession", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Workspace(id={self.workspace_id}, name={self.name}, owner_id={self.owner_user_id})>"

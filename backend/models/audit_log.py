from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin
import enum


class AuditAction(str, enum.Enum):
    """Audit action enum"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"
    EXECUTE = "execute"


class AuditLog(TimestampMixin, Base):
    """Audit log model - tracks all actions in workspace"""
    __tablename__ = "audit_log"

    audit_id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspace.workspace_id"), nullable=False, index=True)
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.audit_id}, workspace_id={self.workspace_id}, action={self.action})>"

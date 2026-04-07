from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base, TimestampMixin


class Sheet(TimestampMixin, Base):
    """Sheet model - represents a spreadsheet/sheet in workspace"""
    __tablename__ = "sheet"

    sheet_id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspace.workspace_id"), nullable=False, index=True)
    sheet_name = Column(String(255), nullable=False)
    sheet_provider_id = Column(String(255), nullable=True)  # e.g., Google Sheets ID
    
    # Relationships
    workspace = relationship("Workspace", back_populates="sheets")

    def __repr__(self):
        return f"<Sheet(id={self.sheet_id}, workspace_id={self.workspace_id}, name={self.sheet_name})>"

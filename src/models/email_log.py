"""Email log model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base


class EmailLog(Base):
    """Email log model for tracking parsed emails."""
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=True)
    email_subject = Column(String(500))
    email_body = Column(Text)
    sender = Column(String(255), index=True)
    received_date = Column(DateTime(timezone=True))
    parsed_status = Column(String(50))  # active, interested, closed
    action_required = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    application = relationship("Application", back_populates="email_logs")

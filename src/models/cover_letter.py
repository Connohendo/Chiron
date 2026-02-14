"""Cover letter model."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base


class CoverLetter(Base):
    """Cover letter model."""
    __tablename__ = "cover_letters"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    content = Column(Text, nullable=False)
    generated_date = Column(DateTime(timezone=True), server_default=func.now())
    version = Column(Integer, default=1)
    
    # Relationships
    application = relationship("Application", back_populates="cover_letters")

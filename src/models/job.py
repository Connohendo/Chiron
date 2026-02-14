"""Job model."""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base


class Job(Base):
    """Job posting model."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    location = Column(String(255), index=True)
    salary_range = Column(String(100))  # e.g., "$50,000 - $70,000"
    job_url = Column(String(500), unique=True)
    source = Column(String(50))  # API name: "indeed", "linkedin", "adzuna"
    posted_date = Column(Date)
    requirements = Column(JSON, default=dict)  # Extracted requirements
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    applications = relationship("Application", back_populates="job")

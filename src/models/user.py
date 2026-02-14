"""User and UserProfile models."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.connection import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    applications = relationship("Application", back_populates="user")


class UserProfile(Base):
    """User profile model with detailed information."""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    skills = Column(JSON, default=list)  # List of skills
    experience_level = Column(String(50))  # e.g., "entry", "mid", "senior", "executive"
    education = Column(JSON, default=list)  # List of education entries
    work_history = Column(JSON, default=list)  # List of work experience entries
    certifications = Column(JSON, default=list)  # List of certifications
    location = Column(String(255))  # User's location
    preferences = Column(JSON, default=dict)  # Job preferences (remote, salary, etc.)
    resume_text = Column(Text)  # Extracted text from resume
    
    # Relationships
    user = relationship("User", back_populates="profile")

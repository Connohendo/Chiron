"""User profile API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr
from src.database.connection import get_db
from src.models.user import User, UserProfile
from src.services.resume_parser import ResumeParser

router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    name: str


class UserProfileUpdate(BaseModel):
    """User profile update model."""
    skills: Optional[list] = None
    experience_level: Optional[str] = None
    education: Optional[list] = None
    work_history: Optional[list] = None
    certifications: Optional[list] = None
    location: Optional[str] = None
    preferences: Optional[dict] = None


class UserProfileResponse(BaseModel):
    """User profile response model."""
    id: int
    user_id: int
    skills: list
    experience_level: Optional[str]
    education: list
    work_history: list
    certifications: list
    location: Optional[str]
    preferences: dict
    
    class Config:
        from_attributes = True


@router.post("/", response_model=dict)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user
    user = User(email=user_data.email, name=user_data.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create empty profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    
    return {"id": user.id, "email": user.email, "name": user.name}


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get user profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    return profile


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: int,
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update user profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Update fields
    if profile_data.skills is not None:
        profile.skills = profile_data.skills
    if profile_data.experience_level is not None:
        profile.experience_level = profile_data.experience_level
    if profile_data.education is not None:
        profile.education = profile_data.education
    if profile_data.work_history is not None:
        profile.work_history = profile_data.work_history
    if profile_data.certifications is not None:
        profile.certifications = profile_data.certifications
    if profile_data.location is not None:
        profile.location = profile_data.location
    if profile_data.preferences is not None:
        profile.preferences = profile_data.preferences
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.post("/profile/upload-resume")
async def upload_resume(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and parse resume."""
    # Check if profile exists
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Read file content
    file_content = await file.read()
    
    # Parse resume
    try:
        parser = ResumeParser()
        parsed_data = parser.parse_resume(file_content, file.filename)
        
        # Update profile with parsed data
        profile.resume_text = parsed_data.get("resume_text", "")
        if parsed_data.get("skills"):
            profile.skills = parsed_data["skills"]
        if parsed_data.get("experience_level"):
            profile.experience_level = parsed_data["experience_level"]
        if parsed_data.get("work_history"):
            profile.work_history = parsed_data["work_history"]
        if parsed_data.get("education"):
            profile.education = parsed_data["education"]
        if parsed_data.get("certifications"):
            profile.certifications = parsed_data["certifications"]
        
        db.commit()
        db.refresh(profile)
        
        return {
            "message": "Resume parsed successfully",
            "profile": UserProfileResponse.model_validate(profile)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing resume: {str(e)}")

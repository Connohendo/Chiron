"""Cover letter API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from src.database.connection import get_db
from src.models.cover_letter import CoverLetter
from src.models.application import Application
from src.models.job import Job
from src.models.user import UserProfile
from src.services.cover_letter_gen import CoverLetterGenerator

router = APIRouter(prefix="/api/cover-letters", tags=["cover-letters"])


class CoverLetterGenerateRequest(BaseModel):
    """Cover letter generation request."""
    application_id: int
    tone: str = "professional"  # professional, friendly, enthusiastic, confident
    length: str = "medium"  # short, medium, long


class CoverLetterUpdateRequest(BaseModel):
    """Cover letter update request."""
    content: str


class CoverLetterResponse(BaseModel):
    """Cover letter response model."""
    id: int
    application_id: int
    content: str
    generated_date: str
    version: int
    
    class Config:
        from_attributes = True


@router.post("/generate", response_model=CoverLetterResponse)
async def generate_cover_letter(
    request: CoverLetterGenerateRequest,
    db: Session = Depends(get_db)
):
    """Generate a cover letter for an application."""
    # Get application
    application = db.query(Application).filter(Application.id == request.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get job
    if not application.job_id:
        raise HTTPException(status_code=400, detail="Application does not have an associated job")
    
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == application.user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Generate cover letter
    try:
        generator = CoverLetterGenerator()
        cover_letter_content = generator.generate_cover_letter(
            profile=profile,
            job=job,
            tone=request.tone,
            length=request.length
        )
        
        # Get latest version number
        latest_cover_letter = db.query(CoverLetter).filter(
            CoverLetter.application_id == request.application_id
        ).order_by(CoverLetter.version.desc()).first()
        
        version = (latest_cover_letter.version + 1) if latest_cover_letter else 1
        
        # Save cover letter
        cover_letter = CoverLetter(
            application_id=request.application_id,
            content=cover_letter_content,
            version=version
        )
        
        db.add(cover_letter)
        db.commit()
        db.refresh(cover_letter)
        
        return CoverLetterResponse(
            id=cover_letter.id,
            application_id=cover_letter.application_id,
            content=cover_letter.content,
            generated_date=cover_letter.generated_date.isoformat() if cover_letter.generated_date else "",
            version=cover_letter.version
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating cover letter: {str(e)}")


@router.get("/{application_id}", response_model=List[CoverLetterResponse])
async def get_cover_letters(
    application_id: int,
    db: Session = Depends(get_db)
):
    """Get all cover letters for an application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    cover_letters = db.query(CoverLetter).filter(
        CoverLetter.application_id == application_id
    ).order_by(CoverLetter.version.desc()).all()
    
    return [
        CoverLetterResponse(
            id=cl.id,
            application_id=cl.application_id,
            content=cl.content,
            generated_date=cl.generated_date.isoformat() if cl.generated_date else "",
            version=cl.version
        )
        for cl in cover_letters
    ]


@router.put("/{cover_letter_id}", response_model=CoverLetterResponse)
async def update_cover_letter(
    cover_letter_id: int,
    request: CoverLetterUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update/edit a cover letter."""
    cover_letter = db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()
    if not cover_letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    
    cover_letter.content = request.content
    db.commit()
    db.refresh(cover_letter)
    
    return CoverLetterResponse(
        id=cover_letter.id,
        application_id=cover_letter.application_id,
        content=cover_letter.content,
        generated_date=cover_letter.generated_date.isoformat() if cover_letter.generated_date else "",
        version=cover_letter.version
    )


@router.post("/{cover_letter_id}/improve", response_model=CoverLetterResponse)
async def improve_cover_letter(
    cover_letter_id: int,
    feedback: str = Query(..., description="Feedback for improvement"),
    db: Session = Depends(get_db)
):
    """Improve a cover letter based on feedback."""
    cover_letter = db.query(CoverLetter).filter(CoverLetter.id == cover_letter_id).first()
    if not cover_letter:
        raise HTTPException(status_code=404, detail="Cover letter not found")
    
    try:
        generator = CoverLetterGenerator()
        improved_content = generator.improve_cover_letter(cover_letter.content, feedback)
        
        # Create new version
        new_version = CoverLetter(
            application_id=cover_letter.application_id,
            content=improved_content,
            version=cover_letter.version + 1
        )
        
        db.add(new_version)
        db.commit()
        db.refresh(new_version)
        
        return CoverLetterResponse(
            id=new_version.id,
            application_id=new_version.application_id,
            content=new_version.content,
            generated_date=new_version.generated_date.isoformat() if new_version.generated_date else "",
            version=new_version.version
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error improving cover letter: {str(e)}")

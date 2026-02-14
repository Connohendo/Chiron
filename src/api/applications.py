"""Application tracking API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime
from src.database.connection import get_db
from src.models.application import Application
from src.models.job import Job
from src.models.user import User

router = APIRouter(prefix="/api/applications", tags=["applications"])


class ApplicationCreate(BaseModel):
    """Application creation model."""
    user_id: int
    job_id: Optional[int] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    status: str = "active"
    applied_date: Optional[str] = None
    notes: Optional[str] = None
    manual_entry: bool = True


class ApplicationUpdate(BaseModel):
    """Application update model."""
    status: Optional[str] = None
    applied_date: Optional[str] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    """Application response model."""
    id: int
    user_id: int
    job_id: Optional[int]
    status: str
    applied_date: Optional[str]
    notes: Optional[str]
    manual_entry: bool
    created_at: str
    updated_at: Optional[str]
    job: Optional[dict] = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[ApplicationResponse])
async def get_applications(
    user_id: int = Query(..., description="User ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Get all applications for a user, optionally filtered by status."""
    query = db.query(Application).filter(Application.user_id == user_id)
    
    if status:
        query = query.filter(Application.status == status)
    
    applications = query.order_by(Application.created_at.desc()).all()
    
    result = []
    for app in applications:
        app_dict = {
            "id": app.id,
            "user_id": app.user_id,
            "job_id": app.job_id,
            "status": app.status,
            "applied_date": str(app.applied_date) if app.applied_date else None,
            "notes": app.notes,
            "manual_entry": app.manual_entry,
            "created_at": app.created_at.isoformat() if app.created_at else "",
            "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        }
        
        # Include job details if available
        if app.job_id:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                app_dict["job"] = {
                    "id": job.id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "job_url": job.job_url
                }
        
        result.append(ApplicationResponse(**app_dict))
    
    return result


@router.post("/", response_model=ApplicationResponse)
async def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db)
):
    """Create a new application entry."""
    # Validate user exists
    user = db.query(User).filter(User.id == application_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If job_id is provided, validate it exists
    if application_data.job_id:
        job = db.query(Job).filter(Job.id == application_data.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
    
    # Parse applied_date
    applied_date = None
    if application_data.applied_date:
        try:
            applied_date = datetime.fromisoformat(application_data.applied_date).date()
        except:
            try:
                applied_date = datetime.strptime(application_data.applied_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Validate status
    valid_statuses = ["active", "interested", "closed"]
    if application_data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")
    
    # Create application
    application = Application(
        user_id=application_data.user_id,
        job_id=application_data.job_id,
        status=application_data.status,
        applied_date=applied_date,
        notes=application_data.notes,
        manual_entry=application_data.manual_entry
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    
    # Build response
    app_dict = {
        "id": application.id,
        "user_id": application.user_id,
        "job_id": application.job_id,
        "status": application.status,
        "applied_date": str(application.applied_date) if application.applied_date else None,
        "notes": application.notes,
        "manual_entry": application.manual_entry,
        "created_at": application.created_at.isoformat() if application.created_at else "",
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }
    
    if application.job_id:
        job = db.query(Job).filter(Job.id == application.job_id).first()
        if job:
            app_dict["job"] = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url
            }
    
    return ApplicationResponse(**app_dict)


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    application_data: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    """Update an application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update fields
    if application_data.status is not None:
        valid_statuses = ["active", "interested", "closed"]
        if application_data.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")
        application.status = application_data.status
    
    if application_data.applied_date is not None:
        try:
            application.applied_date = datetime.fromisoformat(application_data.applied_date).date()
        except:
            try:
                application.applied_date = datetime.strptime(application_data.applied_date, "%Y-%m-%d").date()
            except:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if application_data.notes is not None:
        application.notes = application_data.notes
    
    db.commit()
    db.refresh(application)
    
    # Build response
    app_dict = {
        "id": application.id,
        "user_id": application.user_id,
        "job_id": application.job_id,
        "status": application.status,
        "applied_date": str(application.applied_date) if application.applied_date else None,
        "notes": application.notes,
        "manual_entry": application.manual_entry,
        "created_at": application.created_at.isoformat() if application.created_at else "",
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }
    
    if application.job_id:
        job = db.query(Job).filter(Job.id == application.job_id).first()
        if job:
            app_dict["job"] = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url
            }
    
    return ApplicationResponse(**app_dict)


@router.put("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    status: str = Query(..., description="New status"),
    db: Session = Depends(get_db)
):
    """Update application status."""
    valid_statuses = ["active", "interested", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")
    
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = status
    db.commit()
    db.refresh(application)
    
    # Build response
    app_dict = {
        "id": application.id,
        "user_id": application.user_id,
        "job_id": application.job_id,
        "status": application.status,
        "applied_date": str(application.applied_date) if application.applied_date else None,
        "notes": application.notes,
        "manual_entry": application.manual_entry,
        "created_at": application.created_at.isoformat() if application.created_at else "",
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
    }
    
    if application.job_id:
        job = db.query(Job).filter(Job.id == application.job_id).first()
        if job:
            app_dict["job"] = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url
            }
    
    return ApplicationResponse(**app_dict)


@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """Delete an application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(application)
    db.commit()
    
    return {"message": "Application deleted successfully"}

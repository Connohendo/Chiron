"""Email sync API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from src.database.connection import get_db
from src.models.email_log import EmailLog
from src.models.application import Application
from src.models.job import Job
from src.services.email_parser import GmailService, EmailParser
from src.config import settings
import json

router = APIRouter(prefix="/api/emails", tags=["emails"])


class EmailLogResponse(BaseModel):
    """Email log response model."""
    id: int
    application_id: Optional[int]
    email_subject: Optional[str]
    email_body: Optional[str]
    sender: Optional[str]
    received_date: Optional[str]
    parsed_status: Optional[str]
    action_required: bool
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/connect")
async def get_authorization_url():
    """Get Gmail OAuth authorization URL."""
    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise HTTPException(status_code=500, detail="Gmail API credentials not configured")
    
    gmail_service = GmailService()
    auth_url = gmail_service.get_authorization_url()
    
    return {"authorization_url": auth_url}


@router.post("/oauth/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Gmail"),
    db: Session = Depends(get_db)
):
    """Handle OAuth callback and store credentials."""
    try:
        gmail_service = GmailService()
        credentials = gmail_service.authenticate(code)
        
        # Store credentials (in production, store securely per user)
        # For now, return success
        return {
            "message": "Gmail account connected successfully",
            "token": credentials.token if credentials.token else "stored"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error authenticating: {str(e)}")


@router.post("/sync")
async def sync_emails(
    user_id: int = Query(..., description="User ID"),
    credentials_token: Optional[str] = Query(None, description="Gmail access token"),
    db: Session = Depends(get_db)
):
    """Sync emails from Gmail and update application statuses."""
    try:
        gmail_service = GmailService()
        
        # In production, retrieve stored credentials for user
        # For now, using provided token or requiring re-authentication
        if not credentials_token:
            raise HTTPException(status_code=400, detail="Gmail credentials required. Please connect your account first.")
        
        # Get job-related emails
        emails = gmail_service.get_job_related_emails(max_results=50)
        
        synced_count = 0
        updated_applications = []
        
        for email_data in emails:
            # Check if email already logged
            existing_log = db.query(EmailLog).filter(
                EmailLog.email_subject == email_data.get('subject'),
                EmailLog.sender == email_data.get('sender')
            ).first()
            
            if existing_log:
                continue
            
            # Parse email status
            parsed = EmailParser.parse_email_status(
                email_data.get('subject', ''),
                email_data.get('body', '')
            )
            
            # Try to match with existing application
            application_id = None
            if parsed.get('company'):
                # Try to find application by company name
                applications = db.query(Application).filter(
                    Application.user_id == user_id
                ).all()
                
                for app in applications:
                    if app.job_id:
                        job = db.query(Job).filter(Job.id == app.job_id).first()
                        if job and parsed['company'].lower() in job.company.lower():
                            application_id = app.id
                            
                            # Update application status if parsed status is different
                            if parsed.get('status') and app.status != parsed['status']:
                                app.status = parsed['status']
                                updated_applications.append(app.id)
                            break
            
            # Create email log
            email_log = EmailLog(
                application_id=application_id,
                email_subject=email_data.get('subject'),
                email_body=email_data.get('body', '')[:5000],  # Limit length
                sender=email_data.get('sender'),
                received_date=email_data.get('received_date'),
                parsed_status=parsed.get('status'),
                action_required=parsed.get('action_required', False)
            )
            
            db.add(email_log)
            synced_count += 1
        
        db.commit()
        
        return {
            "message": f"Synced {synced_count} emails",
            "updated_applications": updated_applications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing emails: {str(e)}")


@router.get("/logs", response_model=List[EmailLogResponse])
async def get_email_logs(
    user_id: int = Query(..., description="User ID"),
    application_id: Optional[int] = Query(None, description="Filter by application ID"),
    db: Session = Depends(get_db)
):
    """Get email logs for a user."""
    query = db.query(EmailLog)
    
    # Filter by user's applications
    if application_id:
        query = query.filter(EmailLog.application_id == application_id)
    else:
        # Get all applications for user
        user_applications = db.query(Application).filter(Application.user_id == user_id).all()
        app_ids = [app.id for app in user_applications]
        if app_ids:
            query = query.filter(EmailLog.application_id.in_(app_ids))
        else:
            return []
    
    email_logs = query.order_by(EmailLog.received_date.desc()).all()
    
    return [
        EmailLogResponse(
            id=log.id,
            application_id=log.application_id,
            email_subject=log.email_subject,
            email_body=log.email_body,
            sender=log.sender,
            received_date=log.received_date.isoformat() if log.received_date else None,
            parsed_status=log.parsed_status,
            action_required=log.action_required,
            created_at=log.created_at.isoformat() if log.created_at else ""
        )
        for log in email_logs
    ]

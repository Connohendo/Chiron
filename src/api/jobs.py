"""Jobs API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from src.database.connection import get_db
from src.models.job import Job
from src.services.job_suggestions import JobMatcher
from src.services.job_fetcher import JobFetcher

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobResponse(BaseModel):
    """Job response model."""
    id: int
    title: str
    company: str
    description: Optional[str]
    location: Optional[str]
    salary_range: Optional[str]
    job_url: Optional[str]
    source: Optional[str]
    posted_date: Optional[str]
    requirements: dict
    match_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class JobSearchRequest(BaseModel):
    """Job search request model."""
    query: str
    location: Optional[str] = None
    sources: Optional[List[str]] = None
    limit: int = 50


@router.get("/suggestions", response_model=List[JobResponse])
async def get_job_suggestions(
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get personalized job suggestions for a user."""
    try:
        jobs = JobMatcher.get_suggested_jobs(user_id, db, limit=limit)
        
        # Convert to response format
        job_responses = []
        for job in jobs:
            # Check if job exists in DB
            db_job = db.query(Job).filter(Job.job_url == job.get("job_url")).first()
            
            if db_job:
                job_dict = {
                    "id": db_job.id,
                    "title": db_job.title,
                    "company": db_job.company,
                    "description": db_job.description,
                    "location": db_job.location,
                    "salary_range": db_job.salary_range,
                    "job_url": db_job.job_url,
                    "source": db_job.source,
                    "posted_date": str(db_job.posted_date) if db_job.posted_date else None,
                    "requirements": db_job.requirements or {},
                    "match_score": job.get("match_score")
                }
            else:
                # Save new job to DB
                saved_jobs = JobMatcher.save_jobs_to_db([job], db)
                if saved_jobs:
                    db_job = saved_jobs[0]
                    job_dict = {
                        "id": db_job.id,
                        "title": db_job.title,
                        "company": db_job.company,
                        "description": db_job.description,
                        "location": db_job.location,
                        "salary_range": db_job.salary_range,
                        "job_url": db_job.job_url,
                        "source": db_job.source,
                        "posted_date": str(db_job.posted_date) if db_job.posted_date else None,
                        "requirements": db_job.requirements or {},
                        "match_score": job.get("match_score")
                    }
                else:
                    continue
            
            job_responses.append(JobResponse(**job_dict))
        
        return job_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job suggestions: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get job details by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        id=job.id,
        title=job.title,
        company=job.company,
        description=job.description,
        location=job.location,
        salary_range=job.salary_range,
        job_url=job.job_url,
        source=job.source,
        posted_date=str(job.posted_date) if job.posted_date else None,
        requirements=job.requirements or {}
    )


@router.post("/search", response_model=List[JobResponse])
async def search_jobs(
    search_request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """Manual job search."""
    try:
        job_fetcher = JobFetcher()
        jobs = job_fetcher.fetch_jobs(
            query=search_request.query,
            location=search_request.location,
            sources=search_request.sources,
            limit=search_request.limit
        )
        
        # Save jobs to database
        saved_jobs = JobMatcher.save_jobs_to_db(jobs, db)
        
        # Convert to response format
        job_responses = []
        for job in saved_jobs:
            job_responses.append(JobResponse(
                id=job.id,
                title=job.title,
                company=job.company,
                description=job.description,
                location=job.location,
                salary_range=job.salary_range,
                job_url=job.job_url,
                source=job.source,
                posted_date=str(job.posted_date) if job.posted_date else None,
                requirements=job.requirements or {}
            ))
        
        return job_responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

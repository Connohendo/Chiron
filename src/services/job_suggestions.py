"""Job matching and suggestion service."""
from typing import List, Dict
from sqlalchemy.orm import Session
from src.models.user import UserProfile
from src.models.job import Job
from src.services.job_fetcher import JobFetcher
from datetime import datetime, timedelta


class JobMatcher:
    """Match jobs to user profiles and provide suggestions."""
    
    @staticmethod
    def calculate_match_score(job: Dict, profile: UserProfile) -> float:
        """Calculate match score between a job and user profile (0-100)."""
        score = 0.0
        max_score = 100.0
        
        # Skills matching (40 points)
        user_skills = [skill.lower() for skill in (profile.skills or [])]
        job_description = (job.get("description", "") or "").lower()
        job_title = (job.get("title", "") or "").lower()
        job_text = f"{job_title} {job_description}"
        
        matched_skills = sum(1 for skill in user_skills if skill in job_text)
        if user_skills:
            skills_score = (matched_skills / len(user_skills)) * 40
            score += min(skills_score, 40)
        
        # Experience level matching (20 points)
        if profile.experience_level and job.get("requirements"):
            exp_keywords = {
                "entry": ["entry", "junior", "intern", "graduate", "associate"],
                "mid": ["mid", "intermediate", "2-5 years", "3+ years"],
                "senior": ["senior", "lead", "principal", "5+ years", "7+ years"],
                "executive": ["executive", "director", "vp", "c-level", "10+ years"]
            }
            
            job_text_lower = job_text.lower()
            user_exp = profile.experience_level.lower()
            
            if user_exp in exp_keywords:
                for keyword in exp_keywords[user_exp]:
                    if keyword in job_text_lower:
                        score += 20
                        break
        
        # Location matching (20 points)
        if profile.location and job.get("location"):
            user_location = profile.location.lower()
            job_location = job.get("location", "").lower()
            
            # Exact match
            if user_location in job_location or job_location in user_location:
                score += 20
            # Remote work
            elif "remote" in job_location:
                if profile.preferences and profile.preferences.get("remote", False):
                    score += 20
                else:
                    score += 10  # Partial credit for remote
            # Same state/city
            elif any(word in job_location for word in user_location.split(",")[0].split()):
                score += 10
        
        # Education matching (10 points)
        if profile.education and job.get("requirements"):
            # Simple check for degree requirements
            job_text_lower = job_text.lower()
            education_keywords = ["bachelor", "master", "phd", "degree", "bs", "ms", "ba", "ma"]
            if any(keyword in job_text_lower for keyword in education_keywords):
                if profile.education:
                    score += 10
        
        # Salary preferences (10 points)
        if profile.preferences and profile.preferences.get("min_salary"):
            min_salary = profile.preferences.get("min_salary", 0)
            salary_range = job.get("salary_range", "")
            if salary_range:
                # Extract numbers from salary range
                import re
                numbers = re.findall(r'\d+', salary_range.replace(",", ""))
                if numbers:
                    job_min_salary = int(numbers[0]) * 1000  # Assume format like "50,000"
                    if job_min_salary >= min_salary:
                        score += 10
        
        return min(score, max_score)
    
    @classmethod
    def get_suggested_jobs(cls, user_id: int, db: Session, limit: int = 20) -> List[Dict]:
        """Get job suggestions for a user."""
        # Get user profile
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return []
        
        # Build search query from profile
        query_parts = []
        if profile.skills:
            query_parts.extend(profile.skills[:3])  # Top 3 skills
        if profile.experience_level:
            query_parts.append(profile.experience_level)
        
        query = " ".join(query_parts) if query_parts else "software engineer"
        location = profile.location
        
        # Fetch jobs from APIs
        job_fetcher = JobFetcher()
        jobs = job_fetcher.fetch_jobs(query, location, limit=limit * 2)  # Fetch more to filter
        
        # Calculate match scores
        scored_jobs = []
        for job in jobs:
            score = cls.calculate_match_score(job, profile)
            job["match_score"] = score
            scored_jobs.append(job)
        
        # Sort by match score and return top results
        scored_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        
        return scored_jobs[:limit]
    
    @classmethod
    def save_jobs_to_db(cls, jobs: List[Dict], db: Session) -> List[Job]:
        """Save fetched jobs to database, avoiding duplicates."""
        saved_jobs = []
        
        for job_data in jobs:
            # Check if job already exists
            existing_job = db.query(Job).filter(Job.job_url == job_data.get("job_url")).first()
            
            if existing_job:
                saved_jobs.append(existing_job)
            else:
                # Create new job
                job = Job(
                    title=job_data.get("title", ""),
                    company=job_data.get("company", ""),
                    description=job_data.get("description", ""),
                    location=job_data.get("location", ""),
                    salary_range=job_data.get("salary_range"),
                    job_url=job_data.get("job_url", ""),
                    source=job_data.get("source", ""),
                    posted_date=job_data.get("posted_date"),
                    requirements=job_data.get("requirements", {})
                )
                db.add(job)
                saved_jobs.append(job)
        
        db.commit()
        return saved_jobs

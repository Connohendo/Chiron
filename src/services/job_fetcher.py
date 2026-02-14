"""Job fetching service for various job board APIs."""
import requests
from typing import List, Dict, Optional
from datetime import datetime
from src.config import settings


class JobFetcher:
    """Fetch jobs from various job board APIs."""
    
    @staticmethod
    def fetch_from_adzuna(query: str, location: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Fetch jobs from Adzuna API."""
        if not settings.adzuna_app_id or not settings.adzuna_app_key:
            return []
        
        try:
            url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
            params = {
                "app_id": settings.adzuna_app_id,
                "app_key": settings.adzuna_app_key,
                "results_per_page": limit,
                "what": query,
            }
            if location:
                params["where"] = location
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for result in data.get("results", [])[:limit]:
                job = {
                    "title": result.get("title", ""),
                    "company": result.get("company", {}).get("display_name", "Unknown"),
                    "description": result.get("description", ""),
                    "location": result.get("location", {}).get("display_name", ""),
                    "salary_range": result.get("salary_min") and result.get("salary_max") and 
                                  f"${result['salary_min']:,} - ${result['salary_max']:,}",
                    "job_url": result.get("redirect_url", ""),
                    "source": "adzuna",
                    "posted_date": datetime.fromisoformat(result.get("created", "").replace("Z", "+00:00")).date() if result.get("created") else None,
                    "requirements": {
                        "category": result.get("category", {}).get("label", ""),
                        "contract_type": result.get("contract_type", "")
                    }
                }
                jobs.append(job)
            
            return jobs
        except Exception as e:
            print(f"Error fetching from Adzuna: {str(e)}")
            return []
    
    @staticmethod
    def fetch_from_indeed(query: str, location: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Fetch jobs from Indeed API (using their public RSS/API if available)."""
        # Note: Indeed's official API requires partnership
        # This is a placeholder that could use web scraping or their RSS feed
        if not settings.indeed_api_key:
            return []
        
        try:
            # Indeed API endpoint (if you have access)
            # This is a simplified version - actual implementation would use their API
            url = "https://api.indeed.com/ads/apisearch"
            params = {
                "publisher": settings.indeed_api_key,
                "q": query,
                "l": location or "",
                "limit": limit,
                "format": "json",
                "v": "2"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for result in data.get("results", [])[:limit]:
                job = {
                    "title": result.get("jobtitle", ""),
                    "company": result.get("company", "Unknown"),
                    "description": result.get("snippet", ""),
                    "location": result.get("formattedLocation", ""),
                    "salary_range": result.get("salary", ""),
                    "job_url": result.get("url", ""),
                    "source": "indeed",
                    "posted_date": datetime.fromtimestamp(int(result.get("date", 0))).date() if result.get("date") else None,
                    "requirements": {}
                }
                jobs.append(job)
            
            return jobs
        except Exception as e:
            print(f"Error fetching from Indeed: {str(e)}")
            return []
    
    @staticmethod
    def fetch_from_linkedin(query: str, location: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Fetch jobs from LinkedIn Jobs API."""
        # Note: LinkedIn Jobs API requires partnership/access
        # This is a placeholder structure
        if not settings.linkedin_api_key:
            return []
        
        try:
            # LinkedIn API endpoint (if you have access)
            # This would require OAuth and proper API access
            # For now, return empty list as LinkedIn API access is restricted
            return []
        except Exception as e:
            print(f"Error fetching from LinkedIn: {str(e)}")
            return []
    
    @classmethod
    def fetch_jobs(cls, query: str, location: Optional[str] = None, sources: Optional[List[str]] = None, limit: int = 50) -> List[Dict]:
        """Fetch jobs from multiple sources."""
        if sources is None:
            sources = ["adzuna", "indeed"]
        
        all_jobs = []
        
        if "adzuna" in sources:
            adzuna_jobs = cls.fetch_from_adzuna(query, location, limit)
            all_jobs.extend(adzuna_jobs)
        
        if "indeed" in sources:
            indeed_jobs = cls.fetch_from_indeed(query, location, limit)
            all_jobs.extend(indeed_jobs)
        
        if "linkedin" in sources:
            linkedin_jobs = cls.fetch_from_linkedin(query, location, limit)
            all_jobs.extend(linkedin_jobs)
        
        # Remove duplicates based on job_url
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.get("job_url") and job["job_url"] not in seen_urls:
                seen_urls.add(job["job_url"])
                unique_jobs.append(job)
        
        return unique_jobs[:limit]

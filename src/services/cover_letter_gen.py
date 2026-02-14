"""AI cover letter generation service."""
from typing import Dict, Optional
from openai import OpenAI
from src.config import settings
from src.models.user import UserProfile
from src.models.job import Job


class CoverLetterGenerator:
    """Generate personalized cover letters using AI."""
    
    def __init__(self):
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
    
    def generate_cover_letter(
        self,
        profile: UserProfile,
        job: Job,
        tone: str = "professional",
        length: str = "medium"
    ) -> str:
        """Generate a cover letter for a job application."""
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        # Build prompt
        prompt = self._build_prompt(profile, job, tone, length)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional career coach helping job seekers write compelling cover letters. Write clear, concise, and personalized cover letters that highlight the candidate's relevant skills and experience."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            cover_letter = response.choices[0].message.content.strip()
            return cover_letter
        except Exception as e:
            raise Exception(f"Error generating cover letter: {str(e)}")
    
    def _build_prompt(
        self,
        profile: UserProfile,
        job: Job,
        tone: str,
        length: str
    ) -> str:
        """Build the prompt for cover letter generation."""
        # Extract user information
        skills = ", ".join(profile.skills[:10]) if profile.skills else "Not specified"
        experience_level = profile.experience_level or "Not specified"
        location = profile.location or "Not specified"
        
        # Build work history summary
        work_summary = ""
        if profile.work_history:
            work_summary = "\n".join([
                f"- {exp.get('description', '')[:200]}"
                for exp in profile.work_history[:3]
            ])
        
        # Build education summary
        education_summary = ""
        if profile.education:
            education_summary = "\n".join([
                f"- {edu.get('description', '')}"
                for edu in profile.education[:2]
            ])
        
        # Job information
        job_description = job.description[:1000] if job.description else "Not provided"
        job_requirements = ""
        if job.requirements:
            if isinstance(job.requirements, dict):
                job_requirements = "\n".join([
                    f"- {k}: {v}"
                    for k, v in job.requirements.items()
                ])
        
        # Tone instructions
        tone_instructions = {
            "professional": "Use a formal, professional tone",
            "friendly": "Use a warm, friendly but still professional tone",
            "enthusiastic": "Use an enthusiastic and energetic tone",
            "confident": "Use a confident and assertive tone"
        }
        
        # Length instructions
        length_instructions = {
            "short": "Keep it brief, around 200-300 words",
            "medium": "Write a standard length cover letter, around 300-400 words",
            "long": "Write a detailed cover letter, around 400-500 words"
        }
        
        prompt = f"""Write a personalized cover letter for the following job application.

CANDIDATE INFORMATION:
- Skills: {skills}
- Experience Level: {experience_level}
- Location: {location}
- Work History:
{work_summary if work_summary else "Not provided"}
- Education:
{education_summary if education_summary else "Not provided"}

JOB INFORMATION:
- Position: {job.title}
- Company: {job.company}
- Location: {job.location or "Not specified"}
- Description: {job_description}
- Requirements:
{job_requirements if job_requirements else "Not specified"}

INSTRUCTIONS:
- {tone_instructions.get(tone, tone_instructions['professional'])}
- {length_instructions.get(length, length_instructions['medium'])}
- Address the letter to the hiring manager (use "Dear Hiring Manager" if company name is not available)
- Highlight the candidate's most relevant skills and experience for this specific role
- Show enthusiasm for the position and company
- Include a strong closing statement
- Do not include placeholders or generic statements - make it specific to this job

Generate the cover letter now:"""
        
        return prompt
    
    def improve_cover_letter(
        self,
        cover_letter: str,
        feedback: str
    ) -> str:
        """Improve an existing cover letter based on feedback."""
        if not self.client:
            raise ValueError("OpenAI API key not configured")
        
        prompt = f"""Improve the following cover letter based on this feedback:

FEEDBACK: {feedback}

CURRENT COVER LETTER:
{cover_letter}

Please revise the cover letter to address the feedback while maintaining its core message and structure."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional career coach helping job seekers improve their cover letters."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            improved_letter = response.choices[0].message.content.strip()
            return improved_letter
        except Exception as e:
            raise Exception(f"Error improving cover letter: {str(e)}")

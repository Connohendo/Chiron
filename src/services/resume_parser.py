"""Resume parsing service."""
import PyPDF2
from docx import Document
from typing import Dict, List, Optional
import re


class ResumeParser:
    """Parse resumes from PDF and DOCX files."""
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            from io import BytesIO
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file."""
        try:
            from io import BytesIO
            doc_file = BytesIO(file_content)
            doc = Document(doc_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            raise ValueError(f"Error parsing DOCX: {str(e)}")
    
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """Extract skills from resume text."""
        # Common technical skills keywords
        skill_keywords = [
            "python", "javascript", "java", "c++", "c#", "go", "rust", "ruby",
            "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
            "sql", "postgresql", "mysql", "mongodb", "redis",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "git", "github", "gitlab", "jenkins", "ci/cd",
            "machine learning", "ai", "data science", "analytics",
            "agile", "scrum", "project management"
        ]
        
        text_lower = text.lower()
        found_skills = []
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Also look for skills section
        skills_section = re.search(r'(?:skills|technical skills|competencies)[:]\s*(.+?)(?:\n\n|\n[A-Z]|$)', 
                                   text, re.IGNORECASE | re.DOTALL)
        if skills_section:
            skills_text = skills_section.group(1)
            # Extract comma or bullet-separated skills
            skills_list = re.split(r'[,•\-\n]', skills_text)
            for skill in skills_list:
                skill = skill.strip()
                if skill and len(skill) > 2:
                    found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    @staticmethod
    def extract_experience(text: str) -> List[Dict]:
        """Extract work experience from resume text."""
        experience = []
        
        # Look for experience section
        exp_section = re.search(r'(?:experience|work experience|employment)[:]\s*(.+?)(?:\n\n\n|\n[A-Z]{3,}|$)',
                                text, re.IGNORECASE | re.DOTALL)
        if exp_section:
            exp_text = exp_section.group(1)
            # Try to parse individual experiences
            exp_entries = re.split(r'\n(?=[A-Z][a-z]+.*\d{4})', exp_text)
            for entry in exp_entries[:5]:  # Limit to 5 most recent
                if len(entry.strip()) > 20:
                    experience.append({
                        "description": entry.strip()[:500]  # Limit length
                    })
        
        return experience
    
    @staticmethod
    def extract_education(text: str) -> List[Dict]:
        """Extract education from resume text."""
        education = []
        
        # Look for education section
        edu_section = re.search(r'(?:education|academic)[:]\s*(.+?)(?:\n\n\n|\n[A-Z]{3,}|$)',
                                text, re.IGNORECASE | re.DOTALL)
        if edu_section:
            edu_text = edu_section.group(1)
            # Try to parse education entries
            edu_entries = re.split(r'\n(?=[A-Z])', edu_text)
            for entry in edu_entries[:3]:  # Limit to 3 most recent
                if len(entry.strip()) > 10:
                    education.append({
                        "description": entry.strip()[:300]
                    })
        
        return education
    
    @staticmethod
    def extract_certifications(text: str) -> List[str]:
        """Extract certifications from resume text."""
        certifications = []
        
        # Look for certifications section
        cert_section = re.search(r'(?:certifications|certificates|credentials)[:]\s*(.+?)(?:\n\n\n|\n[A-Z]{3,}|$)',
                                 text, re.IGNORECASE | re.DOTALL)
        if cert_section:
            cert_text = cert_section.group(1)
            cert_list = re.split(r'[,•\-\n]', cert_text)
            for cert in cert_list:
                cert = cert.strip()
                if cert and len(cert) > 5:
                    certifications.append(cert)
        
        return certifications
    
    @staticmethod
    def determine_experience_level(text: str) -> str:
        """Determine experience level from resume text."""
        text_lower = text.lower()
        
        # Look for years of experience
        years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience', text_lower)
        if years_match:
            years = int(years_match.group(1))
            if years >= 10:
                return "executive"
            elif years >= 5:
                return "senior"
            elif years >= 2:
                return "mid"
            else:
                return "entry"
        
        # Look for keywords
        if any(word in text_lower for word in ["senior", "lead", "principal", "architect", "manager"]):
            return "senior"
        elif any(word in text_lower for word in ["junior", "entry", "intern", "graduate"]):
            return "entry"
        else:
            return "mid"
    
    @classmethod
    def parse_resume(cls, file_content: bytes, filename: str) -> Dict:
        """Parse resume file and extract structured data."""
        # Determine file type and extract text
        if filename.endswith('.pdf'):
            text = cls.extract_text_from_pdf(file_content)
        elif filename.endswith('.docx') or filename.endswith('.doc'):
            text = cls.extract_text_from_docx(file_content)
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        
        # Extract structured information
        return {
            "resume_text": text,
            "skills": cls.extract_skills(text),
            "experience_level": cls.determine_experience_level(text),
            "work_history": cls.extract_experience(text),
            "education": cls.extract_education(text),
            "certifications": cls.extract_certifications(text)
        }

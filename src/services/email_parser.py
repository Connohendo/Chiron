"""Email parsing service for Gmail API."""
import re
from typing import Dict, Optional, List
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import pickle
import os
from src.config import settings


class EmailParser:
    """Parse emails to detect application status."""
    
    # Keywords for different statuses
    ACTIVE_KEYWORDS = [
        "application received", "we received your application", "thank you for applying",
        "application confirmation", "your application has been received", "application submitted"
    ]
    
    INTERESTED_KEYWORDS = [
        "interview", "schedule", "assessment", "next steps", "phone screen",
        "technical interview", "hiring manager", "would like to speak",
        "follow up", "assessment test", "coding challenge", "take home"
    ]
    
    CLOSED_KEYWORDS = [
        "unfortunately", "not moving forward", "not selected", "other candidates",
        "position has been filled", "we've decided", "not a fit", "regret to inform",
        "thank you for your interest", "we will not be"
    ]
    
    @staticmethod
    def parse_email_status(subject: str, body: str) -> Dict[str, any]:
        """Parse email to determine application status."""
        subject_lower = subject.lower()
        body_lower = body.lower()
        combined_text = f"{subject_lower} {body_lower}"
        
        status = None
        action_required = False
        
        # Check for closed/rejection
        if any(keyword in combined_text for keyword in EmailParser.CLOSED_KEYWORDS):
            status = "closed"
        
        # Check for interested/needs attention
        elif any(keyword in combined_text for keyword in EmailParser.INTERESTED_KEYWORDS):
            status = "interested"
            action_required = True
        
        # Check for active/confirmation
        elif any(keyword in combined_text for keyword in EmailParser.ACTIVE_KEYWORDS):
            status = "active"
        
        # Extract job/company information
        company_match = re.search(r'from:\s*([^\n<]+)', body, re.IGNORECASE)
        company = company_match.group(1).strip() if company_match else None
        
        # Extract dates mentioned
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december))'
        ]
        
        return {
            "status": status,
            "action_required": action_required,
            "company": company
        }
    
    @staticmethod
    def extract_job_info_from_email(body: str) -> Optional[Dict]:
        """Extract job information from email body."""
        # Try to find job title
        title_patterns = [
            r'position[:\s]+([^\n]+)',
            r'role[:\s]+([^\n]+)',
            r'for the ([^\n]+) position'
        ]
        
        job_title = None
        for pattern in title_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                break
        
        return {
            "job_title": job_title
        } if job_title else None


class GmailService:
    """Gmail API service for fetching and parsing emails."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self):
        self.service = None
        self.credentials = None
    
    def get_authorization_url(self) -> str:
        """Get Gmail OAuth authorization URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.gmail_redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = settings.gmail_redirect_uri
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return authorization_url
    
    def authenticate(self, authorization_code: str) -> Credentials:
        """Authenticate with Gmail using authorization code."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.gmail_redirect_uri]
                }
            },
            scopes=self.SCOPES
        )
        flow.redirect_uri = settings.gmail_redirect_uri
        
        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials
        
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)
        
        return credentials
    
    def set_credentials(self, credentials: Credentials):
        """Set credentials for Gmail service."""
        self.credentials = credentials
        if credentials.valid:
            self.service = build('gmail', 'v1', credentials=credentials)
        elif credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self.service = build('gmail', 'v1', credentials=credentials)
    
    def search_emails(self, query: str = "is:unread", max_results: int = 50) -> List[Dict]:
        """Search for emails matching query."""
        if not self.service:
            raise ValueError("Gmail service not authenticated")
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            email_data = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Extract headers
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
                date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                # Extract body
                body = self._extract_body(msg['payload'])
                
                # Parse date
                try:
                    from email.utils import parsedate_to_datetime
                    received_date = parsedate_to_datetime(date_str)
                except:
                    received_date = datetime.now()
                
                email_data.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'body': body,
                    'received_date': received_date
                })
            
            return email_data
        except Exception as e:
            raise Exception(f"Error fetching emails: {str(e)}")
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload."""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    import base64
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body'].get('data', '')
                    import base64
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    # Simple HTML to text conversion
                    from html.parser import HTMLParser
                    class HTMLTextExtractor(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.text = []
                        def handle_data(self, data):
                            self.text.append(data)
                    parser = HTMLTextExtractor()
                    parser.feed(html_body)
                    body = ' '.join(parser.text)
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                import base64
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body
    
    def get_job_related_emails(self, max_results: int = 50) -> List[Dict]:
        """Get job-related emails."""
        # Search for emails from common job board domains and keywords
        query = "(from:indeed.com OR from:linkedin.com OR from:glassdoor.com OR from:monster.com OR from:ziprecruiter.com OR subject:application OR subject:interview OR subject:job)"
        
        emails = self.search_emails(query, max_results)
        
        # Filter and parse emails
        parsed_emails = []
        for email in emails:
            parsed = EmailParser.parse_email_status(email['subject'], email['body'])
            parsed_emails.append({
                **email,
                **parsed
            })
        
        return parsed_emails

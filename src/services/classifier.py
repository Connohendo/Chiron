"""Classify incoming emails as job-application events.

Primary:   OpenAI (when an API key is configured)
Fallback:  keyword matching

Categories
----------
open             – company acknowledged the application
needs_attention  – interview invite, assessment, or action required
closed           – rejection / position filled
None             – not a recognisable job-application email

The AI path returns classification *and* entity extraction (company, position)
in a single call for better accuracy.
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger(__name__)

# ── AI classification ────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an email classifier for a job-application tracker.

Given the subject line and body of an email, determine:
1. Whether the email relates to a job application.
2. If yes, classify it into exactly ONE of these statuses:
   • "open"             – the company acknowledged or confirmed receiving the application.
   • "needs_attention"  – the company is requesting action: scheduling an interview,
                          completing an assessment/test, a phone screen, etc.
   • "closed"           – the application was rejected or the position was filled.
3. Extract the company name and job position/title if possible.

Respond with ONLY a JSON object (no markdown fences):
{
  "is_job_email": true/false,
  "status": "open" | "needs_attention" | "closed" | null,
  "company": "Company Name" or "",
  "position": "Job Title" or ""
}
"""


def classify_email_ai(
    subject: str, body: str, api_key: str
) -> dict | None:
    """Use OpenAI to classify an email. Returns a dict or None on failure."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        # Truncate very long bodies to save tokens
        trimmed_body = body[:3000] if body else ""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=200,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Subject: {subject}\n\n"
                        f"Body:\n{trimmed_body}"
                    ),
                },
            ],
        )

        text = resp.choices[0].message.content.strip()
        # Strip markdown fences if the model adds them
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        data = json.loads(text)

        if not data.get("is_job_email"):
            return {"status": None, "company": "", "position": ""}

        status = data.get("status")
        if status not in ("open", "needs_attention", "closed"):
            status = None

        return {
            "status": status,
            "company": data.get("company", "") or "",
            "position": data.get("position", "") or "",
        }

    except Exception as exc:
        logger.warning("AI classification failed, falling back to keywords: %s", exc)
        return None


# ── Keyword fallback ─────────────────────────────────────────────────────────

OPEN_KEYWORDS = [
    "received your application",
    "application received",
    "thank you for applying",
    "thanks for applying",
    "we have received your",
    "application has been submitted",
    "successfully submitted",
    "application confirmation",
    "we got your application",
    "your application for",
    "applied to",
    "application submitted",
    "thanks for your interest",
    "thank you for your interest",
]

NEEDS_ATTENTION_KEYWORDS = [
    "schedule an interview",
    "interview invitation",
    "phone screen",
    "video interview",
    "assessment",
    "coding challenge",
    "coding test",
    "take-home",
    "technical test",
    "next steps",
    "would like to meet",
    "your availability",
    "please complete",
    "action required",
    "online test",
    "hackerrank",
    "codility",
    "move forward",
    "like to invite you",
    "pleased to invite",
    "we'd love to chat",
    "set up a time",
    "book a time",
]

CLOSED_KEYWORDS = [
    "unfortunately",
    "not moving forward",
    "decided not to",
    "position has been filled",
    "we regret",
    "not selected",
    "will not be moving",
    "after careful consideration",
    "other candidates",
    "pursue other candidates",
    "not be proceeding",
    "wish you the best",
    "decided to move forward with",
    "no longer being considered",
    "not a match",
    "we have decided",
    "unable to offer",
]


def classify_email(subject: str, body: str) -> str | None:
    """Keyword-based classification (fallback). Returns status or None."""
    text = f"{subject} {body}".lower()

    for kw in CLOSED_KEYWORDS:
        if kw in text:
            return "closed"
    for kw in NEEDS_ATTENTION_KEYWORDS:
        if kw in text:
            return "needs_attention"
    for kw in OPEN_KEYWORDS:
        if kw in text:
            return "open"
    return None


# ── Entity extraction helpers (used only by keyword fallback) ────────────────

_CLEAN_SUFFIXES = re.compile(
    r"\s*(Careers|Recruiting|Jobs|Hiring|HR|Talent|Team|Notifications|via)\s*$",
    re.IGNORECASE,
)

_GENERIC_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "hotmail.com",
    "outlook.com", "live.com", "aol.com", "icloud.com", "me.com",
    "mail.com", "protonmail.com",
}


def extract_company_name(email_from: str, subject: str) -> str:
    """Best-effort company name from the From header or subject line."""
    m = re.match(r'^"?([^"<]+)"?\s*<', email_from)
    if m:
        name = _CLEAN_SUFFIXES.sub("", m.group(1)).strip()
        if name and len(name) > 1:
            return name

    m = re.search(r"@([a-zA-Z0-9.-]+)", email_from)
    if m:
        domain = m.group(1).lower()
        if domain not in _GENERIC_DOMAINS:
            parts = domain.split(".")
            if len(parts) >= 2:
                return parts[-2].capitalize()

    for pat in (r"at\s+([A-Z][a-zA-Z\s&]+)", r"from\s+([A-Z][a-zA-Z\s&]+)"):
        m = re.search(pat, subject)
        if m:
            return m.group(1).strip()

    return "Unknown Company"


def extract_position(subject: str, body: str) -> str:
    """Best-effort job title from the email content."""
    text = f"{subject} {body}"
    patterns = [
        r"(?:position|role|job|application)\s*(?:of|for|:)\s*([A-Z][a-zA-Z\s/&-]+)",
        r"(?:applied for|applying for)\s+(?:the\s+)?([A-Z][a-zA-Z\s/&-]+)",
        r"([A-Z][a-zA-Z\s]*(?:Engineer|Developer|Designer|Manager|Analyst|Scientist|Architect|Lead|Director|Intern|Associate))",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            pos = m.group(1).strip()
            if len(pos) < 60:
                return pos
    return ""

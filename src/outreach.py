"""Creates Gmail drafts for job outreach emails. Thin wrapper over autoapply."""

from typing import Optional
from src.models import Job
from src.autoapply import create_draft


def create_application_draft(job: Job, email_body: str, recruiter_email: str = "") -> Optional[str]:
    from src.autoapply import _guess_recruiter_email
    to = recruiter_email or _guess_recruiter_email(job)
    subject = f"Application: {job.title} — Dhwani Soni"
    return create_draft(to=to, subject=subject, body=email_body)

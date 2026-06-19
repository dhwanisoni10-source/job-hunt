from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str = ""
    posted_date: Optional[str] = None
    salary: Optional[str] = None
    job_id: Optional[str] = None
    found_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def dedup_key(self) -> str:
        return f"{self.company.lower().strip()}::{self.title.lower().strip()}"


@dataclass
class Application:
    job: Job
    status: str = "found"          # found | tailored | applied | outreach_sent | interview | offer | rejected
    tailored_resume: str = ""
    cover_letter: str = ""
    outreach_email: str = ""
    gmail_draft_id: Optional[str] = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

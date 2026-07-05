"""
Auto-apply module — sends outreach emails and tracks application status.

Strategy by job source:
  - Jobs with a direct recruiter email → send via Gmail
  - All others → send cold outreach to guessed recruiter address + open apply URL

Requires: credentials.json + token.json (Google OAuth, same as outreach.py)
Gmail scope needed: gmail.send (in addition to gmail.compose)
"""

import os
import base64
import email.mime.text
import email.mime.multipart
import email.mime.application
import sqlite3
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from src.models import Job


# ── Gmail ─────────────────────────────────────────────────────────────────────

def _gmail_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send",
    ]
    creds = None
    token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_file):
                raise RuntimeError(
                    "credentials.json not found. Download it from Google Cloud Console → "
                    "APIs & Services → Credentials → OAuth 2.0 Client IDs."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def _build_message(
    to: str,
    subject: str,
    body: str,
    sender: str,
    resume_path: Optional[str] = None,
) -> dict:
    """Build a raw MIME message, optionally attaching the resume PDF/docx."""
    if resume_path and Path(resume_path).exists():
        msg = email.mime.multipart.MIMEMultipart()
        msg.attach(email.mime.text.MIMEText(body, "plain"))
        with open(resume_path, "rb") as f:
            part = email.mime.application.MIMEApplication(f.read())
            filename = Path(resume_path).name
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)
    else:
        msg = email.mime.text.MIMEText(body)

    msg["to"] = to
    msg["from"] = sender
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def send_email(
    to: str,
    subject: str,
    body: str,
    sender: str = "sonidhwaniwork@gmail.com",
    resume_path: Optional[str] = None,
) -> Optional[str]:
    """Send immediately. Returns message ID on success."""
    try:
        service = _gmail_service()
        raw_msg = _build_message(to, subject, body, sender, resume_path)
        result = service.users().messages().send(userId="me", body=raw_msg).execute()
        return result.get("id")
    except Exception as exc:
        print(f"  [gmail-send] error: {exc}")
        return None


def create_draft(
    to: str,
    subject: str,
    body: str,
    sender: str = "sonidhwaniwork@gmail.com",
    resume_path: Optional[str] = None,
) -> Optional[str]:
    """Save as draft. Returns draft ID."""
    try:
        service = _gmail_service()
        raw_msg = _build_message(to, subject, body, sender, resume_path)
        draft = service.users().drafts().create(
            userId="me", body={"message": raw_msg}
        ).execute()
        return draft["id"]
    except Exception as exc:
        print(f"  [gmail-draft] warning: {exc}")
        return None


# ── Recruiter email guessing ───────────────────────────────────────────────────

def _guess_recruiter_email(job: Job) -> str:
    """Best-effort guess at a recruiter address from company name."""
    domain = job.company.lower().strip()
    # Strip common suffixes
    for suffix in [" inc", " llc", " corp", " health", " technologies", " labs", " ai"]:
        domain = domain.replace(suffix, "")
    domain = domain.replace(" ", "").replace(",", "").replace(".", "")
    return f"careers@{domain}.com"


# ── Core auto-apply logic ──────────────────────────────────────────────────────

def auto_apply_job(
    job: Job,
    outreach_email: str,
    candidate_email: str = "sonidhwaniwork@gmail.com",
    resume_path: Optional[str] = None,
    dry_run: bool = False,
    open_url: bool = True,
) -> dict:
    """
    Apply to a single job. Returns a result dict with keys:
      sent (bool), draft_id (str|None), method (str), to (str), error (str|None)
    """
    to = _guess_recruiter_email(job)
    subject = f"Application: {job.title} — Dhwani Soni"

    if dry_run:
        return {
            "sent": False,
            "draft_id": None,
            "method": "dry_run",
            "to": to,
            "error": None,
        }

    # Try to send; fall back to draft if Gmail not configured
    try:
        msg_id = send_email(
            to=to,
            subject=subject,
            body=outreach_email,
            sender=candidate_email,
            resume_path=resume_path,
        )
        if msg_id:
            if open_url and job.url:
                # Also open the job URL so you can complete any ATS form
                webbrowser.open(job.url)
            return {"sent": True, "draft_id": None, "method": "email_sent", "to": to, "error": None}
        else:
            raise RuntimeError("send returned no message ID")
    except Exception as exc:
        # Fall back to draft
        draft_id = create_draft(
            to=to,
            subject=subject,
            body=outreach_email,
            sender=candidate_email,
            resume_path=resume_path,
        )
        return {
            "sent": False,
            "draft_id": draft_id,
            "method": "draft_fallback",
            "to": to,
            "error": str(exc),
        }


def auto_apply_batch(
    jobs: List[dict],
    db_path: str,
    candidate_email: str = "sonidhwaniwork@gmail.com",
    resume_path: Optional[str] = None,
    dry_run: bool = False,
    delay_seconds: float = 3.0,
) -> List[dict]:
    """
    Apply to a list of jobs (as dicts from the tracker DB).
    Updates DB status to 'applied' or 'outreach_sent' after each.
    Respects delay_seconds between sends to avoid spam flags.
    """
    results = []
    for job_dict in jobs:
        outreach = job_dict.get("outreach_email", "")
        if not outreach:
            results.append({"job": job_dict["title"], "skipped": "no outreach email drafted yet"})
            continue

        job = Job(
            title=job_dict["title"],
            company=job_dict["company"],
            location=job_dict["location"],
            url=job_dict["url"],
            source=job_dict["source"],
            description=job_dict.get("description", ""),
            salary=job_dict.get("salary"),
        )

        result = auto_apply_job(
            job=job,
            outreach_email=outreach,
            candidate_email=candidate_email,
            resume_path=resume_path,
            dry_run=dry_run,
        )
        result["job"] = job_dict["title"]
        result["company"] = job_dict["company"]
        results.append(result)

        # Update DB status
        new_status = "applied" if result["sent"] else "outreach_sent"
        _update_status(db_path, job_dict["dedup_key"], new_status)

        time.sleep(delay_seconds)

    return results


def _update_status(db_path: str, dedup_key: str, status: str):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE jobs SET status=?, updated_at=? WHERE dedup_key=?",
            (status, datetime.now().isoformat(), dedup_key),
        )
        conn.commit()

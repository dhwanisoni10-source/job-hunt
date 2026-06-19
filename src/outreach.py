"""Creates Gmail drafts for job outreach emails."""

import os
import base64
import email.mime.text
from typing import Optional
from src.models import Job


def _gmail_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
    creds = None
    token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def create_draft(
    to: str,
    subject: str,
    body: str,
    sender: str = "sonidhwaniwork@gmail.com",
) -> Optional[str]:
    """Creates a Gmail draft and returns the draft ID."""
    try:
        service = _gmail_service()
        message = email.mime.text.MIMEText(body)
        message["to"] = to
        message["from"] = sender
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = service.users().drafts().create(
            userId="me", body={"message": {"raw": raw}}
        ).execute()
        return draft["id"]
    except Exception as exc:
        print(f"  [gmail] warning: could not create draft — {exc}")
        return None


def create_application_draft(job: Job, email_body: str, recruiter_email: str = "") -> Optional[str]:
    subject = f"PM Role Inquiry — {job.title} at {job.company}"
    to = recruiter_email or f"recruiting@{job.company.lower().replace(' ', '')}.com"
    return create_draft(to=to, subject=subject, body=email_body)

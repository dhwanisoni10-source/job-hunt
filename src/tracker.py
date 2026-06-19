"""SQLite tracker + optional Google Sheets sync."""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional
from src.models import Job, Application


class Tracker:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    dedup_key TEXT PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    url TEXT,
                    source TEXT,
                    description TEXT,
                    posted_date TEXT,
                    salary TEXT,
                    found_at TEXT,
                    status TEXT DEFAULT 'found',
                    tailored_resume TEXT DEFAULT '',
                    cover_letter TEXT DEFAULT '',
                    outreach_email TEXT DEFAULT '',
                    gmail_draft_id TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()

    def is_seen(self, job: Job) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM jobs WHERE dedup_key = ?", (job.dedup_key(),)
            ).fetchone()
            return row is not None

    def add_job(self, job: Job) -> bool:
        """Returns True if newly inserted, False if already existed."""
        if self.is_seen(job):
            return False
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO jobs
                   (dedup_key, title, company, location, url, source, description,
                    posted_date, salary, found_at, status, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    job.dedup_key(), job.title, job.company, job.location,
                    job.url, job.source, job.description, job.posted_date,
                    job.salary, job.found_at, "found", now, now,
                ),
            )
            conn.commit()
        return True

    def update_application(self, app: Application):
        now = datetime.now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """UPDATE jobs SET
                   status=?, tailored_resume=?, cover_letter=?,
                   outreach_email=?, gmail_draft_id=?, notes=?, updated_at=?
                   WHERE dedup_key=?""",
                (
                    app.status, app.tailored_resume, app.cover_letter,
                    app.outreach_email, app.gmail_draft_id or "",
                    app.notes, now, app.job.dedup_key(),
                ),
            )
            conn.commit()

    def get_new_jobs(self, status: str = "found") -> List[dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC", (status,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all(self) -> List[dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> dict:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) as n FROM jobs GROUP BY status"
            ).fetchall()
            return {r[0]: r[1] for r in rows}


class SheetsSync:
    """Syncs tracker data to Google Sheets. Requires gspread + credentials.json."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    HEADERS = [
        "Status", "Title", "Company", "Location", "Source",
        "Posted Date", "URL", "Has Resume", "Has Cover Letter",
        "Draft Created", "Notes", "Found At",
    ]

    def __init__(self, sheet_id: Optional[str] = None):
        self.sheet_id = sheet_id
        self._gc = None

    def _client(self):
        if self._gc:
            return self._gc
        try:
            import gspread
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request

            creds = None
            token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
            creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(token_file, "w") as f:
                    f.write(creds.to_json())

            self._gc = gspread.authorize(creds)
        except ImportError:
            raise RuntimeError("Run: pip install gspread google-auth-oauthlib")
        return self._gc

    def sync(self, tracker: Tracker) -> str:
        import gspread
        gc = self._client()
        all_jobs = tracker.get_all()

        if self.sheet_id:
            sh = gc.open_by_key(self.sheet_id)
            ws = sh.sheet1
        else:
            sh = gc.create("Job Hunt Tracker — Dhwani Soni")
            ws = sh.sheet1
            self.sheet_id = sh.id
            sh.share(None, perm_type="anyone", role="reader")

        rows = [self.HEADERS]
        for j in all_jobs:
            rows.append([
                j["status"],
                j["title"],
                j["company"],
                j["location"],
                j["source"],
                j["posted_date"] or "",
                j["url"],
                "✓" if j["tailored_resume"] else "",
                "✓" if j["cover_letter"] else "",
                "✓" if j["gmail_draft_id"] else "",
                j["notes"] or "",
                j["found_at"],
            ])

        ws.clear()
        ws.update("A1", rows)
        ws.format("A1:L1", {"textFormat": {"bold": True}})
        return sh.url

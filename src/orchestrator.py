"""
Main pipeline: find → deduplicate → tailor → draft emails → track.
"""

import os
import time
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from src.models import Job, Application
from src.tracker import Tracker, SheetsSync
from src.finder.indeed import IndeedFinder
from src.finder.linkedin import LinkedInFinder
from src.tailor import tailor_resume, draft_cover_letter, draft_outreach_email
from src.outreach import create_application_draft

load_dotenv()
console = Console()


def load_master_resume(path: str = "master_resume.txt") -> str:
    return Path(path).read_text()


def find_jobs(config: dict) -> List[Job]:
    target = config["target"]
    search_cfg = config["search"]
    boards = search_cfg.get("boards", ["indeed"])
    days_back = search_cfg.get("days_back", 7)
    max_jobs = search_cfg.get("max_jobs_per_run", 30)

    all_jobs: List[Job] = []
    queries = target["roles"]
    locations = target["locations"]

    for query in queries:
        for location in locations:
            if "indeed" in boards:
                finder = IndeedFinder(config)
                found = finder.search(query, location, days_back)
                console.print(f"  [indeed] '{query}' in '{location}': {len(found)} jobs")
                all_jobs.extend(found)
                time.sleep(1)

            if "linkedin" in boards:
                finder = LinkedInFinder(config)
                found = finder.search(query, location, days_back)
                console.print(f"  [linkedin] '{query}' in '{location}': {len(found)} jobs")
                all_jobs.extend(found)
                time.sleep(2)

    # Deduplicate by dedup_key
    seen = set()
    unique: List[Job] = []
    for j in all_jobs:
        k = j.dedup_key()
        if k not in seen:
            seen.add(k)
            unique.append(j)

    # Filter out excluded keywords
    exclude = [kw.lower() for kw in target.get("exclude_keywords", [])]
    filtered = [j for j in unique if not any(kw in j.title.lower() for kw in exclude)]

    return filtered[:max_jobs]


def process_job(job: Job, master_resume: str, config: dict, tracker: Tracker) -> Application:
    """Tailor resume + cover letter + outreach email for one job."""
    app = Application(job=job)

    try:
        console.print(f"    Tailoring resume...", end=" ")
        app.tailored_resume = tailor_resume(master_resume, job)
        console.print("[green]✓[/green]")
    except Exception as e:
        console.print(f"[red]✗ {e}[/red]")

    try:
        console.print(f"    Drafting cover letter...", end=" ")
        app.cover_letter = draft_cover_letter(master_resume, job)
        console.print("[green]✓[/green]")
    except Exception as e:
        console.print(f"[red]✗ {e}[/red]")

    try:
        console.print(f"    Writing outreach email...", end=" ")
        app.outreach_email = draft_outreach_email(job, config["candidate"]["name"])
        console.print("[green]✓[/green]")
    except Exception as e:
        console.print(f"[red]✗ {e}[/red]")

    try:
        if app.outreach_email:
            console.print(f"    Creating Gmail draft...", end=" ")
            draft_id = create_application_draft(job, app.outreach_email)
            app.gmail_draft_id = draft_id
            console.print("[green]✓[/green]" if draft_id else "[yellow]skipped[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ {e}[/red]")

    app.status = "tailored"
    tracker.update_application(app)
    return app


def run(config: dict, tailor: bool = True, sheets_sync: bool = False):
    tracker = Tracker(config["tracking"]["db_path"])
    master_resume = load_master_resume(config["resume"]["master_resume_path"])

    console.rule("[bold blue]Job Hunt — Finding Jobs")
    jobs = find_jobs(config)
    console.print(f"\nFound [bold]{len(jobs)}[/bold] total jobs")

    new_jobs = [j for j in jobs if tracker.add_job(j)]
    console.print(f"[green]{len(new_jobs)} new[/green] (skipping {len(jobs) - len(new_jobs)} duplicates)\n")

    if tailor and new_jobs:
        console.rule("[bold blue]Tailoring & Drafting")
        for i, job in enumerate(new_jobs, 1):
            console.print(f"\n[bold]({i}/{len(new_jobs)}) {job.title} @ {job.company}[/bold]")
            process_job(job, master_resume, config, tracker)
            time.sleep(1)

    # Print summary table
    console.rule("[bold blue]Summary")
    stats = tracker.stats()
    table = Table(title="Pipeline Status")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    for status, count in sorted(stats.items()):
        table.add_row(status, str(count))
    console.print(table)

    if sheets_sync:
        try:
            sheet_id = config["tracking"].get("google_sheet_id")
            syncer = SheetsSync(sheet_id)
            url = syncer.sync(tracker)
            console.print(f"\n[green]Google Sheet updated:[/green] {url}")
        except Exception as e:
            console.print(f"\n[yellow]Sheets sync skipped: {e}[/yellow]")

    console.print("\n[bold green]Done![/bold green] Check jobs.db or run `python run.py show` to review.")

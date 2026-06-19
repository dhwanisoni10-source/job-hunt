"""
Auto-apply pipeline.
Pulls tailored jobs from the DB and submits applications on LinkedIn / Indeed.
"""

import os
import time
from pathlib import Path
from rich.console import Console
from dotenv import load_dotenv

from src.tracker import Tracker
from src.models import Job, Application
from src.apply.resume_converter import prepare_resume_file
from src.apply.answers import CANDIDATE

load_dotenv()
console = Console()


def run_auto_apply(
    config: dict,
    max_per_run: int = 10,
    platforms: list[str] | None = None,
    dry_run: bool = False,
):
    """
    Main auto-apply loop. Reads tailored jobs from DB and submits applications.

    Args:
        config:       loaded config.yaml dict
        max_per_run:  max applications to submit in one session
        platforms:    ['linkedin', 'indeed'] — defaults to both
        dry_run:      if True, fill forms but don't click final Submit
    """
    if platforms is None:
        platforms = ["linkedin", "indeed"]

    li_email = os.getenv("LINKEDIN_EMAIL", "")
    li_password = os.getenv("LINKEDIN_PASSWORD", "")
    indeed_email = os.getenv("INDEED_EMAIL", li_email)
    indeed_password = os.getenv("INDEED_PASSWORD", li_password)

    tracker = Tracker(config["tracking"]["db_path"])
    master_resume = Path(config["resume"]["master_resume_path"]).read_text()

    # Get jobs that have been tailored but not yet applied
    jobs_to_apply = tracker.get_new_jobs("tailored")
    console.print(f"\nFound [bold]{len(jobs_to_apply)}[/bold] tailored jobs ready to apply")

    if not jobs_to_apply:
        console.print("[yellow]No tailored jobs yet. Run `python run.py run` first.[/yellow]")
        return

    applied = 0
    for row in jobs_to_apply[:max_per_run]:
        if applied >= max_per_run:
            break

        job = Job(
            title=row["title"],
            company=row["company"],
            location=row["location"],
            url=row["url"],
            source=row["source"],
            description=row["description"] or "",
        )
        tailored_resume = row["tailored_resume"] or master_resume
        cover_letter = row["cover_letter"] or ""

        console.print(f"\n[bold]Applying: {job.title} @ {job.company}[/bold] [{job.source}]")

        # Convert resume to PDF
        resume_path = prepare_resume_file(tailored_resume, job.company)

        result = "skipped"
        try:
            if job.source == "linkedin" and "linkedin" in platforms and li_email:
                result = _apply_linkedin(job, resume_path, cover_letter, tailored_resume,
                                         li_email, li_password, dry_run)
            elif job.source == "indeed" and "indeed" in platforms and indeed_email:
                result = _apply_indeed(job, resume_path, cover_letter, tailored_resume,
                                       indeed_email, indeed_password, dry_run)
            else:
                console.print(f"  [yellow]Skipping {job.source} (not configured or not in platforms)[/yellow]")
                result = "skipped"
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
            result = "error"

        if result == "applied":
            app = Application(job=job, status="applied",
                              tailored_resume=tailored_resume, cover_letter=cover_letter)
            tracker.update_application(app)
            applied += 1
            console.print(f"  [green]✓ Applied ({applied}/{max_per_run})[/green]")
        elif result == "skipped":
            console.print(f"  [yellow]Skipped[/yellow]")
        else:
            console.print(f"  [red]Failed — marked for manual review[/red]")

        time.sleep(3)  # pace between applications

    console.print(f"\n[bold green]Done! Submitted {applied} application(s) this run.[/bold green]")
    console.print(tracker.stats())


def _apply_linkedin(job, resume_path, cover_letter, resume_text,
                    email, password, dry_run) -> str:
    from src.apply.linkedin_applier import LinkedInApplier
    with LinkedInApplier(headless=False) as applier:
        if not applier.login(email, password):
            return "error"
        if dry_run:
            console.print("  [cyan][dry run] would submit Easy Apply[/cyan]")
            return "skipped"
        return applier.easy_apply(job, resume_path, cover_letter, resume_text)


def _apply_indeed(job, resume_path, cover_letter, resume_text,
                  email, password, dry_run) -> str:
    from src.apply.indeed_applier import IndeedApplier
    with IndeedApplier(headless=False) as applier:
        if not applier.login(email, password):
            return "error"
        if dry_run:
            console.print("  [cyan][dry run] would submit Indeed Apply[/cyan]")
            return "skipped"
        return applier.apply(job, resume_path, cover_letter, resume_text)

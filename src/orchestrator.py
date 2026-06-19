"""
Main pipeline: find → score → filter → tailor → draft emails → track.
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
from src.finder.remoteok import RemoteOKFinder
from src.finder.weworkremotely import WeWorkRemotelyFinder
from src.finder.himalayas import HimalayasFinder
from src.scorer import score_job, passes_filters
from src.tailor import tailor_resume, draft_cover_letter, draft_outreach_email
from src.outreach import create_application_draft

load_dotenv()
console = Console()

FINDER_MAP = {
    "indeed": IndeedFinder,
    "linkedin": LinkedInFinder,
    "remoteok": RemoteOKFinder,
    "weworkremotely": WeWorkRemotelyFinder,
    "himalayas": HimalayasFinder,
}


def load_master_resume(path: str = "master_resume.txt") -> str:
    return Path(path).read_text()


def find_jobs(config: dict) -> List[Job]:
    target = config["target"]
    search_cfg = config["search"]
    boards = search_cfg.get("boards", ["remoteok", "weworkremotely", "himalayas", "indeed"])
    days_back = search_cfg.get("days_back", 7)
    max_jobs = search_cfg.get("max_jobs_per_run", 100)

    all_jobs: List[Job] = []
    queries = target["roles"]
    locations = target["locations"]
    exclude = [kw.lower() for kw in target.get("exclude_keywords", [])]

    for board in boards:
        finder_cls = FINDER_MAP.get(board)
        if not finder_cls:
            console.print(f"  [yellow]Unknown board: {board}[/yellow]")
            continue

        for query in queries:
            # Remote-first boards don't need location iteration
            if board in ("remoteok", "weworkremotely", "himalayas"):
                finder = finder_cls(config)
                found = finder.search(query, "Remote", days_back)
                console.print(f"  [{board}] '{query}': {len(found)} jobs")
                all_jobs.extend(found)
                time.sleep(0.5)
            else:
                for location in locations:
                    finder = finder_cls(config)
                    found = finder.search(query, location, days_back)
                    console.print(f"  [{board}] '{query}' in '{location}': {len(found)} jobs")
                    all_jobs.extend(found)
                    time.sleep(1)

    # Deduplicate by dedup_key
    seen: set = set()
    unique: List[Job] = []
    for j in all_jobs:
        k = j.dedup_key()
        if k not in seen:
            seen.add(k)
            unique.append(j)

    # Filter excluded keywords from title
    filtered = [j for j in unique if not any(kw in j.title.lower() for kw in exclude)]

    return filtered[:max_jobs]


def score_and_rank(jobs: List[Job], config: dict, use_ai: bool = True) -> List[Job]:
    """Score every job, filter by gates, return ranked list."""
    search_cfg = config["search"]
    min_sal = search_cfg.get("min_salary_score", 6)
    min_ent = search_cfg.get("min_entry_score", 5)
    top_n = search_cfg.get("top_n", 25)

    console.print(f"\nScoring {len(jobs)} jobs (salary ≥ {min_sal}/10, entry ≥ {min_ent}/10)...")
    passed: List[Job] = []

    for job in jobs:
        scores = score_job(job, use_ai=use_ai)
        job.salary_score = scores["salary_score"]
        job.entry_score = scores["entry_score"]
        job.total_score = scores["total_score"]
        job.score_reasoning = scores.get("reasoning", "")

        if scores["salary_score"] >= min_sal and scores["entry_score"] >= min_ent:
            passed.append(job)

    # Sort: total_score desc, then entry_score desc
    passed.sort(key=lambda j: (j.total_score, j.entry_score), reverse=True)

    console.print(f"  [green]{len(passed)} jobs pass both gates[/green] → showing top {top_n}")
    return passed[:top_n]


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


def run(config: dict, tailor: bool = True, sheets_sync: bool = False, use_ai_scoring: bool = True):
    tracker = Tracker(config["tracking"]["db_path"])
    master_resume = load_master_resume(config["resume"]["master_resume_path"])

    console.rule("[bold blue]Job Hunt — Finding 6-Figure Remote Jobs")
    raw_jobs = find_jobs(config)
    console.print(f"\nFound [bold]{len(raw_jobs)}[/bold] unique jobs across all boards")

    # Score & rank
    top_jobs = score_and_rank(raw_jobs, config, use_ai=use_ai_scoring)

    new_jobs = [j for j in top_jobs if tracker.add_job(j)]
    console.print(f"[green]{len(new_jobs)} new[/green] (skipping {len(top_jobs) - len(new_jobs)} duplicates)\n")

    if tailor and new_jobs:
        console.rule("[bold blue]Tailoring & Drafting (Top Opportunities)")
        for i, job in enumerate(new_jobs, 1):
            console.print(
                f"\n[bold]({i}/{len(new_jobs)}) {job.title} @ {job.company}[/bold]  "
                f"[cyan]score {job.total_score}/20[/cyan]  "
                f"[yellow]{job.salary or 'salary unspecified'}[/yellow]"
            )
            process_job(job, master_resume, config, tracker)
            time.sleep(1)

    # Print summary table
    console.rule("[bold blue]Top Opportunities This Run")
    _print_top_table(top_jobs[:15])

    console.rule("[bold blue]Pipeline Status")
    stats = tracker.stats()
    table = Table(title="All Jobs by Stage")
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

    console.print("\n[bold green]Done![/bold green] Run `python run.py top` to see ranked list, or `python run.py review <company>`.")


def _print_top_table(jobs: List[Job]):
    table = Table(title="Top Ranked Jobs (6-Figure + Easy Entry)", show_lines=True)
    table.add_column("#", width=3)
    table.add_column("Score", width=7, justify="right")
    table.add_column("Title", style="bold", width=28)
    table.add_column("Company", width=18)
    table.add_column("Salary", width=20)
    table.add_column("Source", width=12)

    for i, job in enumerate(jobs, 1):
        score_str = f"{job.total_score}/20 (💰{job.salary_score} 🚪{job.entry_score})"
        table.add_row(
            str(i),
            f"{job.total_score}/20",
            job.title[:28],
            job.company[:18],
            job.salary or "—",
            job.source,
        )
    console.print(table)

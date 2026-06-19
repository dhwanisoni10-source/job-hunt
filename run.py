#!/usr/bin/env python3
"""
Job Hunt CLI — 6-Figure Remote Jobs for Dhwani Soni

Usage:
  python run.py run              # find jobs, score, tailor resumes, create drafts
  python run.py run --no-tailor  # find + score only (no AI tailoring calls)
  python run.py run --no-ai-score # heuristic scoring only (no Claude scoring API)
  python run.py run --sheets     # also sync to Google Sheets
  python run.py demo             # run scoring on sample jobs (works offline)
  python run.py top              # show top-ranked jobs by score
  python run.py show             # show all tracked jobs
  python run.py show --status tailored
  python run.py review <company> # print tailored resume + cover letter for a company
  python run.py stats            # show pipeline stats
"""

import sys
import yaml
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv

load_dotenv()
console = Console()


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


@click.group()
def cli():
    """Dhwani's automated job hunt system."""
    pass


@cli.command()
@click.option("--no-tailor", is_flag=True, help="Skip AI tailoring (find + score only)")
@click.option("--no-ai-score", is_flag=True, help="Skip Claude scoring, use heuristics only")
@click.option("--sheets", is_flag=True, help="Sync results to Google Sheets")
@click.option("--config", "config_path", default="config.yaml")
def run(no_tailor, no_ai_score, sheets, config_path):
    """Find 6-figure remote jobs, score them, tailor resumes, and create Gmail drafts."""
    from src.orchestrator import run as _run
    config = load_config(config_path)
    _run(config, tailor=not no_tailor, sheets_sync=sheets, use_ai_scoring=not no_ai_score)


@cli.command()
@click.option("--status", default=None, help="Filter by status (found, tailored, applied...)")
@click.option("--config", "config_path", default="config.yaml")
def show(status, config_path):
    """List all tracked jobs."""
    from src.tracker import Tracker
    config = load_config(config_path)
    tracker = Tracker(config["tracking"]["db_path"])

    if status:
        jobs = tracker.get_new_jobs(status)
    else:
        jobs = tracker.get_all()

    table = Table(title=f"Jobs ({len(jobs)} total)", show_lines=True)
    table.add_column("Status", style="cyan", width=10)
    table.add_column("Score", width=8, justify="right")
    table.add_column("Title", style="bold", width=28)
    table.add_column("Company", width=18)
    table.add_column("Salary", width=18)
    table.add_column("Source", width=12)
    table.add_column("Date", width=10)

    for j in jobs:
        score = j.get("total_score", 0)
        score_str = f"{score}/20" if score else "—"
        table.add_row(
            j["status"],
            score_str,
            j["title"][:28],
            j["company"][:18],
            j.get("salary") or "—",
            j["source"],
            (j["posted_date"] or "")[:10],
        )
    console.print(table)


@cli.command()
@click.option("--n", default=25, help="How many top jobs to show")
@click.option("--config", "config_path", default="config.yaml")
def top(n, config_path):
    """Show top-ranked 6-figure remote jobs by score."""
    from src.tracker import Tracker
    config = load_config(config_path)
    tracker = Tracker(config["tracking"]["db_path"])
    jobs = tracker.get_top(n)

    table = Table(title=f"Top {n} Ranked Jobs", show_lines=True)
    table.add_column("#", width=3)
    table.add_column("Total", width=6, justify="right")
    table.add_column("💰Sal", width=5, justify="right")
    table.add_column("🚪Ent", width=5, justify="right")
    table.add_column("Title", style="bold", width=28)
    table.add_column("Company", width=18)
    table.add_column("Salary", width=20)
    table.add_column("Source", width=12)
    table.add_column("URL", width=40)

    for i, j in enumerate(jobs, 1):
        table.add_row(
            str(i),
            str(j.get("total_score", 0)),
            str(j.get("salary_score", 0)),
            str(j.get("entry_score", 0)),
            j["title"][:28],
            j["company"][:18],
            j.get("salary") or "—",
            j["source"],
            j["url"][:40],
        )
    console.print(table)
    console.print(f"\n[dim]Run `python run.py review <company>` to see tailored resume + cover letter.[/dim]")


@cli.command()
@click.argument("company")
@click.option("--config", "config_path", default="config.yaml")
def review(company, config_path):
    """Print tailored resume and cover letter for a company."""
    from src.tracker import Tracker
    config = load_config(config_path)
    tracker = Tracker(config["tracking"]["db_path"])

    jobs = [j for j in tracker.get_all() if company.lower() in j["company"].lower()]
    if not jobs:
        console.print(f"[red]No jobs found for company: {company}[/red]")
        return

    for j in jobs:
        console.print(Panel(f"[bold]{j['title']} @ {j['company']}[/bold]\n{j['url']}", title="Job"))
        if j["tailored_resume"]:
            console.print(Panel(j["tailored_resume"], title="Tailored Resume"))
        if j["cover_letter"]:
            console.print(Panel(j["cover_letter"], title="Cover Letter"))
        if j["outreach_email"]:
            console.print(Panel(j["outreach_email"], title="Outreach Email"))


@cli.command()
@click.option("--config", "config_path", default="config.yaml")
def stats(config_path):
    """Show pipeline stats."""
    from src.tracker import Tracker
    config = load_config(config_path)
    tracker = Tracker(config["tracking"]["db_path"])
    s = tracker.stats()

    table = Table(title="Pipeline Stats")
    table.add_column("Stage", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    for stage in ["found", "tailored", "applied", "outreach_sent", "interview", "offer", "rejected"]:
        if stage in s:
            table.add_row(stage, str(s[stage]))
    console.print(table)


@cli.command()
@click.argument("company")
@click.option("--status", default="applied", help="New status to set")
@click.option("--config", "config_path", default="config.yaml")
def update(company, status, config_path):
    """Update status for a job (e.g. mark as applied)."""
    import sqlite3
    config = load_config(config_path)
    db = config["tracking"]["db_path"]
    with sqlite3.connect(db) as conn:
        n = conn.execute(
            "UPDATE jobs SET status=? WHERE lower(company) LIKE ?",
            (status, f"%{company.lower()}%"),
        ).rowcount
        conn.commit()
    console.print(f"[green]Updated {n} job(s) to status '{status}'[/green]")


@cli.command()
@click.option("--config", "config_path", default="config.yaml")
def demo(config_path):
    """Score and rank sample jobs offline (no network needed). Good for testing."""
    from src.demo_data import SAMPLE_JOBS
    from src.scorer import score_job
    from src.tracker import Tracker

    config = load_config(config_path)
    tracker = Tracker(config["tracking"]["db_path"])

    console.rule("[bold blue]Demo — Scoring Sample 6-Figure Remote Jobs")
    console.print(f"Scoring {len(SAMPLE_JOBS)} sample jobs (heuristics only, no AI)...\n")

    scored = []
    for job in SAMPLE_JOBS:
        scores = score_job(job, use_ai=False)
        job.salary_score = scores["salary_score"]
        job.entry_score = scores["entry_score"]
        job.total_score = scores["total_score"]
        scored.append(job)

    scored.sort(key=lambda j: (j.total_score, j.entry_score), reverse=True)

    table = Table(title="Sample Jobs Ranked (Score = Salary + Entry Ease)", show_lines=True)
    table.add_column("#", width=3)
    table.add_column("Total", width=6, justify="right")
    table.add_column("💰Sal", width=5, justify="right")
    table.add_column("🚪Ent", width=5, justify="right")
    table.add_column("Title", style="bold", width=28)
    table.add_column("Company", width=18)
    table.add_column("Salary", width=22)
    table.add_column("Why it ranks here", width=35)

    NOTES = {
        "Sword Health": "Series D, 2-4 yrs, clinical background valued",
        "Garner Health": "Seed, 0-2 yrs, training provided, career pivot",
        "Nuna Health": "5+ yrs req, healthcare data domain experience",
        "Turquoise Health": "Series A, 1-3 yrs, willing to train",
        "Hims & Hers Health": "7+ yrs SWE, PhD pref — wrong role",
        "Cohere Health": "Series B, clinical background preferred",
        "Brightline": "3-5 yrs ops, career changers welcome",
        "Oscar Health": "10+ yrs needed, Director-level, too senior",
        "Spring Health": "Series D, clinical background valued, equity",
        "Accolade Health": "Entry-level, $80-95k — below 6-fig threshold",
    }

    for i, job in enumerate(scored, 1):
        note = NOTES.get(job.company, "")
        table.add_row(
            str(i),
            str(job.total_score),
            str(job.salary_score),
            str(job.entry_score),
            job.title[:28],
            job.company[:18],
            job.salary or "—",
            note,
        )

    console.print(table)
    console.print("\n[bold green]The scorer filtered out:[/bold green]")
    console.print("  - Director roles (too senior, excluded by keyword filter)")
    console.print("  - SWE roles (wrong domain for pivot)")
    console.print("  - Sub-$100k roles (salary score < 6)")
    console.print("\n[bold]To find REAL jobs:[/bold] set ANTHROPIC_API_KEY in .env and run [cyan]python run.py run[/cyan]")
    console.print("[dim]System searches RemoteOK, We Work Remotely, Himalayas, Indeed, LinkedIn[/dim]")


if __name__ == "__main__":
    cli()

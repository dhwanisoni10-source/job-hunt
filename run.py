#!/usr/bin/env python3
"""
Job Hunt CLI

Usage:
  python run.py run        # find jobs, tailor resumes, create drafts
  python run.py run --no-tailor   # find jobs only (no AI calls)
  python run.py run --sheets      # also sync to Google Sheets
  python run.py show       # show all tracked jobs
  python run.py show --status tailored
  python run.py review <company>  # print tailored resume + cover letter for a company
  python run.py stats      # show pipeline stats
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
@click.option("--no-tailor", is_flag=True, help="Skip AI tailoring (find jobs only)")
@click.option("--sheets", is_flag=True, help="Sync results to Google Sheets")
@click.option("--config", "config_path", default="config.yaml")
def run(no_tailor, sheets, config_path):
    """Find jobs, tailor resumes, and create Gmail drafts."""
    from src.orchestrator import run as _run
    config = load_config(config_path)
    _run(config, tailor=not no_tailor, sheets_sync=sheets)


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
    table.add_column("Title", style="bold", width=30)
    table.add_column("Company", width=20)
    table.add_column("Location", width=15)
    table.add_column("Source", width=8)
    table.add_column("Date", width=12)

    for j in jobs:
        table.add_row(
            j["status"],
            j["title"],
            j["company"],
            j["location"],
            j["source"],
            (j["posted_date"] or "")[:10],
        )
    console.print(table)


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


if __name__ == "__main__":
    cli()

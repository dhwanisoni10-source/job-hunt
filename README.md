# Job Hunt Automation — Dhwani Soni

Automated PM job search system: finds jobs → tailors resume → drafts cover letters → creates Gmail outreach drafts.

## What it does

1. **Finds jobs** — scrapes LinkedIn and Indeed for Product Manager roles in health tech / digital health
2. **Deduplicates** — SQLite database prevents seeing the same job twice
3. **Tailors your resume** — Claude rewrites your master resume to match each JD's language
4. **Drafts cover letters** — Claude writes a specific, non-generic cover letter for each role
5. **Creates outreach emails** — short cold emails saved directly to Gmail Drafts
6. **Tracks everything** — SQLite + optional Google Sheets sync

## Setup (one time)

```bash
bash setup.sh
```

Then edit `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

For Gmail + Google Sheets, follow the instructions in `.env.example` to get `credentials.json`.

## Usage

```bash
# Full pipeline (find + tailor + draft emails)
python run.py run

# Find jobs only (no AI calls — good for testing)
python run.py run --no-tailor

# Also sync to Google Sheets
python run.py run --sheets

# Review what was generated for a specific company
python run.py review "Teladoc"

# See all tracked jobs
python run.py show

# Filter by status
python run.py show --status tailored

# Mark a job as applied
python run.py update "Omada" --status applied

# Pipeline stats
python run.py stats
```

## Configuring your search

Edit `config.yaml`:
- `target.roles` — PM titles to search
- `target.locations` — cities or "Remote"
- `search.days_back` — how recent the jobs should be
- `search.max_jobs_per_run` — cap per run

## Files

| File | Purpose |
|------|---------|
| `config.yaml` | All your preferences |
| `master_resume.txt` | Your base resume — edit this as your background evolves |
| `jobs.db` | SQLite database of all tracked jobs |
| `run.py` | CLI entry point |
| `src/finder/` | Job scrapers (Indeed, LinkedIn) |
| `src/tailor.py` | Claude-powered resume + cover letter tailoring |
| `src/tracker.py` | SQLite tracker + Google Sheets sync |
| `src/outreach.py` | Gmail draft creator |
| `src/orchestrator.py` | Main pipeline |

## Already done for you

3 outreach emails have been saved to your Gmail Drafts:
- **Teladoc Health** — Senior PM, Clinical Optimization (Remote, $130K–$155K)
- **Hims & Hers** — Digital health PM
- **Omada Health** — Chronic disease / cardiac PM

Go to Gmail → Drafts → review, update the To: address if needed, and send.

## Running on a schedule

To run daily, add to cron:
```
0 8 * * * cd /path/to/job-hunt && python run.py run >> hunt.log 2>&1
```

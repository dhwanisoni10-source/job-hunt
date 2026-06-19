"""
RemoteOK public JSON API — no key required.
Often includes salary ranges directly in the listing.
https://remoteok.com/api
"""

import time
import requests
from typing import List
from src.models import Job
from src.finder.base import BaseFinder

API_URL = "https://remoteok.com/api"


class RemoteOKFinder(BaseFinder):
    """Pulls jobs from RemoteOK's free public API."""

    def search(self, query: str, location: str = "Remote", days_back: int = 7) -> List[Job]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (job-search-bot/1.0)",
                "Accept": "application/json",
            }
            resp = requests.get(API_URL, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"  [remoteok] warning: {exc}")
            return []

        # First item is metadata, skip it
        listings = [item for item in data if isinstance(item, dict) and "id" in item]

        query_lower = query.lower()
        query_terms = query_lower.split()

        jobs: List[Job] = []
        for item in listings:
            title = item.get("position", "") or ""
            description = item.get("description", "") or ""
            tags = " ".join(item.get("tags", []) or [])
            combined = f"{title} {description} {tags}".lower()

            # Fuzzy match: any query term in combined text
            if not any(term in combined for term in query_terms):
                continue

            salary_min = item.get("salary_min")
            salary_max = item.get("salary_max")
            salary_str = ""
            if salary_min and salary_max:
                salary_str = f"${salary_min:,} – ${salary_max:,}"
            elif salary_min:
                salary_str = f"${salary_min:,}+"

            jobs.append(Job(
                title=title,
                company=item.get("company", ""),
                location="Remote",
                url=item.get("url", f"https://remoteok.com/remote-jobs/{item.get('id','')}"),
                source="remoteok",
                description=description,
                posted_date=item.get("date", ""),
                salary=salary_str,
                job_id=str(item.get("id", "")),
            ))
            time.sleep(0.05)

        return jobs

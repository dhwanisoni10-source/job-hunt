"""
Himalayas.app — free public job API, no key required.
Great for remote-first roles with good salary transparency.
https://himalayas.app/api
"""

import requests
import time
import re
from typing import List
from src.models import Job
from src.finder.base import BaseFinder

SEARCH_URL = "https://himalayas.app/api/jobs"


class HimalayasFinder(BaseFinder):
    """Pulls jobs from the Himalayas remote job board API."""

    def search(self, query: str, location: str = "Remote", days_back: int = 7) -> List[Job]:
        params = {
            "q": query,
            "limit": 50,
        }
        try:
            resp = requests.get(SEARCH_URL, params=params, timeout=20,
                                headers={"User-Agent": "job-search-bot/1.0"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"  [himalayas] warning: {exc}")
            return []

        raw_jobs = data.get("jobs", []) if isinstance(data, dict) else data

        jobs: List[Job] = []
        for item in raw_jobs:
            title = item.get("title", "") or ""
            company = (item.get("company") or {}).get("name", "") or item.get("companyName", "")
            url = item.get("applicationLink", "") or item.get("url", "")
            description = item.get("description", "") or ""
            posted = item.get("publishedAt", "") or item.get("createdAt", "")

            # Salary
            sal_min = item.get("salaryMin") or item.get("salary_min")
            sal_max = item.get("salaryMax") or item.get("salary_max")
            salary_str = ""
            if sal_min and sal_max:
                salary_str = f"${int(sal_min):,} – ${int(sal_max):,}"
            elif sal_min:
                salary_str = f"${int(sal_min):,}+"
            elif not salary_str:
                salary_str = _extract_salary(description)

            if not title:
                continue

            jobs.append(Job(
                title=title,
                company=company,
                location="Remote",
                url=url,
                source="himalayas",
                description=description,
                posted_date=posted,
                salary=salary_str,
                job_id=str(item.get("id", "") or item.get("slug", "")),
            ))
            time.sleep(0.05)

        return jobs


def _extract_salary(text: str) -> str:
    patterns = [
        r"\$[\d,]+\s*[-–to]+\s*\$[\d,]+(?:[kK])?",
        r"\$[\d,]+[kK]\+?",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    return ""

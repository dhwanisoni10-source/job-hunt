"""
We Work Remotely — RSS feeds, no key required.
Category feeds: https://weworkremotely.com/categories/<slug>/jobs.rss
"""

import re
import time
from typing import List
from src.models import Job
from src.finder.base import BaseFinder
from src.rss import parse_feed

CATEGORY_FEEDS = {
    "software-dev": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "product": "https://weworkremotely.com/categories/remote-product-jobs.rss",
    "devops": "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "design": "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "marketing": "https://weworkremotely.com/categories/remote-marketing-jobs.rss",
    "data": "https://weworkremotely.com/categories/remote-data-science-ai-statistical-jobs.rss",
    "management": "https://weworkremotely.com/categories/remote-management-finance-jobs.rss",
    "all": "https://weworkremotely.com/remote-jobs.rss",
}

ROLE_TO_CATEGORIES = {
    "product manager": ["product", "management"],
    "associate product manager": ["product", "management"],
    "software engineer": ["software-dev"],
    "data scientist": ["data"],
    "data analyst": ["data"],
    "devops": ["devops"],
    "designer": ["design"],
    "marketing": ["marketing"],
}


def _pick_categories(query: str) -> List[str]:
    q = query.lower()
    for role, cats in ROLE_TO_CATEGORIES.items():
        if role in q:
            return cats
    # Default: product + management
    return ["product", "management", "all"]


class WeWorkRemotelyFinder(BaseFinder):
    """Scrapes We Work Remotely RSS feeds."""

    def search(self, query: str, location: str = "Remote", days_back: int = 7) -> List[Job]:
        cats = _pick_categories(query)
        query_terms = query.lower().split()

        seen_ids: set = set()
        jobs: List[Job] = []

        for cat in cats:
            feed_url = CATEGORY_FEEDS.get(cat, CATEGORY_FEEDS["all"])
            entries = parse_feed(feed_url)
            if not entries:
                continue

            for entry in entries:
                title = entry.get("title", "")
                link = entry.get("link", "")
                summary = entry.get("summary", "") or ""

                combined = f"{title} {summary}".lower()
                if not any(term in combined for term in query_terms):
                    continue

                job_id = link.split("/")[-1] if link else title
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                # WWR titles are like "CompanyName: Job Title"
                company = ""
                clean_title = title
                if ": " in title:
                    parts = title.split(": ", 1)
                    company = parts[0].strip()
                    clean_title = parts[1].strip() if len(parts) > 1 else title

                salary = _extract_salary(summary)

                jobs.append(Job(
                    title=clean_title,
                    company=company,
                    location="Remote",
                    url=link,
                    source="weworkremotely",
                    description=summary,
                    posted_date=entry.get("published", ""),
                    salary=salary,
                    job_id=job_id,
                ))

            time.sleep(0.5)

        return jobs


def _extract_salary(text: str) -> str:
    """Pull the first salary range or figure from raw text."""
    patterns = [
        r"\$[\d,]+\s*[-–to]+\s*\$[\d,]+(?:[kK])?",
        r"\$[\d,]+[kK]?\s*[-–]\s*\$[\d,]+[kK]?",
        r"\$[\d,]+[kK]\+?",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    return ""

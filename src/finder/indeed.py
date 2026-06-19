import urllib.parse
from typing import List
from src.models import Job
from src.finder.base import BaseFinder
from src.rss import parse_feed


class IndeedFinder(BaseFinder):
    """Scrapes Indeed via their public RSS feed — no API key required."""

    RSS_URL = "https://www.indeed.com/rss"

    def search(self, query: str, location: str, days_back: int = 7) -> List[Job]:
        params = {
            "q": query,
            "l": location,
            "sort": "date",
            "fromage": str(days_back),
        }
        url = f"{self.RSS_URL}?{urllib.parse.urlencode(params)}"
        entries = parse_feed(url)

        jobs: List[Job] = []
        for entry in entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            published = entry.get("published", "")

            # Indeed format: "Title - Company"
            company = ""
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0].strip()
                company = parts[1].strip() if len(parts) > 1 else ""

            jobs.append(Job(
                title=title,
                company=company,
                location=location,
                url=link,
                source="indeed",
                description=summary,
                posted_date=published,
                job_id=entry.get("id", link),
            ))

        return jobs

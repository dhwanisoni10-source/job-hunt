import time
import urllib.parse
from typing import List
from bs4 import BeautifulSoup
from src.models import Job
from src.finder.base import BaseFinder

# LinkedIn's public job search page (no login required for listings)
SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOB_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"


class LinkedInFinder(BaseFinder):
    """Scrapes LinkedIn public job listings (guest API, no auth needed)."""

    TIME_FILTERS = {1: "r86400", 7: "r604800", 30: "r2592000"}

    def search(self, query: str, location: str, days_back: int = 7) -> List[Job]:
        time_filter = self.TIME_FILTERS.get(days_back, "r604800")
        params = {
            "keywords": query,
            "location": location,
            "f_TPR": time_filter,
            "start": 0,
        }

        jobs: List[Job] = []
        url = f"https://www.linkedin.com/jobs/search/?{urllib.parse.urlencode(params)}"

        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            cards = soup.select("div.base-card")
            for card in cards:
                title_el = card.select_one("h3.base-search-card__title")
                company_el = card.select_one("h4.base-search-card__subtitle")
                location_el = card.select_one("span.job-search-card__location")
                link_el = card.select_one("a.base-card__full-link")
                date_el = card.select_one("time")

                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                loc = location_el.get_text(strip=True) if location_el else location
                link = link_el["href"] if link_el else ""
                posted = date_el.get("datetime", "") if date_el else ""

                if not title:
                    continue

                jobs.append(Job(
                    title=title,
                    company=company,
                    location=loc,
                    url=link,
                    source="linkedin",
                    posted_date=posted,
                    job_id=link.split("?")[0].rstrip("/").split("/")[-1] if link else "",
                ))
                time.sleep(0.3)

        except Exception as exc:
            print(f"  [linkedin] warning: {exc}")

        return jobs

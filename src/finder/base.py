import requests
from abc import ABC, abstractmethod
from typing import List
from src.models import Job

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class BaseFinder(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    @abstractmethod
    def search(self, query: str, location: str, days_back: int = 7) -> List[Job]:
        ...

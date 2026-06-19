"""
Minimal RSS/Atom feed parser using stdlib xml.etree — no feedparser needed.
Returns list of dicts with keys: title, link, summary, published, id.
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict

NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (job-search-bot/1.0; +https://github.com)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def _text(el, *tags) -> str:
    for tag in tags:
        child = el.find(tag)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def parse_feed(url: str, timeout: int = 20) -> List[Dict]:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as exc:
        print(f"  [rss] failed to fetch {url}: {exc}")
        return []

    entries = []

    # RSS 2.0
    for item in root.iter("item"):
        entries.append({
            "title": _text(item, "title"),
            "link": _text(item, "link"),
            "summary": _text(item, "description",
                             "{http://purl.org/rss/1.0/modules/content/}encoded"),
            "published": _text(item, "pubDate",
                               "{http://purl.org/dc/elements/1.1/}date"),
            "id": _text(item, "guid", "link"),
        })

    # Atom 1.0
    if not entries:
        ns = "http://www.w3.org/2005/Atom"
        for entry in root.iter(f"{{{ns}}}entry"):
            link_el = entry.find(f"{{{ns}}}link")
            link = link_el.get("href", "") if link_el is not None else ""
            summary = (_text(entry, f"{{{ns}}}summary") or
                       _text(entry, f"{{{ns}}}content"))
            entries.append({
                "title": _text(entry, f"{{{ns}}}title"),
                "link": link,
                "summary": summary,
                "published": _text(entry, f"{{{ns}}}published", f"{{{ns}}}updated"),
                "id": _text(entry, f"{{{ns}}}id") or link,
            })

    return entries

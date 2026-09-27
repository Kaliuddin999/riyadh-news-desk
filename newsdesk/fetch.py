"""Download and parse RSS/Atom feeds."""
import calendar
import html
import re
from datetime import datetime, timezone

import feedparser
import requests

USER_AGENT = "Mozilla/5.0 (compatible; RiyadhNewsDesk/1.0)"
_TAGS = re.compile(r"<[^>]+>")


def _clean(text):
    return " ".join(html.unescape(_TAGS.sub(" ", text or "")).split())


def parse_feed(content):
    feed = feedparser.parse(content)
    if not feed.version:
        raise ValueError("not an RSS/Atom feed")
    feed_title = feed.feed.get("title", "")
    entries = []
    for e in feed.entries:
        source = (e.get("source") or {}).get("title") or feed_title
        title = _clean(e.get("title", ""))
        suffix = f" - {source}"
        if source and title.endswith(suffix):
            title = title[: -len(suffix)]
        summary = _clean(e.get("summary", ""))
        if summary in (title, f"{title} {source}"):  # Google News: just title + outlet name
            summary = ""
        stamp = e.get("published_parsed") or e.get("updated_parsed")
        published = datetime.fromtimestamp(calendar.timegm(stamp), tz=timezone.utc) if stamp else None
        entries.append({"title": title, "link": e.get("link", ""), "summary": summary,
                        "published": published, "source": source})
    return entries


def fetch_entries(url, timeout=15):
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return parse_feed(response.content)

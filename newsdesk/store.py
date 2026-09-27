"""News items: shape, de-duplication and retention."""
import hashlib
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

DEFAULT_RETENTION_DAYS = 14
RETENTION_DAYS = {"shalfa": 365}
_ISO = "%Y-%m-%dT%H:%M:%SZ"


def iso(dt):
    return dt.astimezone(timezone.utc).strftime(_ISO)


def parse_iso(text):
    return datetime.strptime(text, _ISO).replace(tzinfo=timezone.utc)


def normalize_url(url):
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_")]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def item_id(url):
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()[:16]


def _title_key(title):
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def make_item(*, title, link, source, category, urgent, published, now):
    """Build a stored item, or None if the entry is unusable."""
    title = " ".join((title or "").split())
    link = (link or "").strip()
    if not title or not link.lower().startswith(("http://", "https://")):
        return None
    if published is None or published > now:
        published = now
    return {"id": item_id(link), "title": title, "link": link, "source": source or "",
            "category": category, "urgent": bool(urgent),
            "published_at": iso(published), "fetched_at": iso(now)}


def merge(existing, new):
    """Add new items not already present (same URL or same title). Newest first."""
    items = list(existing)
    ids = {i["id"] for i in items}
    titles = {_title_key(i["title"]) for i in items}
    added = 0
    for item in new:
        key = _title_key(item["title"])
        if item["id"] in ids or key in titles:
            continue
        items.append(item)
        ids.add(item["id"])
        titles.add(key)
        added += 1
    items.sort(key=lambda i: i["published_at"], reverse=True)
    return items, added


def prune(items, now):
    """Drop items older than their category's retention period."""
    return [i for i in items
            if parse_iso(i["published_at"])
            >= now - timedelta(days=RETENTION_DAYS.get(i["category"], DEFAULT_RETENTION_DAYS))]

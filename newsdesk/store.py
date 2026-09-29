"""News items: shape, de-duplication and retention."""
import hashlib
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

DEFAULT_RETENTION_DAYS = 14
# Fast-changing topics go stale quickly; Shalfa news is rare, so it stays for a year.
RETENTION_DAYS = {"schools": 3, "weather": 3, "roads": 3,
                  "crime": 7, "major": 7, "shopping": 7, "forecast": 7,
                  "shalfa": 365}
SAME_STORY_DAYS = 3
# Words that say nothing about which story a headline tells.
_FILLER = set("""a an the and or of in on at to for from by with as is are was were be been after amid
over into its it this that than new says said report reports riyadh saudi arabia ksa capital kingdom
authorities official officials""".split())
# Outlets word the same story differently ("online classes" vs "remote learning").
_SAME_MEANING = {"online": "remote", "distance": "remote", "classes": "learning", "lessons": "learning",
                 "switch": "shift", "switches": "shift", "shifts": "shift", "adopt": "shift",
                 "adopts": "shift", "move": "shift", "moves": "shift", "revert": "shift",
                 "reverts": "shift", "closed": "closure", "closes": "closure", "close": "closure",
                 "suspends": "suspend", "suspended": "suspend", "thunderstorm": "storm",
                 "thunderstorms": "storm", "storms": "storm", "rains": "rain", "rainfall": "rain",
                 "warning": "alert", "warns": "alert", "alerts": "alert"}
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


def _story_words(title):
    words = (_SAME_MEANING.get(w, w) for w in _title_key(title).split())
    return {w for w in words if len(w) > 2 and w not in _FILLER}


def _same_story(a, b):
    """Headlines share most of their meaningful words (at least 3)."""
    shared = len(a & b)
    return shared >= 3 and shared >= 0.5 * min(len(a), len(b))


def collapse_similar(items):
    """Keep only the newest headline of each story (same category, within a few days)."""
    kept = []
    for item in sorted(items, key=lambda i: i["published_at"], reverse=True):
        words = _story_words(item["title"])
        when = parse_iso(item["published_at"])
        if not any(k["category"] == item["category"]
                   and when >= parse_iso(k["published_at"]) - timedelta(days=SAME_STORY_DAYS)
                   and _same_story(words, _story_words(k["title"]))
                   for k in kept):
            kept.append(item)
    return kept


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

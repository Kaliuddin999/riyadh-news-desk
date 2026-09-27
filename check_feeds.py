"""Manual check: which feeds work right now, and how many items each gives."""
from newsdesk.fetch import fetch_entries
from newsdesk.sources import FEEDS, OUTLET_CANDIDATES

for feed in FEEDS + OUTLET_CANDIDATES:
    try:
        entries = fetch_entries(feed.url)
        print(f"OK    {len(entries):3d}  {feed.name}")
    except Exception as exc:  # report every kind of failure, keep checking the rest
        print(f"FAIL       {feed.name}: {exc}")

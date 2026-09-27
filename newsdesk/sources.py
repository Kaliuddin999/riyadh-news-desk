"""Where the news comes from. English sources only."""
from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class Feed:
    name: str
    url: str
    assume_local: bool = False  # feed is Saudi-scoped; headline need not say "Riyadh"/"Saudi"


def google_news(query, when="2d"):
    q = quote_plus(f"{query} when:{when}")
    return f"https://news.google.com/rss/search?q={q}&hl=en-SA&gl=SA&ceid=SA:en"


FEEDS = [
    Feed("GN schools", google_news('Riyadh schools suspended OR closed OR "remote learning" OR Madrasati')),
    Feed("GN weather", google_news("Riyadh weather warning OR rain OR dust OR NCM")),
    Feed("GN roads", google_news("Riyadh road closed OR diversion OR detour OR traffic")),
    Feed("GN royal court", google_news('Saudi "Royal Court" announces death'), True),
    Feed("GN incidents", google_news("Riyadh accident OR fire OR explosion OR killed")),
    Feed("GN prince minister", google_news("Saudi prince OR minister dies")),
    Feed("GN IPO", google_news('Saudi IPO OR "CMA approves" OR Nomu', when="7d")),
    Feed("GN shopping", google_news('Riyadh sale OR offer OR "White Friday" OR "Riyadh Season"')),
    Feed("GN Shalfa", google_news("Shalfa -munition", when="365d")),
    Feed("GN Shalfa Facilities", google_news('"Shalfa Facilities"', when="365d")),
]

# Outlet feeds to try. Checked 2026-09-27: Arab News (403), Saudi Gazette, SPA and Argaam
# (no RSS at the tried URLs) all failed, so none are used. Shalfa (9613) has no public
# English announcements feed; its section relies on the Google News searches above.
OUTLET_CANDIDATES = []

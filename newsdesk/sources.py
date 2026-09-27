"""Where the news comes from. English sources only."""
from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class Feed:
    name: str
    url: str
    assume_local: bool = False  # feed is Saudi-scoped; headline need not say "Riyadh"/"Saudi"
    limit: int | None = None  # keep only the newest N entries per run (busy feeds)


def google_news(query, when="2d"):
    q = quote_plus(f"{query} when:{when}")
    return f"https://news.google.com/rss/search?q={q}&hl=en-SA&gl=SA&ceid=SA:en"


FEEDS = [
    Feed("GN schools", google_news('Riyadh schools suspended OR closed OR "remote learning" OR Madrasati')),
    Feed("GN weather", google_news("Riyadh weather warning OR rain OR dust OR NCM")),
    Feed("GN roads", google_news("Riyadh road closed OR diversion OR detour OR traffic OR congestion")),
    Feed("GN crime", google_news("Riyadh theft OR robbery OR arrested OR accident OR fire")),
    Feed("GN fraud", google_news('Nazaha OR corruption OR fraud OR scam OR phishing Saudi')),
    Feed("GN economy", google_news('Saudi economy OR GDP OR inflation OR "non-oil" OR "Vision 2030"')),
    Feed("GN finance", google_news('SAIBOR OR SIBOR OR SAMA OR "Saudi banks" OR ZATCA OR "interest rate" Saudi')),
    Feed("GN contracts", google_news('Saudi "contract award" OR "awarded a contract" OR "signs contract"', when="7d")),
    Feed("GN offers", google_news("Lulu OR Carrefour OR Othaim OR Panda OR eXtra offers Saudi", when="7d")),
    Feed("GN forecast Saudi", google_news("Saudi outlook OR forecast 2027", when="7d"), limit=6),
    Feed("GN forecast gold", google_news("gold price forecast", when="7d"), limit=6),
    Feed("GN forecast oil", google_news("oil price forecast OR outlook", when="7d"), limit=6),
    Feed("GN forecast IMF", google_news('IMF OR "World Bank" outlook OR forecast', when="7d"), limit=6),
    Feed("GN forecast AI jobs", google_news('AI jobs forecast OR "expected to"', when="7d"), limit=6),
    Feed("GN forecast risks", google_news("earthquake OR flood OR crisis warning Gulf OR Saudi", when="7d"), limit=6),
    Feed("GN forecast health", google_news("health outlook OR forecast Saudi", when="7d"), limit=6),
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

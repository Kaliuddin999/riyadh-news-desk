"""Decide which category a headline belongs to and whether it is urgent."""
import re


def _words(*terms):
    """Whole-word matcher. A trailing '*' allows any word ending ('flood*' -> floods, flooding)."""
    parts = [re.escape(t[:-1]) + r"\w*" if t.endswith("*") else re.escape(t) for t in terms]
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b", re.IGNORECASE)


LOCATION = _words("riyadh", "saudi*", "ksa", "kingdom")
MARKET = _words("tadawul", "tasi", "cma", "capital market authority", "nomu",
                "parallel market", "saudi exchange")

SHALFA = _words("shalfa")
SHALFA_CODE = _words("9613")
SHALFA_URGENT = _words("halt*", "suspen*")

IPO_DIRECT = _words("ipo", "ipos", "initial public offering*")
IPO = _words("offering*", "subscription*", "rights issue*", "listing*",
             "book-building", "bookbuilding", "book building")

SCHOOL_SUBJECT = _words("school*", "madrasati", "classes", "students",
                        "ministry of education", "universit*")
SCHOOL_CHANGE = _words("suspend*", "closed", "closure*", "remote", "online",
                       "distance learning", "cancel*", "postpone*", "holiday*")

WEATHER = _words("weather", "rain*", "storm*", "dust*", "sandstorm*", "thunder*", "flood*",
                 "ncm", "meteorolog*", "heatwave", "fog", "hail*", "torrential")
WEATHER_URGENT = _words("warning*", "warns", "alert*", "severe", "flood*", "torrential",
                        "heavy rain*")

ROAD_SUBJECT = _words("road*", "street*", "highway*", "traffic", "interchange*", "tunnel*",
                      "bridge*", "metro")
ROAD_CHANGE = _words("closed", "closure*", "divert*", "diversion*", "detour*", "shut*",
                     "blocked", "congestion")
ROAD_URGENT = _words("closed", "closure*", "shut*", "blocked")

DEATH = _words("died", "dies", "death*", "passed away", "passes away", "funeral*", "mourn*")
MAJOR = _words("died", "dies", "death*", "passed away", "passes away", "funeral*",
               "condolence*", "mourn*", "killed", "fire", "blaze", "explosion*", "crash*",
               "collapse*", "shooting", "attack*")
ROYAL = _words("royal court")

SHOPPING = _words("sale", "discount*", "offer", "offers", "white friday", "black friday",
                  "riyadh season", "deal", "deals", "promotion*")


def classify(title, summary="", assume_local=False):
    """Return (category, urgent) for a headline, or (None, False) to discard it.

    assume_local: the feed itself is Saudi-scoped, so the text need not name Riyadh/Saudi.
    """
    text = f"{title} {summary}"

    if SHALFA.search(text) or (SHALFA_CODE.search(text) and MARKET.search(text)):
        return "shalfa", bool(SHALFA_URGENT.search(text))
    if IPO_DIRECT.search(text) or (IPO.search(text) and MARKET.search(text)):
        return "ipo", False
    if not (assume_local or LOCATION.search(text)):
        return None, False
    if SCHOOL_SUBJECT.search(text) and SCHOOL_CHANGE.search(text):
        return "schools", True
    if WEATHER.search(text):
        return "weather", bool(WEATHER_URGENT.search(text))
    if ROAD_SUBJECT.search(text) and ROAD_CHANGE.search(text):
        return "roads", bool(ROAD_URGENT.search(text))
    if MAJOR.search(text):
        return "major", bool(ROYAL.search(text) and DEATH.search(text))
    if SHOPPING.search(text):
        return "shopping", False
    return None, False

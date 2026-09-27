"""Decide which category a headline belongs to and whether it is urgent."""
import re


def _words(*terms):
    """Whole-word matcher. A trailing '*' allows any word ending ('flood*' -> floods, flooding)."""
    parts = [re.escape(t[:-1]) + r"\w*" if t.endswith("*") else re.escape(t) for t in terms]
    return re.compile(r"\b(?:" + "|".join(parts) + r")\b", re.IGNORECASE)


LOCATION = _words("riyadh", "saudi*", "ksa", "sama", "saibor", "sibor", "zatca")  # last four are Saudi-only
MARKET = _words("tadawul", "tasi", "cma", "capital market authority", "nomu",
                "parallel market", "saudi exchange")

SHALFA = _words("shalfa")
SHALFA_CODE = re.compile(r"\b9613\b(?![.,]\d)")  # not "9613.4 points"
SHALFA_CONTEXT = _words("facilit*", "fm", "contract*", "sar", "share*", "shareholder*", "board",
                        "profit*", "results", "dividend*")
SHALFA_URGENT = _words("halt*", "suspen*")

IPO_DIRECT = _words("ipo", "ipos", "initial public offering*")
IPO = _words("offering*", "subscription*", "rights issue*", "listing*",
             "book-building", "bookbuilding", "book building")

SCHOOL_SUBJECT = _words("school*", "madrasati", "classes", "students",
                        "ministry of education", "universit*")
SCHOOL_CHANGE = _words("suspend*", "closed", "closure*", "remote", "online",
                       "distance learning", "cancel*", "postpone*", "holiday*")
SCHOOL_URGENT = _words("suspend*", "closed", "closure*", "remote", "distance learning", "cancel*")

WEATHER = _words("weather", "rain*", "storm*", "dust*", "sandstorm*", "thunder*", "flood*",
                 "ncm", "meteorolog*", "heatwave", "fog", "hailstorm*", "torrential")
WEATHER_URGENT = _words("warning*", "warns", "alert*", "severe", "flood*", "torrential",
                        "heavy rain*")

ROAD_SUBJECT = _words("road*", "street*", "highway*", "traffic", "interchange*", "tunnel*",
                      "bridge*", "metro")
ROAD_CHANGE = _words("closed", "closure*", "divert*", "diversion*", "detour*", "shut*",
                     "blocked", "congestion", "jam*", "gridlock")
ROAD_URGENT = _words("closed", "closure*", "shut*", "blocked")

FORECAST = _words("forecast*", "outlook*", "expected", "expects", "predict*", "projection*",
                  "projected", "anticipat*", "next year", "2027", "2028")
FORECAST_TOPIC = _words("econom*", "gdp", "growth", "inflation", "recession", "job*", "employment",
                        "unemployment", "gold", "oil", "technolog*", "ai", "a.i",
                        "artificial intelligence", "health*", "pandemic", "flood*", "earthquake*",
                        "cyclone*", "crisis", "crises", "ipo*", "rate*")

FRAUD = _words("fraud*", "scam*", "phishing", "swindl*", "counterfeit*", "embezzl*", "bribery",
               "money laundering", "impersonat*", "nazaha", "corruption", "awareness", "beware", "warns citizens",
               "warns residents", "warns public")

DEATH = _words("died", "dies", "death*", "passed away", "passes away", "funeral*", "mourn*")
MAJOR = _words("died", "dies", "death*", "passed away", "passes away", "funeral*",
               "condolence*", "mourn*", "explosion*", "airstrike*", "missile*", "attack*", "kills")
ROYAL = _words("royal court")

CRIME = _words("theft", "thief", "thieves", "stolen", "steal*", "robbery", "robber*", "burglar*",
               "arrest*", "accident*", "crash*", "collision", "fire", "blaze", "murder*",
               "stabbing", "shooting", "smuggl*", "killed", "injured", "drown*", "collapse*")

CONTRACT = _words("contract*", "tender*")
AWARD = _words("award*", "wins", "won", "signs", "signed", "secures", "secured", "inks")

FINANCE = _words("sibor", "saibor", "sama", "repo rate", "interest rate*", "bank rate*",
                 "central bank", "accounting", "zatca", "vat", "ifrs", "e-invoicing", "mortgage*",
                 "bank", "banks", "banking", "lending", "loan*", "deposit*")

ECONOMY = _words("econom*", "gdp", "inflation", "budget", "vision 2030", "investment*", "fdi",
                 "non-oil", "pmi", "unemployment", "exports", "imports", "trade surplus",
                 "fiscal", "growth")

SHOPPING = _words("sale", "discount*", "offer", "offers", "white friday", "black friday",
                  "riyadh season", "deal", "deals", "promotion*")


def classify(title, summary="", assume_local=False):
    """Return (category, urgent) for a headline, or (None, False) to discard it.

    assume_local: the feed itself is Saudi-scoped, so the text need not name Riyadh/Saudi.
    """
    text = f"{title} {summary}"

    shalfa_named = SHALFA.search(text) and (SHALFA_CONTEXT.search(text) or MARKET.search(text)
                                            or LOCATION.search(text) or SHALFA_CODE.search(text))
    if shalfa_named or (SHALFA_CODE.search(text) and MARKET.search(text)):
        return "shalfa", bool(SHALFA_URGENT.search(text))

    local = assume_local or bool(LOCATION.search(text))
    if local:
        if SCHOOL_SUBJECT.search(text) and SCHOOL_CHANGE.search(text):
            return "schools", bool(SCHOOL_URGENT.search(text))
        if WEATHER.search(text):
            return "weather", bool(WEATHER_URGENT.search(text))
        if ROAD_SUBJECT.search(text) and ROAD_CHANGE.search(text):
            return "roads", bool(ROAD_URGENT.search(text))

    # Outlooks need no Saudi mention: gold, oil or IMF forecasts matter here too.
    if FORECAST.search(text) and FORECAST_TOPIC.search(text):
        return "forecast", False

    saudi_market = MARKET.search(text) or local
    if (IPO_DIRECT.search(text) and saudi_market) or (IPO.search(text) and MARKET.search(text)):
        return "ipo", False
    if not local:
        return None, False

    if FRAUD.search(text):
        return "fraud", False
    if MAJOR.search(text):
        return "major", bool(ROYAL.search(text) and DEATH.search(text))
    if CRIME.search(text):
        return "crime", False
    if CONTRACT.search(text) and AWARD.search(text):
        return "contracts", False
    if FINANCE.search(text):
        return "finance", False
    if ECONOMY.search(text):
        return "economy", False
    if SHOPPING.search(text):
        return "shopping", False
    return None, False

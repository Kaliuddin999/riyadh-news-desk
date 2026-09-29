import pytest

from newsdesk.classify import classify


@pytest.mark.parametrize("title, expected", [
    ("Riyadh schools switch to remote learning on Monday due to rain", ("schools", True)),
    ("NCM issues red alert for heavy rain in Riyadh", ("weather", True)),
    ("Riyadh weather: mild temperatures this week", ("weather", False)),
    ("King Fahd Road exit closed for maintenance in Riyadh", ("roads", True)),
    ("Traffic diversion on Riyadh ring road this weekend", ("roads", False)),
    ("Fire breaks out in Riyadh warehouse", ("crime", False)),
    ("CMA approves IPO of XYZ Company on Tadawul", ("ipo", False)),
    ("Saudi Aramco secondary share offering on Saudi Exchange", ("ipo", False)),
    ("Riyadh Season 2026: huge discounts at Boulevard", ("shopping", False)),
    ("Shalfa shares debut on Nomu", ("shalfa", False)),
    ("Trading halt on Shalfa (9613) shares", ("shalfa", True)),
    ("Company 9613 announces annual results on Nomu", ("shalfa", False)),
])
def test_categories(title, expected):
    assert classify(title) == expected


@pytest.mark.parametrize("title", [
    "Heavy rain expected in Bahrain",            # 'rain' inside 'Bahrain'
    "Train services expand in Riyadh",           # 'rain' inside 'Train'
    "Flight 9613 lands in Jeddah",               # 9613 without a market context
    "Stock market rallies in London",            # not Saudi
    "Netflix raises subscription prices in Saudi Arabia",  # 'subscription' but no market
])
def test_irrelevant_headlines_are_discarded(title):
    assert classify(title) == (None, False)


def test_royal_court_death_is_urgent_when_feed_is_local():
    assert classify("Royal Court: Prince Abdullah passes away", assume_local=True) == ("major", True)


def test_non_saudi_headline_needs_local_feed():
    assert classify("Royal Court: Prince Abdullah passes away") == (None, False)


def test_summary_is_used_too():
    assert classify("Big news today", "Riyadh schools suspended tomorrow") == ("schools", True)


def test_foreign_ipo_is_discarded():
    assert classify("Meet the Data Center Builders Behind A.I.'s Next IPO Wave") == (None, False)


def test_saudi_ipo_without_market_word_is_kept():
    assert classify("Saudi Arabia proposes sweeping overhaul of IPO regulations") == ("ipo", False)


@pytest.mark.parametrize("title", [
    "Saudi crown prince hailed for peace efforts",   # 'hailed' is not weather
    "Former United Kingdom minister dies aged 80",   # 'kingdom' is not Saudi
    "TASI closes at 9613.4 points",                  # index level, not Shalfa's code
    "Shalfa village festival draws visitors in Morocco",  # the name without business context
])
def test_review_false_positives_are_discarded(title):
    assert classify(title) == (None, False)


@pytest.mark.parametrize("title", [
    "Saudi university launches online degree",
    "Riyadh schools announce winter holiday dates",
])
def test_school_news_without_closure_is_not_urgent(title):
    assert classify(title) == ("schools", False)


@pytest.mark.parametrize("title", [
    "Shalfa Awarded SAR 61.2 mln Contract from Ministry of Tourism",
    "Shalfa secures contract to provide FM services at Qassim school buildings",
    "Shalfa Facilities Management Announces Contract Award With Tatweer Buildings Co",
])
def test_real_shalfa_business_news_is_kept(title):
    assert classify(title)[0] == "shalfa"


@pytest.mark.parametrize("title, expected", [
    ("Riyadh traffic police warn of heavy congestion on King Fahd Road", ("roads", False)),
    ("Police arrest gang for car theft in Riyadh", ("crime", False)),
    ("Two injured in accident on Riyadh ring road", ("crime", False)),
    ("Saudi Interior Ministry warns residents of phishing scam messages", ("fraud", False)),
    ("Riyadh court convicts suspects in SAR 40 million fraud case", ("fraud", False)),
    ("Seven killed in Saudi airstrike on Yemen market", ("major", False)),
    ("Saudi non-oil GDP grows 4.5% in second quarter", ("economy", False)),
    ("SAMA keeps repo rate unchanged as SAIBOR eases", ("finance", False)),
    ("ZATCA issues new e-invoicing accounting rules for Saudi firms", ("finance", False)),
    ("Saudi Aramco awards SAR 2 billion contract to local firm", ("contracts", False)),
    ("Lulu Hypermarket launches mega offers across Saudi Arabia", ("shopping", False)),
    ("Carrefour Riyadh weekend deals", ("shopping", False)),
    ("Gold prices expected to hit record high next year", ("forecast", False)),
    ("IMF raises Saudi growth forecast for 2027", ("forecast", False)),
    ("AI expected to reshape jobs in Gulf by 2030", ("forecast", False)),
    ("Saudi IPO market expected to rebound next year", ("forecast", False)),
    ("Rain expected in Riyadh on Tuesday", ("weather", False)),
])
def test_portal_sections(title, expected):
    assert classify(title) == expected


@pytest.mark.parametrize("title", [
    "Manchester United expected to sign striker",      # forecast word, no forecast topic
    "Extra time drama as Al Hilal win in Riyadh",      # 'Extra' is not the eXtra store
    "Panda sightings rise in China",                   # not Saudi
])
def test_portal_false_positives_are_discarded(title):
    assert classify(title) == (None, False)


@pytest.mark.parametrize("title, expected", [
    ("Cardano Price Forecast: ADA Bear Flag Risks Drop to $0.118", (None, False)),
    ("Nazaha arrests officials in Riyadh bribery case", ("fraud", False)),
    ("Saudi strike on Yemen's Taiz kills seven", ("major", False)),
])
def test_live_preview_corrections(title, expected):
    assert classify(title) == expected


def test_schools_reopening_is_not_urgent():
    assert classify("Schools in Riyadh return to in-person learning after temporary closure") == ("schools", False)

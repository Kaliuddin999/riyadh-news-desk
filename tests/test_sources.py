from newsdesk.sources import FEEDS, google_news


def test_google_news_url_is_saudi_english_and_recent():
    url = google_news('Riyadh "road closed"', when="2d")
    assert url.startswith("https://news.google.com/rss/search?q=")
    assert "when%3A2d" in url and "hl=en-SA&gl=SA&ceid=SA:en" in url


def test_shalfa_is_searched():
    assert any("Shalfa" in f.name for f in FEEDS)


def test_only_royal_court_search_skips_the_location_check():
    # Google News matches article bodies, so e.g. "Rain, flooding in Bangkok" comes back
    # from the Riyadh weather search; only Royal Court titles often omit "Saudi".
    assert [f.name for f in FEEDS if f.assume_local] == ["GN royal court"]

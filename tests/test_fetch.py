from datetime import datetime, timezone

import pytest

from newsdesk.fetch import parse_feed

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Google News</title>
<item>
  <title>NCM warns of heavy rain in Riyadh - Arab News</title>
  <link>https://news.google.com/rss/articles/abc</link>
  <pubDate>Sat, 26 Sep 2026 10:00:00 GMT</pubDate>
  <description>&lt;a href="https://x"&gt;NCM warns&lt;/a&gt; of rain &amp;amp; dust</description>
  <source url="https://www.arabnews.com">Arab News</source>
</item>
<item><title>No date item</title><link>https://example.com/a</link></item>
</channel></rss>"""


def test_parse_feed_extracts_clean_fields():
    first, second = parse_feed(RSS)
    assert first == {"title": "NCM warns of heavy rain in Riyadh",
                     "link": "https://news.google.com/rss/articles/abc",
                     "summary": "NCM warns of rain & dust",
                     "published": datetime(2026, 9, 26, 10, 0, tzinfo=timezone.utc),
                     "source": "Arab News"}
    assert second["published"] is None
    assert second["source"] == "Google News"


def test_parse_feed_rejects_html():
    with pytest.raises(ValueError):
        parse_feed(b"<html><body><h1>404 Not Found</h1></body></html>")


def test_parse_feed_accepts_empty_feed():
    assert parse_feed(b'<?xml version="1.0"?><rss version="2.0"><channel><title>x</title></channel></rss>') == []

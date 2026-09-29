from datetime import datetime, timedelta, timezone

from newsdesk.store import collapse_similar, item_id, make_item, merge, normalize_url, prune

NOW = datetime(2026, 9, 27, 9, 0, tzinfo=timezone.utc)


def item(title, link, category="weather", days_old=0):
    return make_item(title=title, link=link, source="SPA", category=category, urgent=False,
                     published=NOW - timedelta(days=days_old), now=NOW)


def test_normalize_url_drops_tracking_fragment_and_trailing_slash():
    assert normalize_url("HTTPS://Example.com/a/?utm_source=x&id=5#top") == "https://example.com/a?id=5"


def test_item_id_ignores_tracking_params():
    assert item_id("https://example.com/a?utm_medium=rss") == item_id("https://example.com/a")
    assert len(item_id("https://example.com/a")) == 16


def test_make_item_shape():
    i = item("  Rain   in Riyadh ", "https://example.com/a")
    assert i == {"id": item_id("https://example.com/a"), "title": "Rain in Riyadh",
                 "link": "https://example.com/a", "source": "SPA", "category": "weather",
                 "urgent": False, "published_at": "2026-09-27T09:00:00Z",
                 "fetched_at": "2026-09-27T09:00:00Z"}


def test_make_item_rejects_non_http_links_and_empty_titles():
    assert item("Rain", "javascript:alert(1)") is None
    assert item("Rain", "") is None
    assert item("   ", "https://example.com/a") is None


def test_make_item_missing_or_future_date_becomes_now():
    for published in (None, NOW + timedelta(days=2)):
        i = make_item(title="Rain", link="https://e.com/a", source="", category="weather",
                      urgent=False, published=published, now=NOW)
        assert i["published_at"] == "2026-09-27T09:00:00Z"


def test_merge_dedupes_by_url_and_title_and_sorts_newest_first():
    old = [item("Rain in Riyadh", "https://a.com/1", days_old=1)]
    new = [
        item("Rain in Riyadh", "https://a.com/1?utm_source=x"),   # same URL
        item("RAIN in Riyadh!", "https://b.com/other"),           # same title
        item("Dust storm warning", "https://c.com/2"),
    ]
    merged, added = merge(old, new)
    assert added == 1
    assert [i["title"] for i in merged] == ["Dust storm warning", "Rain in Riyadh"]


def test_prune_keeps_shalfa_longer():
    items = [item("w15", "https://a.com/1", "economy", 15),
             item("w13", "https://a.com/2", "economy", 13),
             item("s15", "https://a.com/3", "shalfa", 15),
             item("s200", "https://a.com/4", "shalfa", 200),
             item("s366", "https://a.com/5", "shalfa", 366)]
    assert [i["title"] for i in prune(items, NOW)] == ["w13", "s15", "s200"]


def test_fast_changing_topics_expire_sooner():
    items = [item("weather4", "https://a.com/1", "weather", 4),
             item("weather2", "https://a.com/2", "weather", 2),
             item("crime8", "https://a.com/3", "crime", 8),
             item("crime6", "https://a.com/4", "crime", 6),
             item("economy13", "https://a.com/5", "economy", 13)]
    assert [i["title"] for i in prune(items, NOW)] == ["weather2", "crime6", "economy13"]


def test_same_story_from_many_outlets_collapses_to_newest():
    items = [
        item("Saudi authorities shift schools in Riyadh to remote learning for week", "https://a.com/1", "schools", 0),
        item("Schools in Riyadh return to in-person learning after temporary closure", "https://a.com/2", "schools", 0),
        item("Riyadh schools shift to remote learning for a week", "https://a.com/3", "schools", 1),
        item("Riyadh Schools Revert to 'Remote Learning' Due to Houthi Attacks", "https://a.com/4", "schools", 2),
    ]
    assert [i["title"] for i in collapse_similar(items)] == [
        "Saudi authorities shift schools in Riyadh to remote learning for week",
        "Schools in Riyadh return to in-person learning after temporary closure"]


def test_similar_titles_in_other_categories_or_weeks_apart_are_kept():
    items = [item("Riyadh schools shift to remote learning for a week", "https://a.com/1", "schools", 0),
             item("Riyadh schools shift to remote learning for a week again", "https://a.com/2", "schools", 5),
             item("Riyadh schools shift to remote learning for a week", "https://a.com/3", "forecast", 0)]
    assert len(collapse_similar(items)) == 3


def test_differently_worded_versions_of_one_story_collapse():
    items = [item("Saudi Capital Schools Shift Online Amid Houthi Escalation", "https://a.com/1", "schools", 0),
             item("Riyadh schools switch to online classes for a week", "https://a.com/2", "schools", 1),
             item("Riyadh schools adopt remote learning for a week - Region - World", "https://a.com/3", "schools", 1),
             item("Riyadh Schools Revert to 'Remote Learning' Due to Houthi Attacks", "https://a.com/4", "schools", 2)]
    assert [i["title"] for i in collapse_similar(items)] == ["Saudi Capital Schools Shift Online Amid Houthi Escalation"]

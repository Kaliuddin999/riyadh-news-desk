import json
from datetime import datetime, timezone

import pytest

import fetch_news
from newsdesk.crypto import decrypt_json
from newsdesk.sources import Feed

NOW = datetime(2026, 9, 27, 9, 0, tzinfo=timezone.utc)
PW = "test-password-123"
FEEDS = [Feed("good", "http://good", assume_local=True), Feed("bad", "http://bad")]
RAIN = {"title": "NCM issues red alert for heavy rain in Riyadh", "link": "https://example.com/rain",
        "summary": "", "published": datetime(2026, 9, 27, 8, 0, tzinfo=timezone.utc), "source": "SPA"}
LONDON = {"title": "Stock market rallies in London", "link": "https://example.com/london",
          "summary": "", "published": datetime(2026, 9, 27, 8, 0, tzinfo=timezone.utc), "source": "BBC"}


def fake_fetcher(url):
    if url == "http://bad":
        raise TimeoutError("timed out")
    return [RAIN, LONDON]


@pytest.fixture
def root(tmp_path):
    (tmp_path / "secret").mkdir()
    (tmp_path / "secret" / "password.txt").write_text(PW + "\n", encoding="utf-8")
    return tmp_path


def run(root, publisher=lambda repo, msg: True, fetcher=fake_fetcher, **kw):
    return fetch_news.run(root, fetcher=fetcher, publisher=publisher, feeds=FEEDS, now=NOW,
                          iterations=1000, **kw)


def published(root):
    return decrypt_json(json.loads((root / "docs" / "news.enc").read_text(encoding="utf-8")), PW)


def test_run_saves_encrypts_and_publishes(root):
    messages = []
    assert run(root, publisher=lambda repo, msg: messages.append(msg) or True) == 0
    payload = published(root)
    assert [i["title"] for i in payload["items"]] == [RAIN["title"]]
    assert payload["items"][0]["category"] == "weather"
    assert payload["items"][0]["urgent"] is True
    assert payload["status"] == {"last_run": "2026-09-27T09:00:00Z", "new_count": 1,
                                 "failed_sources": ["bad"]}
    assert messages == ["news update 2026-09-27T09:00:00Z"]
    assert PW not in (root / "docs" / "news.enc").read_text(encoding="utf-8")


def test_second_run_adds_nothing_new(root):
    run(root)
    run(root)
    payload = published(root)
    assert len(payload["items"]) == 1
    assert payload["status"]["new_count"] == 0


def test_old_items_are_pruned(root):
    (root / "data").mkdir()
    old = {"id": "x", "title": "Old dust storm", "link": "https://e.com/old", "source": "",
           "category": "weather", "urgent": False, "published_at": "2026-09-01T00:00:00Z",
           "fetched_at": "2026-09-01T00:00:00Z"}
    (root / "data" / "news.json").write_text(json.dumps({"items": [old], "status": {}}), encoding="utf-8")
    run(root)
    assert [i["title"] for i in published(root)["items"]] == [RAIN["title"]]


def test_failed_push_returns_1_but_keeps_data(root):
    assert run(root, publisher=lambda repo, msg: False) == 1
    assert (root / "data" / "news.json").exists()
    assert (root / "docs" / "news.enc").exists()


def test_all_feeds_down_still_publishes_status(root):
    def down(url):
        raise ConnectionError("no internet")
    assert run(root, fetcher=down) == 0
    assert published(root)["status"]["failed_sources"] == ["good", "bad"]


def test_dry_run_writes_nothing(root, capsys):
    assert run(root, dry_run=True) == 0
    assert not (root / "docs").exists()
    assert not (root / "data" / "news.json").exists()
    assert "heavy rain" in capsys.readouterr().out


def test_missing_password_stops_before_writing(tmp_path):
    with pytest.raises(fetch_news.ConfigError):
        run(tmp_path)
    assert not (tmp_path / "docs").exists()


def test_short_password_rejected(root):
    (root / "secret" / "password.txt").write_text("short", encoding="utf-8")
    with pytest.raises(fetch_news.ConfigError):
        run(root)


def test_password_file_with_byte_order_mark_works(root):
    # PowerShell 5.1 and some editors save UTF-8 with a BOM
    (root / "secret" / "password.txt").write_text("﻿" + PW, encoding="utf-8")
    run(root)
    assert published(root)["items"][0]["title"] == RAIN["title"]


def test_corrupt_store_is_set_aside_not_fatal(root):
    # e.g. the run was killed while writing news.json
    (root / "data").mkdir()
    (root / "data" / "news.json").write_text('{"items": [', encoding="utf-8")
    assert run(root) == 0
    assert [i["title"] for i in published(root)["items"]] == [RAIN["title"]]
    assert (root / "data" / "news.json.bad").exists()

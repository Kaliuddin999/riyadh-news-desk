"""Hourly job: collect Riyadh news, encrypt it, publish it to GitHub Pages."""
import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from newsdesk.classify import classify
from newsdesk.crypto import encrypt_json, load_or_create_salt
from newsdesk.fetch import fetch_entries
from newsdesk.publish import git_publish
from newsdesk.sources import FEEDS
from newsdesk.store import iso, make_item, merge, prune

ROOT = Path(__file__).resolve().parent
MIN_PASSWORD_LENGTH = 12
log = logging.getLogger("newsdesk")


class ConfigError(Exception):
    pass


def read_password(root):
    path = root / "secret" / "password.txt"
    if not path.exists():
        raise ConfigError(f"Missing {path}. Put your page password in it (one line).")
    password = path.read_text(encoding="utf-8").strip()
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ConfigError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    return password


def collect(feeds, fetcher, now):
    items, failed = [], []
    for feed in feeds:
        try:
            entries = fetcher(feed.url)
        except Exception as exc:  # one broken feed must not stop the others
            log.warning("feed failed: %s (%s)", feed.name, exc)
            failed.append(feed.name)
            continue
        for e in entries:
            category, urgent = classify(e["title"], e["summary"], assume_local=feed.assume_local)
            if category is None:
                continue
            item = make_item(title=e["title"], link=e["link"], source=e["source"], category=category,
                             urgent=urgent, published=e["published"], now=now)
            if item:
                items.append(item)
    return items, failed


def run(root, *, fetcher=fetch_entries, publisher=git_publish, feeds=FEEDS, now=None,
        dry_run=False, iterations=None):
    now = now or datetime.now(timezone.utc)
    password = read_password(root)
    store_path = root / "data" / "news.json"
    existing = json.loads(store_path.read_text(encoding="utf-8"))["items"] if store_path.exists() else []

    new, failed = collect(feeds, fetcher, now)
    new = prune(new, now)
    items, added = merge(existing, new)
    items = prune(items, now)
    status = {"last_run": iso(now), "new_count": added, "failed_sources": failed}
    log.info("run: %d new, %d total, failed feeds: %s", added, len(items), failed or "none")

    if dry_run:
        for i in new:
            print(f"[{i['category']}]{' URGENT' if i['urgent'] else ''} {i['title']}  ({i['source']})")
        print(f"{added} new, {len(items)} total, failed feeds: {failed or 'none'}")
        return 0

    payload = {"items": items, "status": status}
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    salt = load_or_create_salt(root / "data" / "salt.bin")
    extra = {"iterations": iterations} if iterations else {}
    (root / "docs").mkdir(exist_ok=True)
    blob = encrypt_json(payload, password, salt, **extra)
    (root / "docs" / "news.enc").write_text(json.dumps(blob), encoding="utf-8")

    if not publisher(root, f"news update {iso(now)}"):
        log.warning("push failed; the commit will be pushed on the next run")
        return 1
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Collect and publish Riyadh news.")
    parser.add_argument("--dry-run", action="store_true", help="show what would be added; write nothing")
    args = parser.parse_args(argv)

    (ROOT / "logs").mkdir(exist_ok=True)
    handlers = [logging.FileHandler(ROOT / "logs" / "run.log", encoding="utf-8")]
    if sys.stderr:  # pythonw (Task Scheduler) has no console
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        return run(ROOT, dry_run=args.dry_run)
    except Exception:
        log.exception("run crashed")
        return 2


if __name__ == "__main__":
    sys.exit(main())
